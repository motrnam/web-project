#interrogation/views.py
from rest_framework import viewsets, permissions, exceptions, response, status
from rest_framework.decorators import action

from users.permissions import IsNotBaseUser, IsJudge
from .models import Suspect, Interrogation, VerdictStatus, Court , Punishment
from .serializers import (
    InterrogationListSerializer,
    SuspectSerializer,
    InterrogationWriteSerializer,
    CapitanCommentSerializer,
    CourtSerializer,
    PunishmentSerializer,
)
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

    http_method_names = ["get", "post"]

    def get_queryset(self):
        """Filter queryset based on user role"""
        queryset = Interrogation.objects.all()
        user = self.request.user

        if user.groups.filter(name="Sergeant").exists():
            queryset = queryset.filter(interrogator_sergeant=user)
        elif user.groups.filter(name="Detective").exists():
            queryset = queryset.filter(interrogator_detective=user)
        elif user.groups.filter(name="Captain").exists():
            queryset = queryset.filter(capitan_verdict=VerdictStatus.PENDING)
        elif user.groups.filter(name="Chief").exists():
            queryset = queryset.filter(chief_approved=False)

        return queryset

    def get_serializer_class(self):
        if self.action == "capitan_comment":
            return CapitanCommentSerializer
        elif self.action == "add_court":
            return CourtSerializer
        return super().get_serializer_class()

    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("make it using  Suspect")

    @action(detail=True, methods=["post"])
    def capitan_comment(self, request, pk=None):
        """Add captain's comment and verdict to an interrogation"""
        interrogation = self.get_object()
        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            # Update interrogation with captain's comment and verdict
            interrogation.capitan_comment = serializer.validated_data["comment"]
            interrogation.capitan_verdict = serializer.validated_data["verdict"]
            interrogation.save()

            return response.Response(
                {
                    "message": "Captain comment and verdict added successfully",
                },
                status=status.HTTP_200_OK,
            )

        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=["post"])
    def chief_approve(self, request, pk=None):
        """Chief approves the interrogation"""
        interrogation = self.get_object()

        # Check if user is chief
        if not request.user.groups.filter(name="Chief").exists():
            return response.Response(
                {"error": "Only chiefs can approve interrogations"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Check if captain has provided verdict
        if interrogation.capitan_verdict == VerdictStatus.PENDING:
            return response.Response(
                {"error": "Captain must provide verdict before chief approval"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        interrogation.chief_approved = True
        interrogation.save()

        return response.Response(
            {
                "message": "Interrogation approved successfully",
            }
        )

    @action(detail=False, methods=["get"])
    def pending_captain_review(self, request):
        """Get interrogations pending captain review"""
        queryset = self.get_queryset().filter(capitan_verdict=VerdictStatus.PENDING)
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = InterrogationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = InterrogationListSerializer(queryset, many=True)
        return response.Response(serializer.data)

    @action(detail=False, methods=["get"])
    def pending_chief_approval(self, request):
        """Get interrogations pending chief approval"""
        queryset = self.get_queryset().filter(
            chief_approved=False,
            capitan_verdict__in=[VerdictStatus.APPROVED, VerdictStatus.REJECTED],
        )
        page = self.paginate_queryset(queryset)

        if page is not None:
            serializer = InterrogationListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = InterrogationListSerializer(queryset, many=True)
        return response.Response(serializer.data)

    @action(detail=True, methods=["post"])
    def submit_scores(self, request, pk=None):
        """Submit scores for interrogation (by sergeants/detectives)"""
        interrogation = self.get_object()
        user = request.user

        if user.groups.filter(name="Sergeant").exists():
            if "sergeant_score" not in request.data:
                return response.Response(
                    {"error": "sergeant_score is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            interrogation.sergeant_score = request.data["sergeant_score"]
            message = "Sergeant score submitted successfully"

        elif user.groups.filter(name="Detective").exists():
            if "detective_score" not in request.data:
                return response.Response(
                    {"error": "detective_score is required"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            interrogation.detective_score = request.data["detective_score"]
            message = "Detective score submitted successfully"

        else:
            return response.Response(
                {"error": "Only sergeants and detectives can submit scores"},
                status=status.HTTP_403_FORBIDDEN,
            )

        interrogation.save()
        return response.Response(
            {
                "message": message,
            }
        )

    @action(detail=True, methods=["post"], permission_classes=[IsJudge])
    def add_court(self, request, pk=None):
        """Create a court for a specific interrogation"""
        interrogation = self.get_object()

        # Check if a court already exists for this interrogation
        if Court.objects.filter(interrogation=interrogation).exists():
            raise exceptions.NotAcceptable(
                "court already exists for this interrogation"
            )

        serializer = self.get_serializer(data=request.data)

        if serializer.is_valid():
            court = serializer.save(
                interrogation=interrogation,
                judge=request.user,  # Set the current user as the judge
            )

            return response.Response(
                {
                    "message": "Court created successfully",
                    "court_id": court.id,
                    "court_date": court.date,
                    "judge": court.judge.username,
                },
                status=status.HTTP_201_CREATED,
            )

        return response.Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourtViewSet(viewsets.ModelViewSet):
    queryset = Court.objects.all()
    serializer_class = CourtSerializer
    permission_classes = [permissions.IsAuthenticated]

    http_method_names = ["get", "post", "put", "patch"]
    
    def get_serializer_class(self):
        if self.action == 'punish':
            return PunishmentSerializer
        return super().get_serializer_class()

    @action(detail=False, methods=["get"], permission_classes=[IsJudge])
    def me(self, request):
        """Get courts assigned to the current judge"""
        queryset = Court.objects.filter(judge=request.user)

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return response.Response(serializer.data)

    def perform_update(self, serializer):
        """Update court but prevent changing judge and interrogation"""
        if (
            self.request.user != self.get_object().judge
            and not self.request.user.groups.filter(name="Chief").exists()
        ):
            raise exceptions.PermissionDenied("Only judge or chief can edit the case")
        serializer.save()
    
    @action(detail=True, methods=["post"], url_path="punish")
    def punish(self, request, pk=None):
        """Create a punishment for a specific court"""
        court = self.get_object()
        
        if not court:
            raise exceptions.NotFound("Not such court found")
        
        if (request.user != court.judge and 
            not request.user.groups.filter(name="Chief").exists()):
            raise exceptions.PermissionDenied(
                "Only the court's judge or chief can add punishments"
            )
        
        punishment_data = request.data.copy()
        punishment_data['court'] = court.id
        
        serializer = self.get_serializer(data = punishment_data)
        
        if serializer.is_valid():
            serializer.save()
            return response.Response(
                serializer.data, 
                status=status.HTTP_201_CREATED
            )
        return response.Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )
        
    @action(detail=True, methods=["get"], url_path="punishments")
    def list_punishments(self, request, pk=None):
        """List all punishments for a specific court"""
        court = self.get_object()
        
        if (request.user != court.judge and 
            not request.user.groups.filter(name="Chief").exists() and
            not request.user.groups.filter(name="Judge").exists()):
            raise exceptions.PermissionDenied(
                "You don't have permission to view these punishments"
            )
        
        punishments = Punishment.objects.filter(court=court)
        
        serializer = self.get_serializer(punishments, many=True)
        
        return response.Response({
            'court': court.id,
            'judge': str(court.judge) if court.judge else None,
            'total_punishments': punishments.count(),
            'punishments': serializer.data
        })



class Punishment(viewsets.ModelViewSet):
    queryset = Punishment.objects.all()
    serializer_class = PunishmentSerializer
    http_method_names = ["get", "post", "put", "patch"]
