#evidences/serializers.py
from django.utils import timezone
from rest_framework import serializers

from case.models import Case
from .models import (
    Evidence,
    WitnessStatement,
    BiologicalEvidence,
    VehicleEvidence,
    IdentityDocumentEvidence,
    IdentityDocumentField,
    OtherEvidence,
    EvidenceMedia,
    EvidenceCategory,
)


# ────────────────────────────────────────────────
#          Media (مشترک برای همه شواهد)
# ────────────────────────────────────────────────


class EvidenceMediaSerializer(serializers.ModelSerializer):
    uploaded_by_username = serializers.CharField(
        source="uploaded_by.username", read_only=True, allow_null=True
    )

    class Meta:
        model = EvidenceMedia
        fields = [
            "id",
            "file",
            "media_type",
            "uploaded_at",
            "uploaded_by",
            "uploaded_by_username",
            "description",
        ]
        read_only_fields = ["id", "uploaded_at", "uploaded_by", "uploaded_by_username"]


# ────────────────────────────────────────────────
#          مدل پایه Evidence
# ────────────────────────────────────────────────


class EvidenceBaseSerializer(serializers.ModelSerializer):
    registered_by_username = serializers.CharField(
        source="registered_by.username", read_only=True
    )
    registered_by_full_name = serializers.CharField(
        source="registered_by.full_name", read_only=True, allow_null=True
    )
    media = EvidenceMediaSerializer(many=True, read_only=True)
    media_count = serializers.SerializerMethodField()

    class Meta:
        model = Evidence
        fields = [
            "id",
            "case",
            "category",
            "title",
            "description",
            "registered_by",
            "registered_by_username",
            "registered_by_full_name",
            "registered_at",
            "updated_at",
            "media",
            "media_count",
        ]
        read_only_fields = [
            "id",
            "registered_by",
            "registered_by_username",
            "registered_by_full_name",
            "registered_at",
            "updated_at",
            "media",
            "media_count",
        ]

    def get_media_count(self, obj):
        return obj.media.count()


# ────────────────────────────────────────────────
#          1. استشهاد شاهدان
# ────────────────────────────────────────────────


class WitnessStatementSerializer(EvidenceBaseSerializer):
    class Meta(EvidenceBaseSerializer.Meta):
        model = WitnessStatement
        fields = EvidenceBaseSerializer.Meta.fields + [
            "witness_name",
            "witness_national_id",
            "witness_phone",
            "statement_datetime",
        ]


# ────────────────────────────────────────────────
#          2. شواهد زیستی / پزشکی
# ────────────────────────────────────────────────


class BiologicalEvidenceSerializer(EvidenceBaseSerializer):
    coroner_username = serializers.CharField(
        source="coroner.username", read_only=True, allow_null=True
    )
    coroner_full_name = serializers.CharField(
        source="coroner.full_name", read_only=True, allow_null=True
    )

    class Meta(EvidenceBaseSerializer.Meta):
        model = BiologicalEvidence
        fields = EvidenceBaseSerializer.Meta.fields + [
            "collected_at",
            "collection_location",
            "coroner_result",
            "coroner_verified_at",
            "db_match_result",
            "db_match_verified_at",
            "coroner",
            "coroner_username",
            "coroner_full_name",
        ]


# ────────────────────────────────────────────────
#          3. وسیله نقلیه
# ────────────────────────────────────────────────


class VehicleEvidenceSerializer(EvidenceBaseSerializer):
    class Meta(EvidenceBaseSerializer.Meta):
        model = VehicleEvidence
        fields = EvidenceBaseSerializer.Meta.fields + [
            "vehicle_model",
            "color",
            "license_plate",
            "serial_number",
        ]

    def validate(self, data):
        has_plate = bool(data.get("license_plate", "").strip())
        has_serial = bool(data.get("serial_number", "").strip())

        if has_plate and has_serial:
            raise serializers.ValidationError(
                "شماره پلاک و شماره سریال نمی‌توانند همزمان مقدار داشته باشند."
            )
        if not has_plate and not has_serial:
            raise serializers.ValidationError(
                "حداقل یکی از فیلدهای پلاک یا شماره سریال باید پر شود."
            )
        return data


# ────────────────────────────────────────────────
#          4. مدارک شناسایی + فیلدهای کلید-مقدار
# ────────────────────────────────────────────────


class IdentityDocumentFieldSerializer(serializers.ModelSerializer):
    class Meta:
        model = IdentityDocumentField
        fields = ["id", "key", "value", "order"]
        read_only_fields = ["id"]


class IdentityDocumentEvidenceSerializer(EvidenceBaseSerializer):
    fields = IdentityDocumentFieldSerializer(many=True, read_only=True)
    fields_count = serializers.SerializerMethodField()

    class Meta(EvidenceBaseSerializer.Meta):
        model = IdentityDocumentEvidence
        fields = EvidenceBaseSerializer.Meta.fields + [
            "presumed_owner_name",
            "fields",
            "fields_count",
        ]

    def get_fields_count(self, obj):
        return obj.fields.count()


# ────────────────────────────────────────────────
#          5. سایر شواهد
# ────────────────────────────────────────────────


class OtherEvidenceSerializer(EvidenceBaseSerializer):
    class Meta(EvidenceBaseSerializer.Meta):
        model = OtherEvidence
        fields = EvidenceBaseSerializer.Meta.fields  # فقط پایه + رسانه


# ────────────────────────────────────────────────
#          Serializer Polymorphic (برای لیست و جزئیات)
# ────────────────────────────────────────────────


class EvidencePolymorphicSerializer(serializers.ModelSerializer):
    """
    Serializer اصلی برای لیست شواهد و جزئیات
    نوع واقعی را بر اساس category تشخیص می‌دهد
    """

    concrete_serializer_map = {
        EvidenceCategory.WITNESS_STATEMENT: WitnessStatementSerializer,
        EvidenceCategory.BIOLOGICAL: BiologicalEvidenceSerializer,
        EvidenceCategory.VEHICLE: VehicleEvidenceSerializer,
        EvidenceCategory.ID_DOCUMENT: IdentityDocumentEvidenceSerializer,
        EvidenceCategory.OTHER: OtherEvidenceSerializer,
    }

    serializer = serializers.SerializerMethodField()

    class Meta:
        model = Evidence
        fields = ["id", "category", "serializer"]

    def get_serializer(self, obj):
        serializer_class = self.concrete_serializer_map.get(obj.category)
        if not serializer_class:
            # fallback به پایه در صورت دسته ناشناخته
            return EvidenceBaseSerializer(obj, context=self.context).data

        return serializer_class(obj, context=self.context).data


# ────────────────────────────────────────────────
#          Serializer برای ایجاد شواهد جدید (ورودی)
# ────────────────────────────────────────────────


class EvidenceCreateSerializer(serializers.Serializer):
    category = serializers.ChoiceField(choices=EvidenceCategory.choices)
    case = serializers.UUIDField()
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)

    # فیلدهای خاص هر دسته
    witness_name = serializers.CharField(max_length=150, required=False)
    witness_national_id = serializers.CharField(
        max_length=10, required=False, allow_blank=True
    )
    witness_phone = serializers.CharField(
        max_length=11, required=False, allow_blank=True
    )
    statement_datetime = serializers.DateTimeField(required=False, allow_null=True)

    collected_at = serializers.DateTimeField(required=False)
    collection_location = serializers.CharField(
        max_length=300, required=False, allow_blank=True
    )

    vehicle_model = serializers.CharField(max_length=100, required=False)
    color = serializers.CharField(max_length=50, required=False)
    license_plate = serializers.CharField(
        max_length=20, required=False, allow_blank=True
    )
    serial_number = serializers.CharField(
        max_length=50, required=False, allow_blank=True
    )

    presumed_owner_name = serializers.CharField(
        max_length=150, required=False, allow_blank=True
    )

    # برای آپلود فایل‌ها در create (اختیاری)
    media_files = serializers.ListField(
        child=serializers.FileField(), required=False, write_only=True
    )

    def validate(self, data):
        category = data.get("category")

        if category == EvidenceCategory.WITNESS_STATEMENT:
            if not data.get("witness_name"):
                raise serializers.ValidationError(
                    {"witness_name": "نام شاهد الزامی است."}
                )

        elif category == EvidenceCategory.BIOLOGICAL:
            if not data.get("collected_at"):
                raise serializers.ValidationError(
                    {"collected_at": "زمان جمع‌آوری الزامی است."}
                )

        elif category == EvidenceCategory.VEHICLE:
            has_plate = bool(data.get("license_plate", "").strip())
            has_serial = bool(data.get("serial_number", "").strip())
            if has_plate and has_serial:
                raise serializers.ValidationError("پلاک و سریال همزمان مجاز نیستند.")
            if not has_plate and not has_serial:
                raise serializers.ValidationError("حداقل پلاک یا سریال باید وارد شود.")
            if not data.get("vehicle_model") or not data.get("color"):
                raise serializers.ValidationError("مدل و رنگ الزامی هستند.")

        return data

    def create(self, validated_data):
        category = validated_data.pop("category")
        case_id = validated_data.pop("case")
        media_files = validated_data.pop(
            "media_files", []
        )  # اینجا نمی‌آید، پس استفاده نمی‌کنیم

        case = Case.objects.get(id=case_id)

        evidence_class_map = {
            EvidenceCategory.WITNESS_STATEMENT: WitnessStatement,
            EvidenceCategory.BIOLOGICAL: BiologicalEvidence,
            EvidenceCategory.VEHICLE: VehicleEvidence,
            EvidenceCategory.ID_DOCUMENT: IdentityDocumentEvidence,
            EvidenceCategory.OTHER: OtherEvidence,
        }

        evidence_class = evidence_class_map.get(category)
        if not evidence_class:
            raise serializers.ValidationError("دسته‌بندی نامعتبر")

        evidence = evidence_class.objects.create(
            case=case,
            category=category,
            registered_by=self.context["request"].user,  # مهم
            registered_at=timezone.now(),  # مهم
            **validated_data,
        )

        # آپلود فایل‌ها اینجا انجام نمی‌شود → به view منتقل شده

        return evidence
