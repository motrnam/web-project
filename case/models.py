# case/models.py
from django.db import models
from django.contrib.auth import get_user_model
import uuid
from django.utils import timezone

User = get_user_model()


class CrimeType(models.TextChoices):
    TYPE_3 = "TYPE_3", "سطح ۳ - جرائم خرد"
    TYPE_2 = "TYPE_2", "سطح ۲ - جرائم متوسط"
    TYPE_1 = "TYPE_1", "سطح ۱ - جرائم سنگین"
    CRITICAL = "CRITICAL", "بحرانی"


class ComplainStatus(models.TextChoices):
    DRAFT = "DRAFT", "پیش‌نویس (فقط شاکی)"
    PENDING_CADET = "PENDING_CADET", "در انتظار بررسی کارآموز"
    RETURNED_TO_COMPLAINANT = "RETURNED_TO_COMPLAINANT", "بازگشت به شاکی برای اصلاح"
    PENDING_OFFICER = "PENDING_OFFICER", "در انتظار تأیید افسر پلیس"
    APPROVED = "APPROVED", "پرونده تشکیل شد"
    REJECTED = "REJECTED", "رد نهایی"
    CANCELLED = "CANCELLED", "باطل شده (بیش از حد ویرایش)"


class CrimeSceneReportStatus(models.TextChoices):
    DRAFT = "DRAFT", "پیش‌نویس مأمور"
    PENDING_SUPERVISOR = "PENDING_SUPERVISOR", "در انتظار تأیید مافوق"
    APPROVED = "APPROVED", "تأیید و تشکیل پرونده"
    REJECTED = "REJECTED", "رد شده"


class ComplainantStatus(models.TextChoices):
    PENDING = "PENDING", "در انتظار تأیید"
    APPROVED = "APPROVED", "تأیید شده"
    REJECTED = "REJECTED", "رد شده"


# ────────────────────────────────────────────────
#               شکایت اولیه (از شاکی)
# ────────────────────────────────────────────────
class RegisterComplain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="created_complaints",
        verbose_name="شاکی اصلی",
    )
    title = models.CharField(max_length=255, verbose_name="عنوان شکایت")
    description = models.TextField(verbose_name="شرح کامل شکایت")
    incident_datetime = models.DateTimeField(verbose_name="زمان تقریبی وقوع")
    incident_location = models.CharField(
        max_length=300, blank=True, verbose_name="محل وقوع"
    )
    crime_type = models.CharField(
        max_length=20,
        choices=CrimeType.choices,
        default=CrimeType.TYPE_1,
        verbose_name="نوع جرم",
    )  # ← اضافه شد
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    status = models.CharField(
        max_length=32,
        choices=ComplainStatus.choices,
        default=ComplainStatus.DRAFT,
        verbose_name="وضعیت شکایت",
    )
    revision_count = models.PositiveSmallIntegerField(
        default=0,
        verbose_name="تعداد دفعات بازگشت به شاکی",
    )
    max_revisions = models.PositiveSmallIntegerField(default=3, editable=False)

    class Meta:
        verbose_name = "شکایت اولیه"
        verbose_name_plural = "شکایات اولیه"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} – {self.creator}"

    def can_be_edited_by_complainant(self):
        return self.status in (
            ComplainStatus.DRAFT,
            ComplainStatus.RETURNED_TO_COMPLAINANT,
        )

    def can_submit(self):
        return (
                self.status
                in (
                    ComplainStatus.DRAFT,
                    ComplainStatus.RETURNED_TO_COMPLAINANT,
                )
                and self.revision_count < self.max_revisions
        )


class Complainant(models.Model):
    """شاکیان اضافی (علاوه بر شاکی اصلی)"""

    complain = models.ForeignKey(
        RegisterComplain,
        on_delete=models.CASCADE,
        related_name="complainants",
        null=True,
        blank=True,  # برای مسیر شکایت
    )
    case = models.ForeignKey(
        "Case",
        on_delete=models.CASCADE,
        related_name="complainants",
        null=True,
        blank=True,  # برای مسیر صحنه جرم
    )
    user = models.ForeignKey(User, on_delete=models.RESTRICT)
    relationship_to_incident = models.CharField(
        max_length=120,
        blank=True,
        verbose_name="رابطه با حادثه (اختیاری)",
    )
    status = models.CharField(
        max_length=20,
        choices=ComplainantStatus.choices,
        default=ComplainantStatus.PENDING,
        verbose_name="وضعیت شاکی",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("complain", "user"), ("case", "user")]
        verbose_name = "شاکی پرونده"
        verbose_name_plural = "شاکیان پرونده"

    def __str__(self):
        return f"{self.user} در {self.complain or self.case}"


class ComplainReview(models.Model):
    """هر بررسی توسط کارآموز یا افسر پلیس"""

    complain = models.ForeignKey(
        RegisterComplain, on_delete=models.CASCADE, related_name="reviews"
    )
    reviewed_by = models.ForeignKey(User, on_delete=models.RESTRICT)
    reviewed_at = models.DateTimeField(auto_now_add=True)
    message = models.TextField(blank=True, verbose_name="پیام / دلیل بازگشت یا رد")
    is_approval = models.BooleanField(
        default=False, verbose_name="تأیید نهایی این مرحله؟"
    )
    to_status = models.CharField(max_length=32, choices=ComplainStatus.choices)

    class Meta:
        ordering = ["-reviewed_at"]
        verbose_name = "بررسی شکایت"
        verbose_name_plural = "بررسی‌های شکایت"


# ────────────────────────────────────────────────
#           ثبت صحنه جرم (توسط پلیس)
# ────────────────────────────────────────────────
class CrimeSceneReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    reporter = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="reported_crime_scenes",
        verbose_name="گزارش‌دهنده (مأمور)",
    )
    occurred_at = models.DateTimeField(verbose_name="زمان وقوع جرم")
    reported_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان گزارش")
    location = models.CharField(max_length=300, verbose_name="محل دقیق یا تقریبی")
    description = models.TextField(verbose_name="شرح صحنه جرم")
    crime_type = models.CharField(
        max_length=20,
        choices=CrimeType.choices,
        verbose_name="نوع جرم",
        default=CrimeType.TYPE_1,
    )

    status = models.CharField(
        max_length=32,
        choices=CrimeSceneReportStatus.choices,
        default=CrimeSceneReportStatus.DRAFT,
        verbose_name="وضعیت گزارش",
    )
    supervisor = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="approved_crime_scenes",
        verbose_name="تأییدکننده",
    )
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "گزارش صحنه جرم"
        verbose_name_plural = "گزارش‌های صحنه جرم"
        ordering = ["-reported_at"]

    def __str__(self):
        return f"صحنه جرم {self.location} – {self.reporter}"


class CrimeSceneWitness(models.Model):
    """شاهدان گزارش‌شده در صحنه جرم"""

    report = models.ForeignKey(
        CrimeSceneReport, on_delete=models.CASCADE, related_name="witnesses"
    )
    national_id = models.CharField(max_length=10, verbose_name="کد ملی شاهد")
    phone_number = models.CharField(max_length=11, verbose_name="شماره تماس")
    full_name = models.CharField(max_length=150, verbose_name="نام و نام خانوادگی")
    statement_summary = models.TextField(blank=True, verbose_name="خلاصه اظهارات")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "شاهد صحنه جرم"
        verbose_name_plural = "شاهدان صحنه جرم"


# ────────────────────────────────────────────────
#                     پرونده نهایی
# ────────────────────────────────────────────────
class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # یکی از دو مسیر باید پر باشد
    complain = models.ForeignKey(
        RegisterComplain,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case",
    )
    crime_scene_report = models.OneToOneField(
        CrimeSceneReport,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="case",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        User, on_delete=models.RESTRICT, related_name="created_cases"
    )
    crime_type = models.CharField(
        max_length=20, choices=CrimeType.choices, verbose_name="نوع جرم", default=CrimeType.TYPE_1
    )
    case_number = models.CharField(max_length=32, unique=True, blank=True)

    status = models.CharField(max_length=64, default="OPEN")

    class Meta:
        verbose_name = "پرونده"
        verbose_name_plural = "پرونده‌ها"
        ordering = ["-created_at"]

    def __str__(self):
        return f"پرونده {self.case_number or self.id}"

    def save(self, *args, **kwargs):
        # First, save the object to let Django set created_at
        super().save(*args, **kwargs)

        # Now generate case_number if needed
        if not self.case_number and self.created_at:
            year = self.created_at.year
            count = Case.objects.filter(created_at__year=year).count()
            self.case_number = f"{year}/{count:04d}"
            super().save(update_fields=['case_number'])
