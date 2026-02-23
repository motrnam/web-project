# backend/users/views.py
from rest_framework import generics, viewsets, permissions, status, exceptions
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserSimpleSerializer, GrantSerializer
from rest_framework.decorators import action
from rest_framework.response import Response
from .permissions import IsAdministrator
from django.contrib.auth.models import Group
from users.serializers import UserSimpleSerializer
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authentication import TokenAuthentication
from rest_framework.authtoken.models import Token

UserModel = get_user_model()


class RegisterView(generics.CreateAPIView):
    """فقط برای ثبت‌نام - POST /register/"""
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]
    queryset = UserModel.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Save user
        if not UserModel.objects.exists():
            user = serializer.save()
            admin_group = Group.objects.get_or_create(name="Administrator")[0]
            user.groups.add(admin_group)
        else:
            user = serializer.save()

        # Create token for the user
        token, created = Token.objects.get_or_create(user=user)

        # Return token along with user data
        return Response({
            'user': serializer.data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)


class UserViewSet(viewsets.ModelViewSet):
    """
    مدیریت کاربران - فقط برای Admin
    GET /users/ - لیست کاربران
    GET/PUT/PATCH/DELETE /users/{id}/ - مدیریت کاربر خاص
    POST /users/grant-role/ - دادن نقش
    """
    authentication_classes = [TokenAuthentication]
    queryset = UserModel.objects.all()
    serializer_class = UserSimpleSerializer
    permission_classes = [permissions.IsAuthenticated, IsAdministrator]

    def get_serializer_class(self):
        if self.action == "grant_role":
            return GrantSerializer
        return UserSimpleSerializer

    @action(detail=False, methods=["get"], authentication_classes=[TokenAuthentication],
            permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """پروفایل کاربر فعلی - GET /users/me/"""
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], authentication_classes=[TokenAuthentication],
            permission_classes=[permissions.IsAuthenticated])
    def roles(self, request):
        """نقش‌های کاربر فعلی - GET /users/roles/"""
        groups = request.user.groups.all()
        return Response({
            "username": request.user.username,
            "roles": [group.name for group in groups]
        })

    @action(detail=False, methods=["post"], authentication_classes=[TokenAuthentication],
            permission_classes=[IsAdministrator])
    def grant_role(self, request):
        """دادن نقش به کاربر - POST /users/grant-role/"""
        serializer = GrantSerializer(data=request.data)
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


class CustomAuthToken(ObtainAuthToken):
    """
    ورود با username OR national_id OR phone_number OR email
    POST /api-token-auth/
    {
        "username": "09123456789"  ← می‌تواند هر کدام از ۴ فیلد باشد
        "password": "mypassword"
    }
    """

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data,
                                           context={'request': request})
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)

        return Response({
            'token': token.key,
            'user': UserSimpleSerializer(user).data
        })
