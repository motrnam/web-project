#evidences/models.py

from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.contrib.auth import get_user_model
import uuid
from case.models import Case

User = get_user_model()


class EvidenceCategory(models.TextChoices):
    WITNESS_STATEMENT = "WITNESS", "استشهاد / اظهارات شاهدان"
    BIOLOGICAL = "BIOLOGICAL", "شواهد زیستی و پزشکی"
    VEHICLE = "VEHICLE", "وسیله نقلیه"
    ID_DOCUMENT = "ID_DOCUMENT", "مدارک شناسایی"
    OTHER = "OTHER", "سایر شواهد"


class Evidence(models.Model):
    """
    مدل پایه همه انواع شواهد
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    case = models.ForeignKey(
        Case,
        on_delete=models.CASCADE,
        related_name="evidences",
        verbose_name="پرونده مرتبط",
    )

    category = models.CharField(
        max_length=32, choices=EvidenceCategory.choices, verbose_name="دسته شواهد"
    )

    title = models.CharField(max_length=255, verbose_name="عنوان شواهد")

    description = models.TextField(verbose_name="توضیحات / شرح")

    registered_by = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        related_name="registered_evidences",
        verbose_name="ثبت‌کننده",
    )

    registered_at = models.DateTimeField(
        default=timezone.now, editable=False, verbose_name="تاریخ ثبت"
    )

    updated_at = models.DateTimeField(auto_now=True, verbose_name="آخرین به‌روزرسانی")

    class Meta:
        verbose_name = "شاهد / مدرک"
        verbose_name_plural = "شواهد و مدارک"
        ordering = ["-registered_at"]

    def __str__(self):
        return f"{self.title} ({self.category}) – {self.case}"

    def clean(self):
        if not self.case_id:
            raise ValidationError("شواهد باید حتماً به یک پرونده وصل شود.")


# ────────────────────────────────────────────────
#          1. استشهاد شاهدان / افراد محلی
# ────────────────────────────────────────────────


class WitnessStatement(Evidence):
    """
    استشهاد شاهدان – می‌تواند ضمیمه رسانه (عکس/فیلم/صوت) داشته باشد
    """

    witness_name = models.CharField(
        max_length=150, verbose_name="نام شاهد / فرد اظهارکننده"
    )
    witness_national_id = models.CharField(
        max_length=10, blank=True, verbose_name="کد ملی شاهد (اختیاری)"
    )
    witness_phone = models.CharField(
        max_length=11, blank=True, verbose_name="شماره تماس شاهد (اختیاری)"
    )
    statement_datetime = models.DateTimeField(
        null=True, blank=True, verbose_name="زمان اخذ اظهارات"
    )

    class Meta:
        verbose_name = "استشهاد شاهد"
        verbose_name_plural = "استشهادات شاهدان"

    def allowed_media_types(self):
        return ["PHOTO", "VIDEO", "AUDIO"]


# ────────────────────────────────────────────────
#          2. شواهد زیستی / پزشکی
# ────────────────────────────────────────────────


class BiologicalEvidence(Evidence):
    """
    شواهد زیستی – نیاز به بررسی Coroner / بانک داده
    """

    collected_at = models.DateTimeField(verbose_name="زمان جمع‌آوری نمونه")
    collection_location = models.CharField(
        max_length=300, verbose_name="محل دقیق جمع‌آوری"
    )

    # نتایج بررسی (بعداً پر می‌شود)
    coroner_result = models.TextField(
        blank=True, verbose_name="نتیجه بررسی پزشکی قانونی"
    )
    coroner_verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name="تاریخ تأیید پزشکی قانونی"
    )
    db_match_result = models.TextField(
        blank=True, verbose_name="نتیجه تطبیق با بانک داده هویتی"
    )
    db_match_verified_at = models.DateTimeField(
        null=True, blank=True, verbose_name="تاریخ تطبیق بانک داده"
    )

    coroner = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,
        null=True,
        blank=True,
        related_name="verified_biological_evidences",
        verbose_name="پزشک قانونی تأییدکننده",
    )

    class Meta:
        verbose_name = "شاهد زیستی/پزشکی"
        verbose_name_plural = "شواهد زیستی و پزشکی"

    def allowed_media_types(self):
        return ["PHOTO"]  # معمولاً فقط تصویر


# ────────────────────────────────────────────────
#          3. وسیله نقلیه
# ────────────────────────────────────────────────


class VehicleEvidence(Evidence):
    """
    مدرک وسیله نقلیه – یا پلاک یا سریال (انحصاری)
    """

    vehicle_model = models.CharField(max_length=100, verbose_name="مدل خودرو")
    color = models.CharField(max_length=50, verbose_name="رنگ")
    license_plate = models.CharField(
        max_length=20, blank=True, verbose_name="شماره پلاک"
    )
    serial_number = models.CharField(
        max_length=50, blank=True, verbose_name="شماره شاسی / VIN / سریال"
    )

    def clean(self):
        has_plate = bool(self.license_plate.strip())
        has_serial = bool(self.serial_number.strip())

        if has_plate and has_serial:
            raise ValidationError(
                "شماره پلاک و شماره سریال نمی‌توانند همزمان مقدار داشته باشند."
            )
        if not has_plate and not has_serial:
            raise ValidationError(
                "حداقل یکی از فیلدهای پلاک یا شماره سریال باید پر شود."
            )

    class Meta:
        verbose_name = "مدرک وسیله نقلیه"
        verbose_name_plural = "مدارک وسایل نقلیه"

    def allowed_media_types(self):
        return ["PHOTO"]


# ────────────────────────────────────────────────
#          4. مدارک شناسایی
# ────────────────────────────────────────────────


class IdentityDocumentEvidence(Evidence):
    """
    مدرک شناسایی پیدا شده – اطلاعات کلید-مقدار دلخواه
    """

    presumed_owner_name = models.CharField(
        max_length=150, blank=True, verbose_name="نام احتمالی صاحب مدرک"
    )

    class Meta:
        verbose_name = "مدرک شناسایی"
        verbose_name_plural = "مدارک شناسایی پیدا شده"


class IdentityDocumentField(models.Model):
    """
    فیلدهای کلید-مقدار برای مدرک شناسایی (انعطاف‌پذیر)
    """

    document = models.ForeignKey(
        IdentityDocumentEvidence, on_delete=models.CASCADE, related_name="fields"
    )
    key = models.CharField(
        max_length=100, verbose_name="عنوان فیلد (مثلاً شماره کارت، تاریخ صدور)"
    )
    value = models.CharField(max_length=255, verbose_name="مقدار")
    order = models.PositiveSmallIntegerField(default=0, verbose_name="ترتیب نمایش")

    class Meta:
        ordering = ["order", "key"]
        unique_together = [["document", "key"]]


# ────────────────────────────────────────────────
#          5. سایر شواهد (ساده)
# ────────────────────────────────────────────────


class OtherEvidence(Evidence):
    """
    سایر موارد – فقط عنوان + توضیح
    """

    # می‌تواند subtype یا tag داشته باشد اگر بعداً نیاز شد
    class Meta:
        verbose_name = "سایر شواهد"
        verbose_name_plural = "سایر شواهد"

    def allowed_media_types(self):
        return ["PHOTO", "VIDEO", "AUDIO", "DOCUMENT"]


# ────────────────────────────────────────────────
#          رسانه‌های ضمیمه (مشترک)
# ────────────────────────────────────────────────


class EvidenceMedia(models.Model):
    MEDIA_TYPE_CHOICES = [
        ("PHOTO", "تصویر"),
        ("VIDEO", "ویدئو"),
        ("AUDIO", "صوت"),
        ("DOCUMENT", "سند / PDF"),
    ]

    evidence = models.ForeignKey(
        Evidence, on_delete=models.CASCADE, related_name="media"
    )
    file = models.FileField(upload_to="evidence_media/%Y/%m/%d/", verbose_name="فایل")
    media_type = models.CharField(
        max_length=20, choices=MEDIA_TYPE_CHOICES, verbose_name="نوع رسانه"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="زمان آپلود")
    uploaded_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, verbose_name="آپلودکننده"
    )
    description = models.CharField(
        max_length=255, blank=True, verbose_name="توضیح کوتاه فایل"
    )

    def clean(self):
        # اعتبارسنجی نوع رسانه بر اساس دسته شواهد
        allowed = self.evidence.allowed_media_types()
        if self.media_type not in allowed:
            raise ValidationError(
                f"نوع رسانه {self.media_type} برای این دسته شواهد مجاز نیست. "
                f"مجاز: {', '.join(allowed)}"
            )

    class Meta:
        verbose_name = "فایل شواهد"
        verbose_name_plural = "فایل‌های شواهد"
