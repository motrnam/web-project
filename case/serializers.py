#case/serializers.py
from rest_framework import serializers
from django.utils import timezone
from .models import (
    RegisterComplain,
    Complainant,
    ComplainReview,
    CrimeSceneReport,
    CrimeSceneWitness,
    Case,
    ComplainStatus,
    CrimeSceneReportStatus,
    ComplainantStatus,
)


class ComplainantSerializer(serializers.ModelSerializer):
    user_full_name = serializers.CharField(source='user.full_name', read_only=True)
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = Complainant
        fields = [
            'id',
            'user',
            'user_full_name',
            'username',
            'relationship_to_incident',
            'status',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at', 'user_full_name', 'username']


class RegisterComplainSerializer(serializers.ModelSerializer):
    creator_full_name = serializers.CharField(source='creator.full_name', read_only=True)
    complainants = ComplainantSerializer(many=True, read_only=True)
    complainants_count = serializers.SerializerMethodField()
    last_review = serializers.SerializerMethodField()
    last_review_message = serializers.CharField(source='last_review.message', read_only=True)
    remaining_revisions = serializers.SerializerMethodField()

    class Meta:
        model = RegisterComplain
        fields = [
            'id',
            'creator',
            'creator_full_name',
            'title',
            'description',
            'incident_datetime',
            'incident_location',
            'crime_type',
            'status',
            'revision_count',
            'remaining_revisions',
            'max_revisions',
            'last_review',
            'last_review_message',
            'complainants',
            'complainants_count',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'creator', 'status', 'revision_count', 'created_at', 'updated_at',
            'remaining_revisions', 'last_review', 'last_review_message', 'complainants_count'
        ]

    def get_complainants_count(self, obj):
        return obj.complainants.count() + 1  # +1 برای creator

    def get_remaining_revisions(self, obj):
        return max(0, obj.max_revisions - obj.revision_count)

    def get_last_review(self, obj):
        last = obj.reviews.order_by('-reviewed_at').first()
        if last:
            return ComplainReviewSerializer(last).data
        return None


class ComplainReviewSerializer(serializers.ModelSerializer):
    reviewed_by_full_name = serializers.CharField(source='reviewed_by.full_name', read_only=True)
    reviewed_by_username = serializers.CharField(source='reviewed_by.username', read_only=True)

    class Meta:
        model = ComplainReview
        fields = [
            'id',
            'complain',
            'reviewed_by',
            'reviewed_by_full_name',
            'reviewed_by_username',
            'message',
            'is_approval',
            'to_status',
            'reviewed_at',
        ]
        read_only_fields = ['id', 'reviewed_by', 'reviewed_by_full_name', 'reviewed_by_username', 'reviewed_at']


class CrimeSceneWitnessSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrimeSceneWitness
        fields = [
            'id',
            'report',
            'national_id',
            'phone_number',
            'full_name',
            'statement_summary',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class CrimeSceneReportSerializer(serializers.ModelSerializer):
    reporter_full_name = serializers.CharField(source='reporter.full_name', read_only=True)
    witnesses = CrimeSceneWitnessSerializer(many=True, read_only=True)
    witnesses_count = serializers.SerializerMethodField()

    class Meta:
        model = CrimeSceneReport
        fields = [
            'id',
            'reporter',
            'reporter_full_name',
            'occurred_at',
            'reported_at',
            'location',
            'description',
            'crime_type',
            'status',
            'supervisor',
            'approved_at',
            'case',
            'witnesses',
            'witnesses_count',
        ]
        read_only_fields = [
            'id', 'reporter', 'reported_at', 'approved_at', 'case', 'witnesses', 'witnesses_count',
        ]

    def get_witnesses_count(self, obj):
        return obj.witnesses.count()


class CaseSerializer(serializers.ModelSerializer):
    complain = RegisterComplainSerializer(read_only=True)
    crime_scene_report = CrimeSceneReportSerializer(read_only=True)
    created_by_full_name = serializers.CharField(source='created_by.full_name', read_only=True)
    complainants = ComplainantSerializer(many=True, read_only=True)  # ← اضافه شد

    class Meta:
        model = Case
        fields = [
            'id',
            'complain',
            'crime_scene_report',
            'created_at',
            'created_by',
            'created_by_full_name',
            'crime_type',
            'case_number',
            'status',
            'complainants',
        ]
        read_only_fields = [
            'id', 'created_at', 'case_number', 'created_by_full_name', 'complainants'
        ]

class EmptySerializer(serializers.Serializer):
    pass