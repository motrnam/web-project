#rewards/models.py
from django.db import models
from django.utils import timezone
import uuid
from django.contrib.auth import get_user_model
from case.models import Case
from interrogation.models import Suspect

User = get_user_model()


class RewardTipStatus(models.TextChoices):
    PENDING_REVIEW     = "PENDING_REVIEW",     "در انتظار بررسی اولیه افسر"
    REJECTED           = "REJECTED",           "رد شده (بی‌اعتبار)"
    SENT_TO_DETECTIVE  = "SENT_TO_DETECTIVE",  "ارسال به کارآگاه"
    ACCEPTED           = "ACCEPTED",           "تأیید شده توسط کارآگاه"
    CANCELLED          = "CANCELLED",          "لغو شده"


class RewardTip(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    tip_submitter = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True,
        related_name="submitted_tips", verbose_name="ثبت‌کننده اطلاعات"
    )

    related_case   = models.ForeignKey(Case,   on_delete=models.SET_NULL, null=True, blank=True)
    related_suspect = models.ForeignKey(Suspect, on_delete=models.SET_NULL, null=True, blank=True)

    title          = models.CharField(max_length=255, verbose_name="عنوان اطلاعات")
    description    = models.TextField(verbose_name="جزئیات اطلاعات ارائه شده")
    submitted_at   = models.DateTimeField(default=timezone.now)

    status         = models.CharField(
        max_length=30, choices=RewardTipStatus.choices,
        default=RewardTipStatus.PENDING_REVIEW
    )

    reviewed_by_officer = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="reviewed_tips", verbose_name="افسر بررسی‌کننده"
    )
    officer_review_at   = models.DateTimeField(null=True, blank=True)
    officer_note        = models.TextField(blank=True, verbose_name="یادداشت افسر")

    reviewed_by_detective = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="confirmed_tips", verbose_name="کارآگاه تأییدکننده"
    )
    detective_review_at   = models.DateTimeField(null=True, blank=True)
    detective_note        = models.TextField(blank=True, verbose_name="یادداشت کارآگاه")

    reward_code       = models.CharField(max_length=36, unique=True, null=True, blank=True)
    reward_amount     = models.PositiveIntegerField(null=True, blank=True, verbose_name="مبلغ پاداش (ریال)")

    notified_at       = models.DateTimeField(null=True, blank=True, verbose_name="زمان اطلاع‌رسانی به کاربر")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-submitted_at"]
        verbose_name = "اطلاعات ارسالی برای پاداش"
        verbose_name_plural = "اطلاعات ارسالی برای پاداش"

    def __str__(self):
        return f"{self.title} – {self.tip_submitter}"

    def generate_reward_code(self):
        if self.status == RewardTipStatus.ACCEPTED and not self.reward_code:
            self.reward_code = str(uuid.uuid4())
            self.save(update_fields=['reward_code'])

    def can_be_reviewed_by(self, user):
        """برای استفاده در permissionها"""
        if self.status == RewardTipStatus.PENDING_REVIEW:
            return user.groups.filter(name__in=['Police Officer', 'Patrol Officer']).exists()
        if self.status == RewardTipStatus.SENT_TO_DETECTIVE:
            # فقط کارآگاه مسئول پرونده/مظنون
            if self.related_case and hasattr(self.related_case, 'detective'):
                return user == getattr(self.related_case, 'detective', None)
            if self.related_suspect and self.related_suspect.case:
                return user == getattr(self.related_suspect.case, 'detective', None)
            return False
        return False