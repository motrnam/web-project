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


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    username = serializers.CharField(write_only=True)
    first_name = serializers.CharField(write_only=True, required=False)
    last_name = serializers.CharField(write_only=True, required=False)
    class Meta:
        model = Profile
        fields = ['national_id','phone_number','email', 'username', 'password', 'first_name', 'last_name']
        
    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data['username'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', '')
        )
        defualt_group = Group.objects.get_or_create(name='default')[0]
        user.groups.add(defualt_group)
        profile = Profile.objects.create(
            user=user,
            national_id=validated_data['national_id'],
            phone_number=validated_data['phone_number'],
            email=validated_data['email']
        )
        return profile
    
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation.pop('password', None)  
        return representation
