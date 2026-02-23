# backend/detection/serializers.py
from rest_framework import serializers
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from .models import Detection, DetectionBoard, Lead, Yarn, SuspectsSuggested
from evidences.models import Evidence
from evidences.serializers import EvidencePolymorphicSerializer
from interrogation.models import Suspect

User = get_user_model()


class DetectionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Detection
        fields = ['id', 'detective', 'case', 'detection_board', 'sergeant']
        read_only_fields = ['detective', 'detection_board']


class LeadSerializer(serializers.ModelSerializer):
    board_id = serializers.IntegerField(write_only=True)
    evidence_details = serializers.SerializerMethodField(read_only=True)
    content = serializers.CharField(required=False, allow_blank=True, allow_null=True)

    class Meta:
        model = Lead
        fields = [
            'id', 'title', 'board', 'board_id', 'lead_type',
            'evidence', 'evidence_details', 'content', 'position_x', 'position_y'
        ]
        read_only_fields = ['board']

    def get_evidence_details(self, obj):
        """Use the existing EvidencePolymorphicSerializer for evidence details."""
        if obj.evidence:
            return EvidencePolymorphicSerializer(obj.evidence, context=self.context).data
        return None

    def validate(self, data):
        # Custom validation logic from Lead.clean method
        if data.get('position_x', 0) <= 0 or data.get('position_x', 0) >= 1 or \
                data.get('position_y', 0) <= 0 or data.get('position_y', 0) >= 1:
            raise serializers.ValidationError("Position arguments must be between 0 and 1")

        lead_type = data.get('lead_type')
        evidence = data.get('evidence')
        content = data.get('content')

        if lead_type == 'E':
            if not evidence or content is not None:
                raise serializers.ValidationError(
                    'Lead must have evidence and no content for "Evidence" lead type.'
                )
        elif lead_type == 'N':
            if evidence is not None or not content:
                raise serializers.ValidationError(
                    'Lead must have content and no evidence for "Note" lead type.'
                )

        return data


class YarnSerializer(serializers.ModelSerializer):
    class Meta:
        model = Yarn
        fields = ['id', 'lead1', 'lead2']

    def validate(self, data):
        lead1 = data.get('lead1')
        lead2 = data.get('lead2')

        if lead1.board != lead2.board:
            raise serializers.ValidationError("Board arguments must match")

        if lead1 == lead2:
            raise serializers.ValidationError("You cannot connect a lead to itself")

        return data


# detection/serializers.py

class DetectionBoardSerializer(serializers.ModelSerializer):
    """Serializer for DetectionBoard model."""
    leads = LeadSerializer(many=True, read_only=True)
    detection_id = serializers.UUIDField(source='detection.id', read_only=True)
    case_id = serializers.UUIDField(source='detection.case.id', read_only=True)
    case_title = serializers.SerializerMethodField()
    detective_name = serializers.SerializerMethodField()
    sergeant_name = serializers.SerializerMethodField()

    class Meta:
        model = DetectionBoard
        fields = [
            'id',
            'title',
            'leads',
            'detection_id',
            'case_id',
            'case_title',
            'detective_name',
            'sergeant_name',
        ]
        read_only_fields = ['id', 'detection_id', 'case_id']

    def get_case_title(self, obj):
        """Get the case title or identifier."""
        if hasattr(obj, 'detection') and obj.detection and obj.detection.case:
            # You can customize this based on your Case model
            return str(obj.detection.case)  # or obj.detection.case.title if you have a title field
        return None

    def get_detective_name(self, obj):
        """Get the detective's full name."""
        if hasattr(obj, 'detection') and obj.detection and obj.detection.detective:
            detective = obj.detection.detective
            return f"{detective.first_name} {detective.last_name}".strip() or detective.username
        return None

    def get_sergeant_name(self, obj):
        """Get the sergeant's full name."""
        if hasattr(obj, 'detection') and obj.detection and obj.detection.sergeant:
            sergeant = obj.detection.sergeant
            return f"{sergeant.first_name} {sergeant.last_name}".strip() or sergeant.username
        return None

    def to_representation(self, instance):
        """Customize the representation."""
        data = super().to_representation(instance)

        # Add counts for convenience
        data['leads_count'] = instance.lead_set.count()

        return data


class SuspectsSuggestedSerializer(serializers.ModelSerializer):
    suspects_details = serializers.SerializerMethodField()
    state_display = serializers.CharField(source='get_state_display', read_only=True)

    class Meta:
        model = SuspectsSuggested
        fields = [
            'id', 'detection', 'time_suggested', 'detective_reasons',
            'state', 'state_display', 'feedback', 'suspects', 'suspects_details'
        ]
        read_only_fields = ['detection', 'time_suggested', 'state', 'feedback']

    def get_suspects_details(self, obj):
        return [
            {
                'id': user.id,
                'username': user.username,
                'full_name': f"{user.first_name} {user.last_name}".strip(),
                'email': user.email
            }
            for user in obj.suspects.all()
        ]


class SubmitSuspectsSerializer(serializers.Serializer):
    suspects = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=True
    )
    reasons = serializers.CharField(required=True, min_length=10)

    def validate_suspects(self, value):
        if not value:
            raise serializers.ValidationError("At least one suspect must be selected")

        # Optional: Validate that suspects are actual persons (not detectives/sergeants)
        # You might want to add additional validation here

        return value

    def validate_reasons(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Reasons must be at least 10 characters long")
        return value

    def validate(self, data):
        detection = self.context.get('detection')

        # Check if any of these suspects are already suspects in this case
        existing_suspects = Suspect.objects.filter(
            case=detection.case,
            person__in=data['suspects']
        ).values_list('person_id', flat=True)

        if existing_suspects:
            existing_users = User.objects.filter(id__in=existing_suspects)
            usernames = [u.username for u in existing_users]
            raise serializers.ValidationError(
                f"These users are already suspects in this case: {', '.join(usernames)}"
            )

        return data


class RejectFeedbackSerializer(serializers.Serializer):
    """Serializer for sergeants to provide rejection feedback."""
    feedback = serializers.CharField(required=True, min_length=5)

    def validate_feedback(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Feedback must be at least 5 characters long")
        return value
