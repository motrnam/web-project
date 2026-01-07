from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, exceptions
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token


from .serializers import (
    ProfileSerializer,
    RegisterSerializer,
)
from .models import Profile


class RegisterViewSet(viewsets.ModelViewSet):
    serializer_class = RegisterSerializer
    queryset = Profile.objects.all()
    http_method_names = ['post']
    
    @swagger_auto_schema(
        operation_description="Register a new user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
                'first_name': openapi.Schema(type=openapi.TYPE_STRING, description='First Name'),
                'last_name': openapi.Schema(type=openapi.TYPE_STRING, description='Last Name'),
                'national_id': openapi.Schema(type=openapi.TYPE_STRING, description='National ID'),
                'phone_number': openapi.Schema(type=openapi.TYPE_STRING, description='Phone Number'),
                'email': openapi.Schema(type=openapi.TYPE_STRING, description='Email Address'),
            },
            required=['username', 'password', 'national_id', 'phone_number', 'email']
        ),
        responses={
            201: RegisterSerializer,
            400: openapi.Response(description="Bad Request"),
        }
    )    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class ProfileViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = ProfileSerializer
    queryset = Profile.objects.all()
    http_method_names = ['get']

    @action(detail=False, methods=['get'], permission_classes =[permissions.IsAuthenticated])
    def me(self, request):
        profile = self.get_queryset().get(user=request.user)
        serializer = self.get_serializer(profile)
        return Response(serializer.data)
    
class LoginAPIView(APIView):
    @swagger_auto_schema(
        operation_description="Login with username/email and password",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description="Username or Email or National ID"),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description="User password"),
            },
        ),
        responses={
            200: openapi.Response(description="Login successful"),
            401: openapi.Response(description="Invalid credentials"),
            400: openapi.Response(description="Missing fields")
        }
    )
    def post(self, request):
        username = request.data.get("username")
        password = request.data.get("password")
        
        if not username:
            email = request.data.get("email")
            if email:
                try:
                    profile = Profile.objects.get(email=email)
                    username = profile.user.username
                except Profile.DoesNotExist:
                    raise exceptions.AuthenticationFailed("Invalid credentials")
        if not username:
            national_id = request.data.get("national_id")
            if national_id:
                try:
                    profile = Profile.objects.get(national_id=national_id)
                    username = profile.user.username
                except Profile.DoesNotExist:
                    raise exceptions.AuthenticationFailed("Invalid credentials")
        if not username:
            phone = request.data.get("phone_number")
            if phone:
                try:
                    profile = Profile.objects.get(phone_number=phone)
                    username = profile.user.username
                except Profile.DoesNotExist:
                    raise exceptions.AuthenticationFailed("Invalid credentials")
                
        if not username or not password:
            raise exceptions.ParseError("Username and password are required")
        
        user = authenticate(
            request,
            username=username,
            password=password
        )

        if user:
            login(request, user)
            return Response(
                {"message": "Login successful"},
                status=status.HTTP_200_OK
            )

        return Response(
            {"error": "Invalid credentials"},
            status=status.HTTP_401_UNAUTHORIZED
        )

class LogoutAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        operation_description="Logout the current user",
        responses={
            200: openapi.Response(description="Logout successful"),
            401: openapi.Response(description="Authentication required")
        }
    )
    def post(self, request):
        request.user.auth_token.delete()
        try:
            request.user.auth_token.delete()
        except Token.DoesNotExist:
            raise exceptions.NotAcceptable("Invalid Token")
        response = Response(
            {"message": "Logout successful"},
            status=status.HTTP_200_OK
        )
        response.delete_cookie('sessionid')
        return response
