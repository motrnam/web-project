#backend/rewards/views.py
from django.utils import timezone
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied

from users.permissions import IsBaseUser, IsPoliceOfficer, IsDetective, IsPoliceNotCadet
from .models import RewardTip, RewardTipStatus
from .serializers import (
    RewardTipCreateSerializer, RewardTipListSerializer,
    OfficerReviewSerializer, DetectiveConfirmSerializer
)


class RewardTipViewSet(viewsets.ModelViewSet):
    queryset = RewardTip.objects.select_related(
        'tip_submitter', 'reviewed_by_officer', 'reviewed_by_detective',
        'related_case', 'related_suspect'
    ).prefetch_related('related_case__suspects').all()

    def get_serializer_class(self):
        if self.action == 'create':
            return RewardTipCreateSerializer
        if self.action in ['officer_review', 'detective_confirm']:
            return OfficerReviewSerializer if self.action == 'officer_review' else DetectiveConfirmSerializer
        return RewardTipListSerializer

    def get_permissions(self):
        if self.action in ['create', 'my_tips']:
            return [permissions.IsAuthenticated(), IsBaseUser()]
        if self.action == 'officer_review':
            return [permissions.IsAuthenticated(), IsPoliceOfficer()]
        if self.action == 'detective_confirm':
            return [permissions.IsAuthenticated(), IsDetective()]
        if self.action in ['lookup_by_code', 'pending_for_officer', 'pending_for_detective']:
            return [permissions.IsAuthenticated(), IsPoliceNotCadet()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        user = self.request.user

        if self.action == 'my_tips':
            return qs.filter(tip_submitter=user)

        if self.action == 'pending_for_officer':
            return qs.filter(status=RewardTipStatus.PENDING_REVIEW)

        if self.action == 'pending_for_detective':
            # فقط مواردی که کاربر کارآگاه مسئول آن پرونده/مظنون است
            # Check through Detection relationship
            from detection.models import Detection
            from django.db.models import Q
            
            detective_cases = Detection.objects.filter(detective=user).values_list('case_id', flat=True)
            
            return qs.filter(
                status=RewardTipStatus.SENT_TO_DETECTIVE
            ).filter(
                Q(related_case_id__in=detective_cases) | 
                Q(related_suspect__case_id__in=detective_cases)
            )

        return qs

    def perform_create(self, serializer):
        serializer.save(tip_submitter=self.request.user)

    @action(detail=True, methods=['post'], url_path='officer-review')
    def officer_review(self, request, pk=None):
        tip = self.get_object()

        if tip.status != RewardTipStatus.PENDING_REVIEW:
            raise ValidationError("این اطلاعات دیگر قابل بررسی اولیه نیست.")

        if not tip.reviewed_by_officer.can_be_reviewed_by(request.user):  # اگر متد را در مدل دارید
            raise PermissionDenied("شما اجازه بررسی این اطلاعات را ندارید.")

        serializer = OfficerReviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        action = serializer.validated_data['action']
        note = serializer.validated_data.get('note', '')

        tip.reviewed_by_officer = request.user
        tip.officer_review_at = timezone.now()
        tip.officer_note = note

        if action == 'reject':
            tip.status = RewardTipStatus.REJECTED
        else:
            tip.status = RewardTipStatus.SENT_TO_DETECTIVE

        tip.save()
        return Response(RewardTipListSerializer(tip).data)

    @action(detail=True, methods=['post'], url_path='detective-confirm')
    def detective_confirm(self, request, pk=None):
        tip = self.get_object()

        if tip.status != RewardTipStatus.SENT_TO_DETECTIVE:
            raise ValidationError("این اطلاعات در مرحله تأیید کارآگاه نیست.")

        serializer = DetectiveConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Check if user is the detective for this case
        is_detective_for_case = False
        if tip.related_case:
            # Check through Detection relationship
            if hasattr(tip.related_case, 'detection') and tip.related_case.detection:
                is_detective_for_case = tip.related_case.detection.detective == request.user
        
        if tip.related_suspect and tip.related_suspect.case:
            if hasattr(tip.related_suspect.case, 'detection') and tip.related_suspect.case.detection:
                is_detective_for_case = tip.related_suspect.case.detection.detective == request.user
        
        if not is_detective_for_case:
            raise PermissionDenied("شما کارآگاه مسئول این پرونده نیستید.")

        if serializer.validated_data['confirmed']:
            tip.status = RewardTipStatus.ACCEPTED
            tip.reviewed_by_detective = request.user
            tip.detective_review_at = timezone.now()
            tip.detective_note = serializer.validated_data.get('note', '')
            tip.reward_amount = serializer.validated_data['reward_amount']
            tip.generate_reward_code()
            tip.notified_at = timezone.now()  # نشانه اطلاع‌رسانی
        else:
            tip.status = RewardTipStatus.REJECTED
            tip.detective_note += f"\nکارآگاه رد کرد: {serializer.validated_data.get('note', '')}"

        tip.save()
        return Response(RewardTipListSerializer(tip).data)

    @action(detail=False, methods=['get'], url_path='my-tips')
    def my_tips(self, request):
        """لیست تمام tipهای ثبت‌شده توسط کاربر فعلی"""
        return Response(RewardTipListSerializer(self.get_queryset(), many=True).data)

    @action(detail=False, methods=['get'], url_path='pending-for-officer')
    def pending_for_officer(self, request):
        """لیست tipهای در انتظار بررسی افسر"""
        return Response(RewardTipListSerializer(self.get_queryset(), many=True).data)

    @action(detail=False, methods=['get'], url_path='pending-for-detective')
    def pending_for_detective(self, request):
        """لیست tipهای منتظر تأیید کارآگاه مسئول"""
        return Response(RewardTipListSerializer(self.get_queryset(), many=True).data)

    @action(detail=False, methods=['get'], url_path='lookup')
    def lookup_by_code(self, request):
        national_id = request.query_params.get('national_id')
        reward_code = request.query_params.get('reward_code')

        if not national_id or not reward_code:
            raise ValidationError("national_id و reward_code هر دو الزامی هستند.")

        try:
            tip = RewardTip.objects.get(
                reward_code=reward_code,
                tip_submitter__national_id=national_id,
                status=RewardTipStatus.ACCEPTED
            )
            return Response(RewardTipListSerializer(tip).data)
        except RewardTip.DoesNotExist:
            raise ValidationError("اطلاعات معتبر یافت نشد.")