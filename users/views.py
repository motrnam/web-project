from rest_framework import viewsets, permissions, status
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSimpleSerializer
from rest_framework.decorators import action
from rest_framework.response import Response

UserModel = get_user_model()


class UserViewSet(viewsets.ModelViewSet):
    queryset = UserModel.objects.all()

    def get_serializer_class(self):
        if self.action == "create":
            return RegisterSerializer
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
        return Response(res, status=status.HTTP_200_OK)
