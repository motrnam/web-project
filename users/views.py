# users/views.py
from rest_framework import viewsets, permissions, status, exceptions
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSimpleSerializer, GrantSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import IsAdministrator
from django.contrib.auth.models import Group

UserModel = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return RegisterSerializer
        if self.action == "grant_role":
            return GrantSerializer
        return UserSimpleSerializer

    def get_permissions(self):
        if self.action == "create":
            return [permissions.AllowAny()]
        return [permissions.IsAuthenticated()]

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def ping(self, request):
        res = {"username": request.user.username, "message": "success"}
        if self.request.user.groups.filter(name="Administrator").exists():
            res["role"] = "admin"
        return Response(res, status=status.HTTP_200_OK)

    @action(
        detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated]
    )
    def role(self, request):
        groups = request.user.groups.all()
        return Response([group.name for group in groups])

    def perform_create(self, serializer):
        if not UserModel.objects.exists():
            user = serializer.save()
            admin_group = Group.objects.get_or_create(name="Administrator")[0]
            user.groups.add(admin_group)
        else:
            serializer.save()

    @action(detail=False, methods=["post"], permission_classes=[IsAdministrator])
    def grant_role(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data["username"]
        role = serializer.validated_data["role"]
        try:
            user = UserModel.objects.get(username=username)
            assigned_group, _ = Group.objects.get_or_create(name=role)
            user.groups.add(assigned_group)
            user.save()
            return Response(
                {"message": f"Role '{role}' granted to user '{username}' successfully"},
                status=status.HTTP_200_OK,
            )
        except UserModel.DoesNotExist:
            raise exceptions.NotFound("user does not exist")
