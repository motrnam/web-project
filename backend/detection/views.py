# detection/views.py
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from django.db import transaction
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.contrib.auth import get_user_model

from .models import DetectionBoard, Lead, Yarn, SuspectsSuggested
from interrogation.models import Suspect, Interrogation, InterrogationStatus, SuspectStatus
from users.permissions import IsDetective, IsSergeant
from .serializers import (
    DetectionBoardSerializer, LeadSerializer, YarnSerializer,
    SuspectsSuggestedSerializer,
    SubmitSuspectsSerializer, RejectFeedbackSerializer
)

User = get_user_model()

# unnecessary import
from django.db import models


class DetectionBoardViewSet(viewsets.ModelViewSet):
    """
    ViewSet for detectives to manage their investigation boards.
    """
    serializer_class = DetectionBoardSerializer
    permission_classes = [permissions.IsAuthenticated, IsDetective]

    def get_queryset(self):
        """Return only the detection boards belonging to the current detective."""
        return DetectionBoard.objects.filter(
            detection__detective=self.request.user
        ).select_related('detection').prefetch_related(
            'lead_set', 'lead_set__yarns_as_first', 'lead_set__yarns_as_second'
        )

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context

    @action(detail=True, methods=['get'])
    def leads(self, request, pk=None):
        """Get all leads for a specific board."""
        board = self.get_object()
        leads = Lead.objects.filter(board=board)
        serializer = LeadSerializer(leads, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def yarns(self, request, pk=None):
        """Get all connections (yarns) for a specific board."""
        board = self.get_object()
        leads = Lead.objects.filter(board=board)
        yarns = Yarn.objects.filter(
            models.Q(lead1__in=leads) | models.Q(lead2__in=leads)
        ).distinct()
        serializer = YarnSerializer(yarns, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def suggestions(self, request, pk=None):
        """Get all suspect suggestions for this detection."""
        board = self.get_object()
        detection = board.detection
        suggestions = SuspectsSuggested.objects.filter(detection=detection)
        serializer = SuspectsSuggestedSerializer(
            suggestions, many=True, context={'request': request}
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    @transaction.atomic
    def submit_suspects(self, request, pk=None):
        """
        Submit suspects for sergeant approval.
        Creates a SuspectsSuggested instance with PENDING state.
        """
        board = self.get_object()
        detection = board.detection

        # Check if there's already a pending suggestion
        if SuspectsSuggested.objects.filter(
                detection=detection, state=0
        ).exists():
            return Response(
                {"error": "You already have a pending suggestion. Wait for it to be processed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = SubmitSuspectsSerializer(
            data=request.data,
            context={'request': request, 'detection': detection}
        )

        if serializer.is_valid():
            # Create the suggestion
            suggestion = SuspectsSuggested.objects.create(
                detection=detection,
                detective_reasons=serializer.validated_data['reasons'],
                state=0  # PENDING
            )

            # Add selected suspects (users) to the many-to-many field
            suspect_users = serializer.validated_data['suspects']
            suggestion.suspects.set(suspect_users)

            # Here you could trigger a notification to the sergeant
            # notify_sergeant.delay(detection.sergeant_id, suggestion.id)

            return Response(
                SuspectsSuggestedSerializer(suggestion, context={'request': request}).data,
                status=status.HTTP_201_CREATED
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['get'], url_path='messages')
    def get_messages(self, request, pk=None):
        """
        Get all rejected suggestions as messages for the detective.
        Yes, you can filter SuspectsSuggested with state==2 for messages!
        This returns all rejected suggestions with their feedback.
        """
        board = self.get_object()
        detection = board.detection

        # Filter suggestions with state=2 (REJECTED)
        rejected_suggestions = SuspectsSuggested.objects.filter(
            detection=detection,
            state=2  # REJECTED
        ).order_by('-time_suggested')

        # Transform into message-like format
        messages = []
        for suggestion in rejected_suggestions:
            messages.append({
                'id': suggestion.id,
                'type': 'rejection',
                'title': 'Suspect Suggestion Rejected',
                'content': suggestion.feedback,  # The sergeant's feedback
                'reasons': suggestion.detective_reasons,  # Your original reasons
                'timestamp': suggestion.time_suggested,
                'read': False,  # You could add a read flag if needed
            })

        return Response(messages)


class LeadViewSet(viewsets.ModelViewSet):
    """CRUD operations for leads on a board."""
    serializer_class = LeadSerializer
    permission_classes = [permissions.IsAuthenticated, IsDetective]

    def get_queryset(self):
        # Ensure detective can only access leads from their own boards
        return Lead.objects.filter(
            board__detection__detective=self.request.user
        ).select_related('board', 'evidence')

    def perform_create(self, serializer):
        # Ensure the board belongs to the current detective
        board_id = self.request.data.get('board_id')
        board = get_object_or_404(
            DetectionBoard,
            id=board_id,
            detection__detective=self.request.user
        )
        serializer.save(board=board)


class YarnViewSet(viewsets.ModelViewSet):
    """CRUD operations for connections (yarns) between leads."""
    serializer_class = YarnSerializer
    permission_classes = [permissions.IsAuthenticated, IsDetective]

    def get_queryset(self):
        # Ensure detective can only access yarns from their own boards
        return Yarn.objects.filter(
            models.Q(lead1__board__detection__detective=self.request.user) |
            models.Q(lead2__board__detection__detective=self.request.user)
        ).distinct().select_related('lead1', 'lead2')

    def perform_create(self, serializer):
        # Validate that both leads belong to the same board and it's the detective's board
        lead1 = serializer.validated_data['lead1']
        lead2 = serializer.validated_data['lead2']

        if lead1.board != lead2.board:
            raise ValidationError("Both leads must belong to the same board")

        # Check if board belongs to current detective
        if lead1.board.detection.detective != self.request.user:
            raise ValidationError("You don't have permission to create yarns on this board")

        serializer.save()


class SuspectsSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for detectives to view their suspect suggestions.
    Note: This is read-only for detectives. Only sergeants can update states.
    """
    serializer_class = SuspectsSuggestedSerializer
    permission_classes = [permissions.IsAuthenticated, IsDetective]

    def get_queryset(self):
        return SuspectsSuggested.objects.filter(
            detection__detective=self.request.user
        ).select_related('detection').prefetch_related('suspects')

    @action(detail=True, methods=['get'], url_path='status')
    def check_status(self, request, pk=None):
        """Check the current status of a suggestion."""
        suggestion = self.get_object()
        return Response({
            'id': suggestion.id,
            'state': suggestion.get_state_display(),
            'state_code': suggestion.state,
            'feedback': suggestion.feedback if suggestion.state == 2 else None,
            'time_suggested': suggestion.time_suggested
        })


# detection/views.py - add this temporary view
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(['GET'])
def test_view(request):
    return Response({"message": "URLs are working!"})


class SergeantSuggestionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for sergeants to review and approve/reject detective suggestions.
    This is the CRITICAL missing piece that connects detection to interrogation!
    """
    serializer_class = SuspectsSuggestedSerializer
    permission_classes = [permissions.IsAuthenticated, IsSergeant]

    def get_queryset(self):
        """Return suggestions for cases where this sergeant is assigned."""
        return SuspectsSuggested.objects.filter(
            detection__sergeant=self.request.user
        ).select_related('detection', 'detection__case').prefetch_related('suspects')

    @action(detail=False, methods=['get'], url_path='pending')
    def pending(self, request):
        """Get all pending suggestions for this sergeant."""
        pending_suggestions = self.get_queryset().filter(state=0)
        serializer = self.get_serializer(pending_suggestions, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='approve')
    @transaction.atomic
    def approve(self, request, pk=None):
        """
        Approve the detective's suspect suggestions.
        This creates Suspect objects in the interrogation app and starts interrogations.
        """
        suggestion = self.get_object()

        if suggestion.state != 0:
            return Response(
                {"error": "This suggestion has already been processed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update suggestion state
        suggestion.state = 1  # CONFIRMED
        suggestion.save()

        # Create Suspect objects for each suggested user
        suspects_created = []
        interrogations_created = []

        for user in suggestion.suspects.all():
            # Create Suspect
            suspect, created = Suspect.objects.get_or_create(
                person=user,
                case=suggestion.detection.case,
                defaults={
                    'detail': f"تأیید شده توسط گروهبان بر اساس پیشنهاد کارآگاه: {suggestion.detective_reasons[:100]}",
                    'suspect_status': SuspectStatus.WANTED,
                    'added_by': request.user
                }
            )
            suspects_created.append(suspect)

            # Create Interrogation
            interrogation = Interrogation.objects.create(
                suspect=suspect,
                interrogator_sergeant=request.user,
                interrogator_detective=suggestion.detection.detective,
                status=InterrogationStatus.PENDING_SCORES
            )
            interrogations_created.append(interrogation)

        return Response({
            'message': 'Suspects approved and interrogations started',
            'suggestion_id': suggestion.id,
            'suspects_count': len(suspects_created),
            'interrogations_count': len(interrogations_created),
            'suspects': [
                {
                    'id': str(s.id),
                    'person': s.person.username,
                    'status': s.suspect_status
                } for s in suspects_created
            ]
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='reject')
    @transaction.atomic
    def reject(self, request, pk=None):
        """
        Reject the detective's suspect suggestions with feedback.
        """
        suggestion = self.get_object()

        if suggestion.state != 0:
            return Response(
                {"error": "This suggestion has already been processed."},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = RejectFeedbackSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Update suggestion state
        suggestion.state = 2  # REJECTED
        suggestion.feedback = serializer.validated_data['feedback']
        suggestion.save()

        return Response({
            'message': 'Suggestion rejected',
            'suggestion_id': suggestion.id,
            'feedback': suggestion.feedback
        }, status=status.HTTP_200_OK)
