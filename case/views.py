from django.shortcuts import get_object_or_404, render
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, exceptions

from case.models import RegisterComplain, Case, RequestForCaseStatus
from case.serializers import CaseSerializers, RegisterComplainSerializers, RequestCheckSerializers
from rest_framework.decorators import action
from drf_yasg.utils import swagger_auto_schema


from users.permissions import IsCadet, IsNotBaseUser, IsPoliceOfficer , IsOwner

# Create your views here.


class RegisterComplainViewSet(viewsets.ModelViewSet):
    serializer_class = RegisterComplainSerializers
    queryset = RegisterComplain.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Register a new complain",
        request_body=RegisterComplainSerializers,
        responses={201: RegisterComplainSerializers, 400: "Bad Request"},
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def get_serializer_class(self):
        if self.action in ["accept", "reject", "send_to_sender"]:
            return RequestCheckSerializers
        return super().get_serializer_class()

    def get_object(self):
        obj = super().get_object()
        user = self.request.user

        is_cadet = user.groups.filter(name="Cadet").exists()
        is_owner = obj.user == user

        if not (is_cadet or is_owner):
            raise exceptions.PermissionDenied(
                "You do not have permission to access this."
            )

        cadet_action = ["send_to_sender", "update", "partial_update"]
        owner_action = ["update", "partial_update"]

        if self.action in cadet_action:
            if not is_cadet:
                raise exceptions.PermissionDenied(
                    "Only cadets can perform this action."
                )
            if obj.status != RequestForCaseStatus.PENDING:
                raise exceptions.NotAcceptable(
                    "Complaint has already been processed and cannot be modified."
                )
            if obj.TTL <= 0:
                raise exceptions.NotAcceptable(
                    "Complaint has reached the maximum number of modifications (3)."
                )
            return obj
        elif self.action in owner_action:
            if not is_owner:
                raise exceptions.PermissionDenied(
                    "Only the owner can perform this action."
                )
            if (
                obj.status != RequestForCaseStatus.PENDING
                and obj.status != RequestForCaseStatus.RETURN_TO_SENDER
            ):
                raise exceptions.NotAcceptable(
                    "Complaint has already been processed and cannot be modified."
                )
            if obj.TTL <= 0:
                raise exceptions.NotAcceptable(
                    "Complaint has reached the maximum number of modifications (3)."
                )
            return obj
        return obj

    @action(detail=True, methods=["post"], permission_classes=[IsCadet])
    def accept(self, request, pk=None):
        return self._process_complaint_status(
            request, RequestForCaseStatus.ACCEPTED, create_case=True
        )

    @action(detail=True, methods=["post"], permission_classes=[IsCadet])
    def reject(self, request, pk=None):
        return self._process_complaint_status(request, RequestForCaseStatus.REJECTED)

    @action(detail=True, methods=["post"], permission_classes=[IsCadet])
    def return_to_sender(self, request, pk=None):
        return self._process_complaint_status(
            request, RequestForCaseStatus.RETURN_TO_SENDER
        )

    def _process_complaint_status(self, request, new_status, create_case=False):
        complain = self.get_object()
        if not complain:
            raise exceptions.NotFound("Complain not found")
        if complain.TTL <= 0:
            raise exceptions.NotAcceptable("Complaint modified more than 3 times")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        serializer.save(request=complain, checked_by=request.user)
        complain.status = new_status
        complain.TTL -= 1
        complain.save()

        if create_case:
            Case.objects.create(complain=complain)

        return Response(serializer.data, status=status.HTTP_200_OK)


class CaseViewSet(viewsets.ModelViewSet):
    serializer_class = CaseSerializers
    queryset = Case.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update"]:
            return [IsPoliceOfficer(),IsOwner()]
        return super().get_permissions()
    
    # @action(detail=False, methods=['get'],permission_classes=[permissions.IsAuthenticated])
    # def me(self, request):
    #     cases = self.get_queryset().filter(petrol_creator=request.user)
    #     serializer = self.get_serializer(cases, many=True)
    #     return Response(serializer.data)
    
    def get_queryset(self):
        if self.request.user.groups.count() > 1: # TEMP
            return Case.objects.all()
        return Case.objects.filter(request__creator = self.request.us)
    
    @swagger_auto_schema(auto_schema=None)
    def destroy(self, request, *args, **kwargs):
        raise exceptions.MethodNotAllowed("DELETE")
    
    @action(detail=True, methods=["post"])
    def add_witness(self,request,pk=None):
        case  = get_object_or_404(Case, pk=id)

        return Response({"todo","todo"},status=status.HTTP_418_IM_A_TEAPOT)
    
    @action(detail=True, methods=["post"])
    def add_complain(self,request,pk=None):
        case  = get_object_or_404(Case, pk=id)
        return Response({"todo","todo"},status=status.HTTP_418_IM_A_TEAPOT)
    
    @action(detail=True,methods=["post"])
    def accept_complain(self,request,pk=None):
        case  = get_object_or_404(Case, pk=id)
        return Response({"todo","todo"},status=status.HTTP_418_IM_A_TEAPOT)