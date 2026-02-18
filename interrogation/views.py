#interrogation/views.py
from rest_framework import viewsets, permissions, exceptions, response, status
from rest_framework.decorators import action

from users.permissions import IsNotBaseUser
from .models import Suspect, Interrogation
from .serializers import (
    InterrogationListSerializer,
    SuspectSerializer,
    InterrogationWriteSerializer,
    CapitanCommentSerializer,
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

    http_method_names = ["get" , "post"]  # add more

    def get_serializer_class(self):
        if self.action == "capitan_comment":
            return CapitanCommentSerializer
        return super().get_serializer_class()

    @action(detail=True, methods=["post"])
    def capitan_comment(self, request, pk=None):
        return response.responses({"todo":"todo"})
    
    @swagger_auto_schema(auto_schema=None)
    def create(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("make it using  Suspect")
