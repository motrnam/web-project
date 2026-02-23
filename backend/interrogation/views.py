#backend/interrogation/views.py
from rest_framework import viewsets, permissions, exceptions, response, status
from rest_framework.decorators import action, api_view, permission_classes
from django.utils import timezone
from drf_yasg import openapi

from users.permissions import IsNotBaseUser
from .models import Suspect, Interrogation, InterrogationStatus, Court, VerdictStatus
from .serializers import (
    InterrogationListSerializer,
    SuspectSerializer,
    InterrogationWriteSerializer,
    CapitanCommentSerializer,
    CourtSerializer,
)
from .utils import get_most_wanted_list, calculate_suspect_ranking
from drf_yasg.utils import swagger_auto_schema
from django.db import models


class SuspectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for viewing and editing Suspect instances.
    """

    queryset = Suspect.objects.select_related("person", "case").all()
    serializer_class = SuspectSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotBaseUser]

    def get_serializer_class(self):
        if self.action == "interrogate":
            return InterrogationWriteSerializer
        return super().get_serializer_class()

    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("Not allowed")

    def destroy(self, request, *args, **kwargs):
        if Interrogation.objects.filter(suspect=self.get_object()).exists():
            raise exceptions.ValidationError(
                "suspect has Interrogation and you can't delete it"
            )
        return super().destroy(request, *args, **kwargs)

    @action(detail=True, methods=["post"])
    def interrogate(self, request, pk=None):
        """
        Start a new interrogation for this suspect
        """
        suspect = self.get_object()

        request.data["suspect"] = suspect.id

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        interrogation = serializer.save()

        return response.Response(
            {
                "message": "Interrogation started successfully",
                "interrogation_id": interrogation.id,
                "suspect_id": suspect.id,
                "suspect_name": suspect.person.get_full_name()
                if suspect.person
                else None,
                "sergeant": interrogation.interrogator_sergeant.get_full_name(),
                "detective": interrogation.interrogator_detective.get_full_name(),
                "status": "pending",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"])
    def interrogations(self, request, pk=None):
        """
        Get all interrogations for this suspect
        """
        suspect = self.get_object()
        interrogations = Interrogation.objects.filter(suspect=suspect)

        data = [
            {
                "id": i.id,
                "sergeant": i.interrogator_sergeant.get_full_name(),
                "detective": i.interrogator_detective.get_full_name(),
                "sergeant_score": i.sergeant_score,
                "detective_score": i.detective_score,
                "capitan_verdict": i.capitan_verdict,
                "chief_approved": i.chief_approved,
                "created_at": i.created_at if hasattr(i, "created_at") else None,
            }
            for i in interrogations
        ]

        return response.Response(data)

    @action(detail=True, methods=["get"])
    def summary(self, request, pk=None):
        """
        Get summary information about the suspect
        """
        suspect = self.get_object()

        interrogations = Interrogation.objects.filter(suspect=suspect)
        total_interrogations = interrogations.count()
        approved_interrogations = interrogations.filter(chief_approved=True).count()

        avg_sergeant_score = None
        avg_detective_score = None

        if total_interrogations > 0:
            avg_sergeant_score = interrogations.exclude(
                sergeant_score__isnull=True
            ).aggregate(avg=models.Avg("sergeant_score"))["avg"]

            avg_detective_score = interrogations.exclude(
                detective_score__isnull=True
            ).aggregate(avg=models.Avg("detective_score"))["avg"]

        return response.Response(
            {
                "suspect_id": suspect.id,
                "person_name": suspect.person.get_full_name()
                if suspect.person
                else None,
                "case_number": suspect.case.case_number if suspect.case else None,
                "suspect_status": suspect.suspect_status,
                "statistics": {
                    "total_interrogations": total_interrogations,
                    "approved_interrogations": approved_interrogations,
                    "avg_sergeant_score": avg_sergeant_score,
                    "avg_detective_score": avg_detective_score,
                },
            }
        )


class InterrogationViewSet(viewsets.ModelViewSet):
    queryset = Interrogation.objects.all()
    serializer_class = InterrogationListSerializer
    permission_classes = [permissions.IsAuthenticated, IsNotBaseUser]

    http_method_names = ["get" , "post", "patch"]  # add more

    def get_serializer_class(self):
        if self.action == "capitan_comment":
            return CapitanCommentSerializer
        return super().get_serializer_class()

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'score': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1, maximum=10),
            },
            required=['score']
        )
    )
    @action(detail=True, methods=["post"], url_path='submit-sergeant-score')
    def submit_sergeant_score(self, request, pk=None):
        """Sergeant submits their guilt probability score (1-10)"""
        interrogation = self.get_object()
        
        if interrogation.interrogator_sergeant != request.user:
            raise exceptions.PermissionDenied("You are not the sergeant for this interrogation")
        
        score = request.data.get('score')
        if not score or not (1 <= int(score) <= 10):
            raise exceptions.ValidationError("Score must be between 1 and 10")
        
        interrogation.sergeant_score = int(score)
        interrogation.save()
        interrogation.update_status_after_scores()
        
        return response.Response({
            'message': 'Sergeant score submitted successfully',
            'interrogation_id': interrogation.id,
            'sergeant_score': interrogation.sergeant_score,
            'status': interrogation.status
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'score': openapi.Schema(type=openapi.TYPE_INTEGER, minimum=1, maximum=10),
            },
            required=['score']
        )
    )
    @action(detail=True, methods=["post"], url_path='submit-detective-score')
    def submit_detective_score(self, request, pk=None):
        """Detective submits their guilt probability score (1-10)"""
        interrogation = self.get_object()
        
        if interrogation.interrogator_detective != request.user:
            raise exceptions.PermissionDenied("You are not the detective for this interrogation")
        
        score = request.data.get('score')
        if not score or not (1 <= int(score) <= 10):
            raise exceptions.ValidationError("Score must be between 1 and 10")
        
        interrogation.detective_score = int(score)
        interrogation.save()
        interrogation.update_status_after_scores()
        
        return response.Response({
            'message': 'Detective score submitted successfully',
            'interrogation_id': interrogation.id,
            'detective_score': interrogation.detective_score,
            'status': interrogation.status
        })

    @action(detail=True, methods=["post"])
    def capitan_comment(self, request, pk=None):
        """Captain submits verdict and comment"""
        interrogation = self.get_object()
        
        if not request.user.groups.filter(name='Captain').exists():
            raise exceptions.PermissionDenied("Only captains can submit verdicts")
        
        if interrogation.status != InterrogationStatus.SCORES_COMPLETED:
            raise exceptions.ValidationError("Scores must be completed before captain verdict")
        
        serializer = CapitanCommentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        interrogation.capitan_comment = serializer.validated_data['comment']
        interrogation.capitan_verdict = serializer.validated_data['verdict']
        interrogation.captain_decided_at = timezone.now()
        interrogation.status = InterrogationStatus.CAPTAIN_DECIDED
        
        # Check if chief approval is needed (CRITICAL crimes)
        if interrogation.requires_chief_approval():
            interrogation.status = InterrogationStatus.PENDING_CHIEF
        else:
            interrogation.status = InterrogationStatus.COMPLETED
        
        interrogation.save()
        
        return response.Response({
            'message': 'Captain verdict submitted successfully',
            'interrogation_id': interrogation.id,
            'verdict': interrogation.capitan_verdict,
            'requires_chief_approval': interrogation.requires_chief_approval(),
            'status': interrogation.status
        })

    @swagger_auto_schema(
        method='post',
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'approved': openapi.Schema(type=openapi.TYPE_BOOLEAN),
            },
            required=['approved']
        )
    )
    @action(detail=True, methods=["post"], url_path='chief-approval')
    def chief_approval(self, request, pk=None):
        """Police Chief approves or rejects captain's verdict (for CRITICAL cases only)"""
        interrogation = self.get_object()
        
        if not request.user.groups.filter(name='Chief').exists():
            raise exceptions.PermissionDenied("Only the police chief can approve verdicts")
        
        if interrogation.status != InterrogationStatus.PENDING_CHIEF:
            raise exceptions.ValidationError("This interrogation is not pending chief approval")
        
        if not interrogation.requires_chief_approval():
            raise exceptions.ValidationError("This case doesn't require chief approval")
        
        approved = request.data.get('approved')
        if approved is None:
            raise exceptions.ValidationError("'approved' field is required")
        
        from interrogation.models import PoliceChiefApproval
        interrogation.chief_approved = PoliceChiefApproval.APPROVED if approved else PoliceChiefApproval.NOT_APPROVED
        interrogation.chief_approved_at = timezone.now()
        interrogation.status = InterrogationStatus.COMPLETED
        interrogation.save()
        
        return response.Response({
            'message': 'Chief approval submitted successfully',
            'interrogation_id': interrogation.id,
            'chief_approved': interrogation.chief_approved,
            'status': interrogation.status
        })
    
    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("make it using  Suspect")


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def most_wanted_view(request):
    """
    Public view showing most wanted suspects with their ranking and rewards.
    According to project requirements:
    - Ranking = max(L_j) * max(D_i)
    - Reward = max(L_j) * max(D_i) * 20,000,000 Rials
    """
    most_wanted = get_most_wanted_list()
    
    results = []
    for item in most_wanted:
        suspect = item['suspect']
        person = item['person']
        
        results.append({
            'rank': len(results) + 1,
            'suspect_id': str(suspect.id),
            'person': {
                'id': person.id,
                'username': person.username,
                'full_name': person.full_name,
                'national_id': person.national_id,
                'phone_number': person.phone_number,
            },
            'photo': None,  # Add photo field if you have it in User model
            'ranking_score': item['ranking'],
            'max_days_wanted': item['max_days_wanted'],
            'max_crime_severity': item['max_crime_severity'],
            'reward_amount': item['reward_amount'],
            'reward_formatted': f"{item['reward_amount']:,} ریال",
            'cases_involved': item['cases_involved'],
            'current_case': {
                'id': str(suspect.case.id),
                'case_number': suspect.case.case_number,
                'crime_type': suspect.case.crime_type,
            }
        })
    
    return response.Response({
        'count': len(results),
        'most_wanted': results
    })


class CourtViewSet(viewsets.ModelViewSet):
    """
    ViewSet for judges to manage court cases and submit verdicts.
    """
    queryset = Court.objects.all()
    serializer_class = CourtSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy', 'submit_verdict']:
            from users.permissions import IsJudge
            return [permissions.IsAuthenticated(), IsJudge()]
        return [permissions.IsAuthenticated()]
    
    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user
        
        # Judges see only their cases
        if user.groups.filter(name='Judge').exists():
            return qs.filter(judge=user)
        
        # Others can see all (police can view for reference)
        return qs
    
    def perform_create(self, serializer):
        """Create court case for a completed interrogation"""
        serializer.save(judge=self.request.user)
    
    @swagger_auto_schema(
        method='post',
        operation_description="Judge submits final verdict and punishment",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'verdict': openapi.Schema(
                    type=openapi.TYPE_STRING, 
                    enum=['GUILTY', 'NOT_GUILTY'],
                    description='Final verdict'
                ),
                'punishment_title': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Title of punishment (if guilty)'
                ),
                'punishment_description': openapi.Schema(
                    type=openapi.TYPE_STRING,
                    description='Detailed description of punishment'
                ),
            },
            required=['verdict']
        )
    )
    @action(detail=True, methods=['post'], url_path='submit-verdict')
    def submit_verdict(self, request, pk=None):
        """Judge submits final verdict"""
        court = self.get_object()
        
        if court.judge != request.user:
            raise exceptions.PermissionDenied("You are not the judge for this case")
        
        if court.final_verdict:
            raise exceptions.ValidationError("Verdict already submitted for this case")
        
        verdict = request.data.get('verdict')
        if verdict not in ['GUILTY', 'NOT_GUILTY']:
            raise exceptions.ValidationError("Verdict must be GUILTY or NOT_GUILTY")
        
        court.final_verdict = verdict
        court.verdict_date = timezone.now()
        
        if verdict == VerdictStatus.GUILTY:
            punishment_title = request.data.get('punishment_title', '')
            punishment_desc = request.data.get('punishment_description', '')
            
            if not punishment_title or not punishment_desc:
                raise exceptions.ValidationError(
                    "Punishment title and description are required for guilty verdict"
                )
            
            court.punishment_title = punishment_title
            court.punishment_description = punishment_desc
        
        court.save()
        
        return response.Response({
            'message': 'Verdict submitted successfully',
            'court_id': str(court.id),
            'verdict': court.final_verdict,
            'punishment_title': court.punishment_title if verdict == 'GUILTY' else None,
        }, status=status.HTTP_200_OK)
    
    @action(detail=True, methods=['get'], url_path='case-details')
    def case_details(self, request, pk=None):
        """Get complete case details for court review"""
        court = self.get_object()
        interrogation = court.interrogation
        suspect = interrogation.suspect
        case = suspect.case
        
        # Gather all evidences
        from evidences.models import Evidence
        evidences = Evidence.objects.filter(case=case)
        
        # Get all involved personnel
        from detection.models import Detection
        detection = None
        if hasattr(case, 'detection'):
            detection = case.detection
        
        return response.Response({
            'court': CourtSerializer(court).data,
            'case': {
                'id': str(case.id),
                'case_number': case.case_number,
                'crime_type': case.crime_type,
                'created_at': case.created_at,
                'status': case.status,
            },
            'suspect': {
                'id': str(suspect.id),
                'person': {
                    'id': suspect.person.id,
                    'username': suspect.person.username,
                    'full_name': suspect.person.full_name,
                    'national_id': suspect.person.national_id,
                },
                'status': suspect.suspect_status,
                'detail': suspect.detail,
            },
            'interrogation': {
                'id': str(interrogation.id),
                'sergeant': interrogation.interrogator_sergeant.username,
                'detective': interrogation.interrogator_detective.username,
                'sergeant_score': interrogation.sergeant_score,
                'detective_score': interrogation.detective_score,
                'captain_verdict': interrogation.capitan_verdict,
                'captain_comment': interrogation.capitan_comment,
                'chief_approved': interrogation.chief_approved,
            },
            'detection': {
                'detective': detection.detective.username if detection else None,
                'sergeant': detection.sergeant.username if detection and detection.sergeant else None,
            } if detection else None,
            'evidences_count': evidences.count(),
        })

