# evidences/views.py

from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone

from .models import Evidence, BiologicalEvidence, EvidenceMedia
from .serializers import (
    EvidencePolymorphicSerializer,
    EvidenceCreateSerializer,
    EvidenceMediaSerializer,
    BiologicalEvidenceSerializer,
)
from users.permissions import (
    IsPoliceNotCadet,
    IsCoroner,
    IsSergeant,
    CanVerifyBiologicalEvidence,
    CanDeleteEvidence,
    CanEditEvidence,
    CanAddMediaToEvidence,
    CanRegisterEvidence,  # فرض بر وجود این permissionها
)


class EvidenceViewSet(viewsets.ModelViewSet):
    """
    مدیریت شواهد پرونده‌ها
    - لیست / جزئیات / ایجاد / ویرایش / حذف
    - ایجاد با category مشخص → زیرنوع مناسب ساخته می‌شود
    """

    queryset = (
        Evidence.objects.all()
        .select_related("case", "registered_by")
        .prefetch_related("media")
    )
    serializer_class = EvidencePolymorphicSerializer
    permission_classes = [permissions.IsAuthenticated, IsPoliceNotCadet]

    def get_permissions(self):
        if self.action == "create":
            return [permissions.IsAuthenticated(), CanRegisterEvidence()]
        if self.action == "add_media":
            return [permissions.IsAuthenticated(), CanAddMediaToEvidence()]
        if self.action in ["update", "partial_update"]:
            return [permissions.IsAuthenticated(), CanEditEvidence()]
        if self.action == "destroy":
            return [permissions.IsAuthenticated(), CanDeleteEvidence()]
        if self.action == "verify_biological":
            return [permissions.IsAuthenticated(), CanVerifyBiologicalEvidence()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        qs = super().get_queryset()
        case_id = self.request.query_params.get("case")
        if case_id:
            qs = qs.filter(case_id=case_id)
        return qs

    def get_serializer_class(self):
        if self.action == "create":
            return EvidenceCreateSerializer
        if self.action in ["update", "partial_update"]:
            # برای ویرایش ساده → از polymorphic استفاده می‌کنیم (یا serializer جدا بساز)
            return EvidencePolymorphicSerializer
        if self.action in ["retrieve", "list"]:
            return EvidencePolymorphicSerializer
        return super().get_serializer_class()

    def perform_create(self, serializer):
        serializer.save(registered_by=self.request.user)

    @swagger_auto_schema(
        method="POST",
        request_body=EvidenceCreateSerializer,
        responses={201: EvidencePolymorphicSerializer},
    )
    def create(self, request, *args, **kwargs):
        """
        ایجاد شواهد جدید با دسته‌بندی مشخص
        - فایل‌های رسانه می‌توانند همزمان آپلود شوند (multipart/form-data)
        - registered_by خودکار ست می‌شود
        """
        # 1. سریالایزر را با context مناسب مقداردهی می‌کنیم
        serializer = self.get_serializer(
            data=request.data, context={"request": request, "view": self}
        )

        # 2. اعتبارسنجی داده‌ها
        serializer.is_valid(raise_exception=True)

        # 3. ذخیره شیء با استفاده از متد create سریالایزر
        # اینجا registered_by و registered_at داخل create سریالایزر ست می‌شوند
        evidence = serializer.save()

        # 4. مدیریت آپلود فایل‌ها (چون ListField write_only است و در validated_data نمی‌آید)
        media_files = request.FILES.getlist("media_files") or []
        for file in media_files:
            # حدس نوع رسانه بر اساس پسوند فایل
            media_type = self._guess_media_type(file.name)

            # چک مجاز بودن نوع فایل برای این دسته شواهد
            if media_type not in evidence.allowed_media_types():
                raise ValidationError(
                    detail={
                        "media_type": f"نوع رسانه {media_type} برای دسته {evidence.category} مجاز نیست.",
                        "allowed": evidence.allowed_media_types(),
                    }
                )

            EvidenceMedia.objects.create(
                evidence=evidence,
                file=file,
                media_type=media_type,
                uploaded_by=request.user,
                description=f"آپلود شده در {timezone.now().strftime('%Y-%m-%d %H:%M')}",
            )

        # 5. آماده‌سازی پاسخ (استفاده از polymorphic برای نمایش کامل)
        response_serializer = EvidencePolymorphicSerializer(
            evidence, context={"request": request}
        )

        headers = self.get_success_headers(response_serializer.data)

        return Response(
            response_serializer.data, status=status.HTTP_201_CREATED, headers=headers
        )

    def _guess_media_type(self, filename):
        ext = filename.lower().split(".")[-1]
        if ext in ["jpg", "jpeg", "png", "gif"]:
            return "PHOTO"
        if ext in ["mp4", "mov", "avi"]:
            return "VIDEO"
        if ext in ["mp3", "wav", "m4a"]:
            return "AUDIO"
        if ext in ["pdf", "doc", "docx"]:
            return "DOCUMENT"
        return "PHOTO"  # default

    @action(detail=True, methods=["post"], url_path="add-media")
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "file": openapi.Schema(type=openapi.TYPE_FILE),
                "media_type": openapi.Schema(
                    type=openapi.TYPE_STRING,
                    enum=["PHOTO", "VIDEO", "AUDIO", "DOCUMENT"],
                ),
                "description": openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=["file"],
        ),
        responses={201: EvidenceMediaSerializer},
    )
    def add_media(self, request, pk=None):
        evidence = self.get_object()

        if "file" not in request.FILES:
            raise ValidationError({"file": "فایل الزامی است"})

        file = request.FILES["file"]
        media_type = request.data.get("media_type", self._guess_media_type(file.name))
        description = request.data.get("description", "")

        # چک مجاز بودن نوع رسانه برای این دسته
        if media_type not in evidence.allowed_media_types():
            raise ValidationError(
                f"نوع رسانه {media_type} برای این شواهد مجاز نیست. "
                f"مجاز: {', '.join(evidence.allowed_media_types())}"
            )

        media = EvidenceMedia.objects.create(
            evidence=evidence,
            file=file,
            media_type=media_type,
            uploaded_by=request.user,
            description=description,
        )

        return Response(
            EvidenceMediaSerializer(media).data, status=status.HTTP_201_CREATED
        )

    @action(detail=True, methods=["post"], permission_classes=[IsCoroner | IsSergeant])
    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                "coroner_result": openapi.Schema(type=openapi.TYPE_STRING),
                "db_match_result": openapi.Schema(type=openapi.TYPE_STRING),
            },
        ),
        responses={200: BiologicalEvidenceSerializer},
    )
    def verify_biological(self, request, pk=None):
        evidence = self.get_object()
        if not isinstance(evidence, BiologicalEvidence):
            raise ValidationError("این عملیات فقط برای شواهد زیستی مجاز است.")

        evidence.coroner_result = request.data.get(
            "coroner_result", evidence.coroner_result
        )
        evidence.db_match_result = request.data.get(
            "db_match_result", evidence.db_match_result
        )
        evidence.coroner = request.user
        evidence.coroner_verified_at = timezone.now()
        evidence.db_match_verified_at = (
            timezone.now() if evidence.db_match_result else None
        )
        evidence.save()

        return Response(BiologicalEvidenceSerializer(evidence).data)
