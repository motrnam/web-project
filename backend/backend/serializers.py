from rest_framework import serializers
from django.contrib.auth.models import User , Group
from .models import (
    Profile,
)


class UserSimpleSerializer(serializers.ModelSerializer):
    groups = serializers.StringRelatedField(many=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'groups']

class ProfileSerializer(serializers.ModelSerializer):
    user = UserSimpleSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'national_id', 'phone_number', 'email', 'created_at', 'updated_at']


