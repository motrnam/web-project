from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, exceptions
from rest_framework.decorators import action
from rest_framework.views import APIView
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token
from django.contrib.auth import get_user_model

import logging
logger = logging.getLogger(__name__)




User = get_user_model()
    

    
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
                    profile = User.objects.get(email=email)
                    username = profile.username
                except User.DoesNotExist:
                    raise exceptions.AuthenticationFailed("Invalid credentials1")
        if not username:
            national_id = request.data.get("national_id")
            if national_id:
                try:
                    profile = User.objects.get(national_id=national_id)
                    username = profile.username
                except User.DoesNotExist:
                    raise exceptions.AuthenticationFailed("Invalid credentials2")
        if not username:
            phone = request.data.get("phone_number")
            if phone:
                try:
                    profile = User.objects.get(phone_number=phone)
                    username = profile.username
                except User.DoesNotExist:
                    raise exceptions.AuthenticationFailed("Invalid credentials3")
                
        if not username or not password:
            raise exceptions.ParseError("Username and password are required")
        
        user = authenticate(
            request,
            username=username,
            password=password
        )
        print(f"{username = } , {password=}")
        if user:
            login(request, user)
            print(f"{user.password = }") # prints hashed (runserver)
            return Response(
                {"message": "Login successful"},
                status=status.HTTP_200_OK
            )
        else:
            try:
                user = User.objects.get(username=username) # print plain text (running test)
                print(f"{user.password = }")
                if user.check_password(password):
                    print("Password is correct but authentication failed - backend issue")
                else:
                    print("Password is incorrect")
                    print(f"Password hash: {user.password}")
            except User.DoesNotExist:
                print("user not")

        return Response(
            {"error": "Invalid credentials4"},
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
