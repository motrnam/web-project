# backend/users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group

UserModel = get_user_model()


class UserSimpleSerializer(serializers.ModelSerializer):
    groups = serializers.StringRelatedField(many=True, read_only=True)
    roles = serializers.SerializerMethodField()
    photo_url = serializers.SerializerMethodField()

    class Meta:
        model = UserModel
        fields = ["id", "username", "full_name", "email", "groups", "roles", "photo_url"]

    def get_roles(self, obj):
        return obj.get_roles_display()

    def get_photo_url(self, obj):
        if obj.photo:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.photo.url)
            return obj.photo.url
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = UserModel
        fields = [
            "username",
            "password",
            "full_name",
            "national_id",
            "phone_number",
            "email",
        ]

    def create(self, validated_data):
        user = UserModel.objects.create_user(
            username=validated_data["username"],
            password=validated_data["password"],
            full_name=validated_data.get("full_name", ""),
            national_id=validated_data["national_id"],
            phone_number=validated_data["phone_number"],
            email=validated_data["email"],
        )
        default_group, _ = Group.objects.get_or_create(name="Base User")
        user.groups.add(default_group)
        return user


class GrantSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    role = serializers.ChoiceField(
        choices=[
            "Cadet",
            "Police Officer",
            "Patrol Officer",
            "Detective",
            "Sergeant",
            "Captain",
            "Chief",
            "Coroner",
            "Judge",
        ]
    )
