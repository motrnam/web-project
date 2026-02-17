from rest_framework import serializers
from .models import Suspect
from .models import User, Case  # Adjust imports based on your app structure
from .models import VerdictStatus, PoliceChiefApproval  # Import your choice classes
from .models import Interrogation, Suspect, User
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
        read_only_fields = ["id"]

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
    suspect_details = serializers.SerializerMethodField(read_only=True)
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
            "suspect_details",
            "interrogator_sergeant_details",
            "interrogator_detective_details",
        ]
        read_only_fields = [
            "id",
            "suspect",
            "chief_approved",
            "capitan_verdict",
            "sergeant_score",
            "detective_score",
            "capitan_comment",
        ]

    def get_suspect_details(self, obj):
        """Return basic suspect information"""
        if obj.suspect:
            return {
                "id": obj.suspect.id,
                "person_id": obj.suspect.person_id,
                "person_name": obj.suspect.person.get_full_name()
                if obj.suspect.person
                else None,
                "case_id": obj.suspect.case_id,
                "suspect_status": obj.suspect.suspect_status,
            }
        return None

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

    def validate_sergeant_score(self, value):
        """Additional validation for sergeant_score if needed"""
        if value < 1 or value > 100:
            raise serializers.ValidationError("Score must be between 1 and 100.")
        return value

    def validate_detective_score(self, value):
        """Additional validation for detective_score if needed"""
        if value < 1 or value > 100:
            raise serializers.ValidationError("Score must be between 1 and 100.")
        return value

    def validate(self, data):
        """
        Cross-field validation
        """
        # Check if sergeant and detective are the same person
        if data.get("interrogator_sergeant") and data.get("interrogator_detective"):
            if data["interrogator_sergeant"] == data["interrogator_detective"]:
                raise serializers.ValidationError(
                    "Sergeant and Detective must be different officers."
                )

        # Validate that suspect exists (though ForeignKey handles this)
        if (
            data.get("suspect")
            and not Suspect.objects.filter(id=data["suspect"].id).exists()
        ):
            raise serializers.ValidationError({"suspect": "Invalid suspect ID."})

        return data

    def create(self, validated_data):
        """Create method with model's clean validation"""
        instance = Interrogation(**validated_data)

        # Call the model's clean method to run the group validations
        try:
            instance.clean()
        except ValidationError as e:
            # Convert model ValidationError to DRF ValidationError
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, "message_dict") else str(e)
            )

        instance.save()
        return instance

    def update(self, instance, validated_data):
        """Update method with model's clean validation"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        # Call the model's clean method to run the group validations
        try:
            instance.clean()
        except ValidationError as e:
            # Convert model ValidationError to DRF ValidationError
            raise serializers.ValidationError(
                e.message_dict if hasattr(e, "message_dict") else str(e)
            )

        instance.save()
        return instance
