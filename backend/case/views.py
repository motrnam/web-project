#case/views.py
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.utils import timezone
from .models import (
    RegisterComplain, ComplainReview, Complainant,
    CrimeSceneReport, Case,
    ComplainStatus, CrimeSceneReportStatus, ComplainantStatus
)
from .serializers import (
    EmptySerializer, RegisterComplainSerializer, ComplainantSerializer, CrimeSceneReportSerializer,
    CrimeSceneWitnessSerializer,CaseSerializer
)
from users.permissions import (
    IsPoliceNotCadet, CanSubmitComplaint, IsCadetReviewer, IsOfficerReviewer
)
from interrogation.serializers import SuspectSerializer

class RegisterComplainViewSet(viewsets.ModelViewSet):
    queryset = RegisterComplain.objects.all()
    serializer_class = RegisterComplainSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_permissions(self):
        if self.action in ['create']:
            return [permissions.IsAuthenticated()]  # فقط کاربران عادی (Base User)
        if self.action in ['submit', 'update', 'partial_update']:
            return [CanSubmitComplaint()]
        if self.action in ['cadet_review', 'review_complainant']:
            return [IsCadetReviewer()]
        if self.action == 'officer_review':
            return [IsOfficerReviewer()]
        return super().get_permissions()

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user, status=ComplainStatus.DRAFT)

    @swagger_auto_schema(
        method='post',
        operation_description="ارسال شکایت به کارآموز برای بررسی (تغییر وضعیت به PENDING_CADET)",
        responses={200: RegisterComplainSerializer(many=False)}
    )
    @action(detail=True, methods=['post'],serializer_class=EmptySerializer)
    def submit(self, request, pk=None):
        complain = self.get_object()
        if not complain.can_submit():
            raise ValidationError(
                detail={
                    "status": complain.status,
                    "revision_count": complain.revision_count,
                    "message": "شکایت قابل ارسال نیست. یا وضعیت مناسب نیست یا حداکثر ویرایش رسیده است."
                }
            )
        complain.status = ComplainStatus.PENDING_CADET
        complain.save(update_fields=['status'])
        return Response(RegisterComplainSerializer(complain).data)

    @swagger_auto_schema(
        method='post',
        operation_description="بررسی توسط کارآموز - accept یا return",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['accept', 'return']),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['action']
        ),
        responses={200: RegisterComplainSerializer, 400: 'Bad request'}
    )
    @action(detail=True, methods=['post'])
    def cadet_review(self, request, pk=None):
        complain = self.get_object()
        action_type = request.data.get('action')
        message = request.data.get('message', '').strip()

        if action_type not in ['accept', 'return']:
            raise ValidationError("action باید 'accept' یا 'return' باشد")

        if action_type == 'return' and not message:
            raise ValidationError("هنگام بازگشت، پیام الزامی است")

        review = ComplainReview.objects.create(
            complain=complain,
            reviewed_by=request.user,
            message=message,
            is_approval=(action_type == 'accept'),
            to_status=ComplainStatus.PENDING_OFFICER if action_type == 'accept' else ComplainStatus.RETURNED_TO_COMPLAINANT
        )

        if action_type == 'return':
            complain.revision_count += 1
            if complain.revision_count >= complain.max_revisions:
                complain.status = ComplainStatus.CANCELLED
                review.to_status = ComplainStatus.CANCELLED
                review.save()
            else:
                complain.status = ComplainStatus.RETURNED_TO_COMPLAINANT
        else:
            complain.status = ComplainStatus.PENDING_OFFICER

        complain.save()
        return Response(RegisterComplainSerializer(complain).data)

    @swagger_auto_schema(
        method='post',
        operation_description="بررسی توسط افسر پلیس - accept (تشکیل پرونده) یا return (به کارآموز)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['accept', 'return']),
                'message': openapi.Schema(type=openapi.TYPE_STRING),
            },
            required=['action']
        )
    )
    @action(detail=True, methods=['post'])
    def officer_review(self, request, pk=None):
        complain = self.get_object()
        action_type = request.data.get('action')
        message = request.data.get('message', '').strip()

        if action_type not in ['accept', 'return']:
            raise ValidationError("action باید 'accept' یا 'return' باشد")

        review = ComplainReview.objects.create(
            complain=complain,
            reviewed_by=request.user,
            message=message,
            is_approval=(action_type == 'accept'),
            to_status=ComplainStatus.APPROVED if action_type == 'accept' else ComplainStatus.PENDING_CADET
        )

        if action_type == 'accept':
            case = Case.objects.create(
                complain=complain,
                created_by=request.user,
                crime_type=complain.crime_type,  # ← از مدل خوانده می‌شود
                status="OPEN"
            )
            complain.status = ComplainStatus.APPROVED
        else:
            complain.status = ComplainStatus.PENDING_CADET

        complain.save()
        return Response(RegisterComplainSerializer(complain).data)
    

    @swagger_auto_schema(
        method='post',
        operation_description="اضافه کردن شاکی اضافی به شکایت (فقط در وضعیت‌های مجاز)",
        request_body=ComplainantSerializer,
        responses={201: ComplainantSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_complainant(self, request, pk=None):
        complain = self.get_object()
        if complain.status not in [ComplainStatus.DRAFT, ComplainStatus.PENDING_CADET, ComplainStatus.RETURNED_TO_COMPLAINANT]:
            raise ValidationError("نمی‌توان در این وضعیت شاکی اضافه کرد")

        serializer = ComplainantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(complain=complain)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method='post',
        operation_description="تأیید/رد شاکی اضافی توسط کارآموز",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            # properties={
            #     'complainant_id': openapi.Schema(type=openapi.TYPE_UUID),
            #     'action': openapi.Schema(type=openapi.TYPE_STRING, enum=['approve', 'reject']),
            #     'message': openapi.Schema(type=openapi.TYPE_STRING),
            # },
            required=['complainant_id', 'action']
        ),
        responses={200: ComplainantSerializer}
    )
    @action(detail=True, methods=['post'])
    def review_complainant(self, request, pk=None):
        complain = self.get_object()
        complainant_id = request.data.get('complainant_id')
        action = request.data.get('action')
        message = request.data.get('message', '')

        if action not in ['approve', 'reject']:
            raise ValidationError("action باید 'approve' یا 'reject' باشد")

        try:
            complainant = complain.complainants.get(id=complainant_id)
        except Complainant.DoesNotExist:
            raise ValidationError("شاکی یافت نشد")

        if complainant.status != ComplainantStatus.PENDING:
            raise ValidationError("شاکی قبلاً بررسی شده")

        complainant.status = ComplainantStatus.APPROVED if action == 'approve' else ComplainantStatus.REJECTED
        # می‌توان ComplainReview جدا برای شاکیان اضافه کرد، اما فعلاً ساده نگه داشتم
        complainant.save()

        return Response(ComplainantSerializer(complainant).data)


# ────────────────────────────────────────────────
#               Crime Scene Report
# ────────────────────────────────────────────────

class CrimeSceneReportViewSet(viewsets.ModelViewSet):
    queryset = CrimeSceneReport.objects.all()
    serializer_class = CrimeSceneReportSerializer
    permission_classes = [permissions.IsAuthenticated, IsPoliceNotCadet]

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user, status=CrimeSceneReportStatus.DRAFT)

    @swagger_auto_schema(
        method='post',
        operation_description="ارسال گزارش صحنه جرم به مافوق (یا مستقیم تأیید اگر Chief باشد)",
        responses={200: CrimeSceneReportSerializer}
    )
    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        report = self.get_object()
        if report.status != CrimeSceneReportStatus.DRAFT:
            raise ValidationError("گزارش قبلاً ارسال شده است.")

        if request.user.groups.filter(name='Chief').exists():
            # استثنا: Chief مستقیم تأیید می‌کند
            report.status = CrimeSceneReportStatus.APPROVED
            report.supervisor = request.user
            report.approved_at = timezone.now()
            case = Case.objects.create(
                crime_scene_report=report,
                created_by=request.user,
                crime_type=report.crime_type,
                status="OPEN"
            )
            report.case = case
        else:
            report.status = CrimeSceneReportStatus.PENDING_SUPERVISOR

        report.save()
        return Response(CrimeSceneReportSerializer(report).data)

    @swagger_auto_schema(
        method='post',
        operation_description="تأیید گزارش صحنه جرم توسط مافوق و تشکیل پرونده",
        responses={200: CrimeSceneReportSerializer}
    )
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        report = self.get_object()
        if report.status != CrimeSceneReportStatus.PENDING_SUPERVISOR:
            raise ValidationError("گزارش در وضعیت قابل تأیید نیست.")

        report.status = CrimeSceneReportStatus.APPROVED
        report.supervisor = request.user
        report.approved_at = timezone.now()
        report.save()

        case = Case.objects.create(
            crime_scene_report=report,
            created_by=request.user,
            crime_type=report.crime_type,
            status="OPEN"
        )
        report.case = case
        report.save()

        return Response(CrimeSceneReportSerializer(report).data)

    @swagger_auto_schema(
        method='post',
        operation_description="اضافه کردن شاهد به گزارش صحنه جرم",
        request_body=CrimeSceneWitnessSerializer,
        responses={201: CrimeSceneWitnessSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_witness(self, request, pk=None):
        report = self.get_object()
        serializer = CrimeSceneWitnessSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        witness = serializer.save(report=report)
        return Response(CrimeSceneWitnessSerializer(witness).data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method='post',
        operation_description="اضافه کردن شاکی به پرونده صحنه جرم (فقط بعد از تشکیل Case)",
        request_body=ComplainantSerializer,
        responses={201: ComplainantSerializer}
    )
    @action(detail=True, methods=['post'])
    def add_complainant(self, request, pk=None):
        report = self.get_object()
        if not report.case:
            raise ValidationError("پرونده هنوز تشکیل نشده. ابتدا گزارش را تأیید کنید.")

        serializer = ComplainantSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(case=report.case)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
class CaseViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Case.objects.all()
    serializer_class = CaseSerializer
    permission_classes = [permissions.IsAuthenticated]

    @swagger_auto_schema(
        method='post',
        operation_description="Add a suspect to a case",
        request_body=SuspectSerializer,
    )
    @action(detail=True, methods=['post'])
    def add_suspect(self, request, pk=None):
        case = self.get_object()

        if case.status != "OPEN":
            raise ValidationError("You cannot add suspects unless the case is OPEN")

        serializer = SuspectSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(case=case, added_by=request.user)

        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @swagger_auto_schema(
        method='post',
        operation_description="Detective starts working on a case - creates Detection and DetectionBoard",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'sergeant_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of assigned sergeant'),
                'board_title': openapi.Schema(type=openapi.TYPE_STRING, description='Title for the detection board'),
            },
            required=['sergeant_id']
        )
    )
    @action(detail=True, methods=['post'], url_path='start-detection')
    def start_detection(self, request, pk=None):
        """Detective starts working on a case by creating a Detection"""
        from detection.models import Detection, DetectionBoard
        from users.permissions import IsDetective
        
        case = self.get_object()
        
        # Check if user is a detective
        if not request.user.groups.filter(name='Detective').exists():
            raise ValidationError("Only detectives can start case detection")
        
        # Check if detection already exists
        if hasattr(case, 'detection') and case.detection:
            raise ValidationError("Detection already exists for this case")
        
        sergeant_id = request.data.get('sergeant_id')
        if not sergeant_id:
            raise ValidationError("sergeant_id is required")
        
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            sergeant = User.objects.get(id=sergeant_id)
        except User.DoesNotExist:
            raise ValidationError("Sergeant not found")
        
        if not sergeant.groups.filter(name='Sergeant').exists():
            raise ValidationError("Selected user is not a sergeant")
        
        # Create detection board
        board_title = request.data.get('board_title', f'تحقیقات پرونده {case.case_number}')
        board = DetectionBoard.objects.create(title=board_title)
        
        # Create detection
        detection = Detection.objects.create(
            detective=request.user,
            case=case,
            detection_board=board,
            sergeant=sergeant
        )
        
        return Response({
            'message': 'Detection started successfully',
            'detection_id': detection.id,
            'board_id': board.id,
            'case_id': str(case.id),
            'detective': request.user.username,
            'sergeant': sergeant.username
        }, status=status.HTTP_201_CREATED)