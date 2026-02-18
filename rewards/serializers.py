#rewards/serializers.py
from rest_framework import serializers
from .models import RewardTip


class RewardTipCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = RewardTip
        fields = ['related_case', 'related_suspect', 'title', 'description']
        read_only_fields = ['tip_submitter']

    def validate(self, data):
        if not (data.get('related_case') or data.get('related_suspect')):
            raise serializers.ValidationError("حداقل یک پرونده یا مظنون باید مشخص شود.")
        return data


class RewardTipListSerializer(serializers.ModelSerializer):
    submitter_name    = serializers.CharField(source='tip_submitter.full_name', read_only=True)
    officer_name      = serializers.CharField(source='reviewed_by_officer.full_name', read_only=True, allow_null=True)
    detective_name    = serializers.CharField(source='reviewed_by_detective.full_name', read_only=True, allow_null=True)
    case_title        = serializers.CharField(source='related_case.title', read_only=True, allow_null=True)
    suspect_name      = serializers.CharField(source='related_suspect.person.full_name', read_only=True, allow_null=True)

    class Meta:
        model = RewardTip
        fields = [
            'id', 'title', 'description', 'status', 'submitted_at',
            'submitter_name', 'officer_name', 'detective_name',
            'case_title', 'suspect_name',
            'reward_code', 'reward_amount', 'notified_at'
        ]


class OfficerReviewSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=['approve', 'reject'])
    note   = serializers.CharField(required=False, allow_blank=True)


class DetectiveConfirmSerializer(serializers.Serializer):
    confirmed     = serializers.BooleanField()
    note          = serializers.CharField(required=False, allow_blank=True)
    reward_amount = serializers.IntegerField(min_value=100_000, required=True)  # حداقل منطقی مثلاً