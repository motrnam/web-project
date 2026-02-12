from django.shortcuts import render
from rest_framework import viewsets
from rest_framework.response import Response
from rest_framework import viewsets, permissions, status, exceptions

from case.models import RegisterComplain
from case.serializers import RegisterComplainSerializers

# Create your views here.

class RegisterComplainViewSet(viewsets.ModelViewSet):
    serializer_class = RegisterComplainSerializers
    queryset = RegisterComplain.objects.all()
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    # todo 