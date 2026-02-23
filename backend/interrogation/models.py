#backend/interrogation/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

from case.models import Case
from django.core.validators import MaxValueValidator, MinValueValidator
import uuid
from django.core.exceptions import ValidationError


# Create your models here.
User = get_user_model()


class VerdictStatus(models.TextChoices):
    GUILTY = "GUILTY", "guilty"
    NOT_GUILTY = "NOT_GUILTY", "not guilty"


class PoliceChiefApproval(models.TextChoices):
    APPROVED = "APPROVED", "approved"
    NOT_APPROVED = "NOT_APPROVED", "not approved"

class InterrogationStatus(models.TextChoices):
    PENDING_SCORES      = "PENDING_SCORES",      "در انتظار ثبت امتیازها"
    SCORES_COMPLETED    = "SCORES_COMPLETED",    "امتیازها ثبت شده"
    PENDING_CAPTAIN     = "PENDING_CAPTAIN",     "در انتظار تصمیم کاپیتان"
    CAPTAIN_DECIDED     = "CAPTAIN_DECIDED",     "کاپیتان تصمیم گرفت"
    PENDING_CHIEF       = "PENDING_CHIEF",       "در انتظار تأیید رئیس پلیس"
    COMPLETED           = "COMPLETED",           "کامل شده"
    CANCELLED           = "CANCELLED",           "لغو شده"

class SuspectStatus(models.TextChoices):
    CAPTURED = "CAPTURED", "captured"
    WANTED = "WANTED", "wanted"
    MOST_WANTED = "MOST_WANTED", "most wanted"


class Suspect(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(User, on_delete=models.RESTRICT, related_name="suspects_as_person")
    case = models.ForeignKey(Case, on_delete=models.RESTRICT, related_name="suspects")
    detail = models.CharField(max_length=500, blank=True)
    suspect_status = models.CharField(
        max_length=20,
        choices=SuspectStatus.choices,
        default=SuspectStatus.WANTED
    )
    added_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="added_suspects")
    added_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = [['person', 'case']]
        ordering = ['-added_at']

    def __str__(self):
        return f"{self.person} در پرونده {self.case}"


class Interrogation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    suspect = models.ForeignKey(Suspect, on_delete=models.CASCADE, related_name="interrogations")
    interrogator_sergeant = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="interrogations_as_sergeant"
    )
    interrogator_detective = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="interrogations_as_detective"
    )

    sergeant_score = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="امتیاز احتمال گناهکاری گروهبان"
    )
    detective_score = models.PositiveSmallIntegerField(
        null=True, blank=True,
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        verbose_name="امتیاز احتمال گناهکاری کارآگاه"
    )

    capitan_comment = models.TextField(blank=True, verbose_name="نظر / توضیحات کاپیتان")
    capitan_verdict = models.CharField(
        max_length=20, choices=VerdictStatus.choices, null=True, blank=True
    )
    captain_decided_at = models.DateTimeField(null=True, blank=True)

    chief_approved = models.CharField(
        max_length=20, choices=PoliceChiefApproval.choices, null=True, blank=True,
        verbose_name="نظر نهایی رئیس پلیس"
    )
    chief_approved_at = models.DateTimeField(null=True, blank=True)

    status = models.CharField(
        max_length=30,
        choices=InterrogationStatus.choices,
        default=InterrogationStatus.PENDING_SCORES,
        verbose_name="وضعیت فرآیند بازجویی"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"بازجویی {self.suspect} – {self.status}"

    def clean(self):
        if self.interrogator_sergeant == self.interrogator_detective:
            raise ValidationError("گروهبان و کارآگاه نمی‌توانند یک نفر باشند")

        if not self.interrogator_sergeant.groups.filter(name="Sergeant").exists():
            raise ValidationError("interrogator_sergeant باید عضو گروه Sergeant باشد")

        if not self.interrogator_detective.groups.filter(name="Detective").exists():
            raise ValidationError("interrogator_detective باید عضو گروه Detective باشد")

    def requires_chief_approval(self):
        # فرض می‌کنیم crime_type از Case قابل دسترسی است
        return self.suspect.case.crime_type == "CRITICAL"

    def update_status_after_scores(self):
        if self.sergeant_score is not None and self.detective_score is not None:
            self.status = InterrogationStatus.SCORES_COMPLETED
            self.save(update_fields=['status'])
        
    

class Court(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judge = models.ForeignKey(User, on_delete=models.RESTRICT, related_name='court_cases')
    interrogation = models.OneToOneField(Interrogation, on_delete=models.RESTRICT, related_name='court')
    created_at = models.DateTimeField(auto_now_add=True)
    hearing_date = models.DateField(null=True, blank=True, verbose_name="تاریخ دادگاه")
    
    final_verdict = models.CharField(
        max_length=20, 
        choices=VerdictStatus.choices, 
        null=True, 
        blank=True,
        verbose_name="حکم نهایی"
    )
    punishment_title = models.CharField(
        max_length=255,
        blank=True,
        verbose_name="عنوان مجازات"
    )
    punishment_description = models.TextField(
        blank=True,
        verbose_name="توضیحات مجازات"
    )
    verdict_date = models.DateTimeField(null=True, blank=True, verbose_name="تاریخ صدور حکم")
    
    class Meta:
        verbose_name = "دادگاه"
        verbose_name_plural = "دادگاه‌ها"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"دادگاه {self.interrogation.suspect.person.username} - قاضی {self.judge.username}"
