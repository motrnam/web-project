#interrogation/serializers.py
from rest_framework import serializers
from .models import Interrogation, Suspect, Court, VerdictStatus
from django.core.exceptions import ValidationError


class SuspectSerializer(serializers.ModelSerializer):
    person_details = serializers.SerializerMethodField(read_only=True)
    case_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Suspect
        fields = [
            "id",
            "person",
            "case",
            "detail",
            "suspect_status",
            "person_details",
            "case_details",
        ]
        read_only_fields = ["id", "case","person"]

    def get_person_details(self, obj):
        """Return basic user information"""
        if obj.person:
            return {
                "username": obj.person.username,
                "email": obj.person.email,
            }
        return None

    def get_case_details(self, obj):
        """Return basic case information"""
        if obj.case:
            return {
                "id": obj.case.id,
                "title": getattr(obj.case, "title", None),
            }
        return None

    def validate(self, data):
        """Optional: Add cross-field validation"""
        if self.instance is None:
            person = data.get("person")
            case = data.get("case")
            if person and case:
                if Suspect.objects.filter(person=person, case=case).exists():
                    raise serializers.ValidationError(
                        "This person is already a suspect in this case."
                    )
        return data


class InterrogationSerializer(serializers.ModelSerializer):
    interrogator_sergeant_details = serializers.SerializerMethodField(read_only=True)
    interrogator_detective_details = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Interrogation
        fields = [
            "id",
            "suspect",
            "interrogator_sergeant",
            "interrogator_detective",
            "sergeant_score",
            "detective_score",
            "capitan_comment",
            "capitan_verdict",
            "chief_approved",
            "interrogator_sergeant_details",
            "interrogator_detective_details",
        ]

    def get_interrogator_sergeant_details(self, obj):
        """Return sergeant information"""
        if obj.interrogator_sergeant:
            return {
                "id": obj.interrogator_sergeant.id,
                "username": obj.interrogator_sergeant.username,
                "full_name": obj.interrogator_sergeant.get_full_name(),
                "email": obj.interrogator_sergeant.email,
            }
        return None

    def get_interrogator_detective_details(self, obj):
        """Return detective information"""
        if obj.interrogator_detective:
            return {
                "id": obj.interrogator_detective.id,
                "username": obj.interrogator_detective.username,
                "full_name": obj.interrogator_detective.get_full_name(),
                "email": obj.interrogator_detective.email,
            }
        return None

    def create(self, validated_data):
        raise Exception("don't use this class as serializer")

    def update(self, instance, validated_data):
        """Update method with model's clean validation"""
        raise Exception("don't use this class as serializer")


class InterrogationListSerializer(serializers.ModelSerializer):
    sergeant_name = serializers.CharField(
        source="interrogator_sergeant.get_full_name", read_only=True
    )
    detective_name = serializers.CharField(
        source="interrogator_detective.get_full_name", read_only=True
    )

    class Meta:
        model = Interrogation
        fields = [
            "id",
            "sergeant_name",
            "detective_name",
            "sergeant_score",
            "detective_score",
            "capitan_verdict",
            "chief_approved",
        ]


class InterrogationWriteSerializer(serializers.ModelSerializer):
    """
    Write-only serializer for Interrogation model
    Used for create and update operations
    """

    class Meta:
        model = Interrogation
        fields = [
            "id",
            "suspect",
            "interrogator_sergeant",
            "interrogator_detective",
        ]
        read_only_fields = ["id","suspect"]
        extra_kwargs = {
            "interrogator_sergeant": {"required": True, "allow_null": False},
            "interrogator_detective": {"required": True, "allow_null": False},
            "suspect": {"required": True, "allow_null": False},
            "sergeant_score": {"min_value": 1, "max_value": 100},
            "detective_score": {"min_value": 1, "max_value": 100},
        }

    def validate_interrogator_sergeant(self, value):
        """Validate that sergeant belongs to Sergeant group"""
        if not value.groups.filter(name="Sergeant").exists():
            raise serializers.ValidationError(
                "Interrogator sergeant must be a member of the 'Sergeant' group."
            )
        return value

    def validate_interrogator_detective(self, value):
        """Validate that detective belongs to Detective group"""
        if not value.groups.filter(name="Detective").exists():
            raise serializers.ValidationError(
                "Interrogator detective must be a member of the 'Detective' group."
            )
        return value

    def validate(self, data):
        """Cross-field validation"""
        if data.get("interrogator_sergeant") and data.get("interrogator_detective"):
            if data["interrogator_sergeant"] == data["interrogator_detective"]:
                raise serializers.ValidationError(
                    "Sergeant and Detective must be different officers."
                )

        if (
            data.get("suspect")
            and not Suspect.objects.filter(id=data["suspect"].id).exists()
        ):
            raise serializers.ValidationError({"suspect": "Invalid suspect ID."})

        return data

    def create(self, validated_data):
        """Create with model validation"""
        instance = Interrogation(**validated_data)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, "message_dict") else str(e)
            )

        instance.save()
        return instance

    def update(self, instance, validated_data):
        """Update with model validation"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        try:
            instance.clean()
        except ValidationError as e:
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, "message_dict") else str(e)
            )

        instance.save()
        return instance


class CourtSerializer(serializers.ModelSerializer):
    class Meta:
        model = Court
        fields = "__all__"
        read_only_fields = ["id", "created_at"]


class CapitanCommentSerializer(serializers.Serializer):
    comment = serializers.CharField()  # an string
    verdict = serializers.ChoiceField(choices=VerdictStatus.choices)
