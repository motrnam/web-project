#users/permissions.py
from rest_framework import permissions
from case.models import ComplainStatus
from evidences.models import Evidence
from case.models import Case

class IsAdministrator(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Administrator').exists()

class IsCadet(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Cadet').exists()

class IsPoliceOfficer(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name__in=['Police Officer', 'Patrol Officer']).exists()

class IsDetective(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Detective').exists()

class IsSergeant(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Sergeant').exists()

class IsCaptain(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Captain').exists()

class IsChief(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Chief').exists()

class IsCoroner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Coroner').exists()

class IsJudge(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Judge').exists()

# برای کاربران عادی (شاکی، شاهد و ...)
class IsBaseUser(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(name='Base User').exists()
    
class IsNotBaseUser(permissions.BasePermission):
    """Permission to deny access to base users"""
    def has_permission(self, request, view):
        # TODO implement better check
        return request.user.groups.count() > 1

class IsOwner(permissions.BasePermission):
    """Permission to only allow owners of a case to edit it"""
    def has_object_permission(self, request, view, obj):
        return obj.petrol_creator == request.user

class CanSubmitComplaint(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            obj.creator == request.user and
            obj.status in [ComplainStatus.DRAFT, ComplainStatus.RETURNED_TO_COMPLAINANT] and
            obj.revision_count < obj.max_revisions
        )

class IsCadetReviewer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.groups.filter(name='Cadet').exists() and
            obj.status == ComplainStatus.PENDING_CADET
        )

class IsOfficerReviewer(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return (
            request.user.groups.filter(name__in=['Police Officer', 'Patrol Officer']).exists() and
            obj.status == ComplainStatus.PENDING_OFFICER
        )

class IsPoliceNotCadet(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.groups.filter(
            name__in=['Police Officer', 'Patrol Officer', 'Detective', 'Sergeant', 'Captain', 'Chief']
        ).exists()

class IsSupervisor(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # فرض: Chief نیازی به supervisor ندارد؛ بقیه نیاز به Chief/Captain/Sergeant دارند
        if request.user.groups.filter(name='Chief').exists():
            return True
        return request.user.groups.filter(
            name__in=['Captain', 'Sergeant']
        ).exists() and obj.reporter != request.user  # نه خود reporter


class CanRegisterEvidence(permissions.BasePermission):
    """
    اجازه ثبت شواهد جدید
    معمولاً: پلیس غیر کارآموز + دسترسی به پرونده
    """
    def has_permission(self, request, view):
        # شرط پایه: کاربر پلیس غیر کارآموز باشد
        if not request.user.groups.filter(
            name__in=['Police Officer', 'Patrol Officer', 'Detective', 'Sergeant', 'Captain', 'Chief']
        ).exists():
            return False
        return True

    def has_object_permission(self, request, view, obj):
        # obj اینجا معمولاً Case است (اگر در view چک شود)
        if isinstance(obj, Case):
            # مثلاً: فقط کسی که پرونده را ایجاد کرده یا درگیر آن است
            return obj.created_by == request.user or \
                   obj.evidences.filter(registered_by=request.user).exists()  # یا شرط‌های دیگر
        return True  # اگر obj Evidence باشد، در create معمولاً اعمال نمی‌شود


class CanAddMediaToEvidence(permissions.BasePermission):
    """
    اجازه اضافه کردن فایل/رسانه به یک شواهد موجود
    """
    def has_object_permission(self, request, view, obj):  # obj → Evidence
        if not isinstance(obj, Evidence):
            return False

        # شرط: ثبت‌کننده شواهد باشد یا نقش بالاتر (مثل Sergeant یا Detective)
        if obj.registered_by == request.user:
            return True

        # اختیاری: اجازه به گروهبان/کارآگاه/کاپیتان برای پرونده مربوطه
        case = obj.case
        if case and (
            request.user.groups.filter(name__in=['Detective', 'Sergeant', 'Captain', 'Chief']).exists()
        ):
            return True

        return False


class CanEditEvidence(permissions.BasePermission):
    """
    اجازه ویرایش شواهد (title, description, فیلدهای خاص و ...)
    """
    def has_object_permission(self, request, view, obj):  # obj → Evidence
        if not isinstance(obj, Evidence):
            return False

        # ثبت‌کننده اصلی بتواند ویرایش کند
        if obj.registered_by == request.user:
            return True

        # نقش‌های بالاتر برای پرونده مربوطه
        if request.user.groups.filter(name__in=['Sergeant', 'Captain', 'Chief']).exists():
            return True

        # اختیاری: کارآگاه مسئول پرونده هم بتواند ویرایش کند
        # اگر مدل Detection یا رابطه‌ای با کارآگاه دارید، اینجا چک کنید

        return False


class CanDeleteEvidence(permissions.BasePermission):
    """
    اجازه حذف شواهد
    معمولاً محدود به نقش‌های خیلی بالا یا ثبت‌کننده + شرط زمانی
    """
    def has_object_permission(self, request, view, obj):  # obj → Evidence
        if not isinstance(obj, Evidence):
            return False

        # فقط ثبت‌کننده یا Chief/Sergeant بتواند حذف کند
        if obj.registered_by == request.user:
            return True

        if request.user.groups.filter(name__in=['Sergeant', 'Captain', 'Chief']).exists():
            return True

        # می‌توانید شرط زمانی اضافه کنید مثلاً:
        # from django.utils import timezone
        # if (timezone.now() - obj.registered_at).days <= 1:  # فقط در ۲۴ ساعت اول

        return False


class CanVerifyBiologicalEvidence(permissions.BasePermission):
    """
    اجازه تأیید/ثبت نتیجه برای شواهد زیستی (coroner_result, db_match_result)
    """
    def has_permission(self, request, view):
        # شرط پایه: Coroner یا Sergeant/Captain (طبق نیازمندی پروژه)
        return request.user.groups.filter(
            name__in=['Coroner', 'Sergeant', 'Captain']
        ).exists()

    def has_object_permission(self, request, view, obj):  # obj → Evidence
        if not isinstance(obj, Evidence):
            return False

        # فقط برای نوع زیستی
        from evidences.models import BiologicalEvidence
        if not isinstance(obj, BiologicalEvidence):
            return False

        # Coroner حتماً باید Coroner باشد
        if request.user.groups.filter(name='Coroner').exists():
            return True

        # Sergeant یا Captain هم می‌توانند (اختیاری، بسته به سیاست پروژه)
        if request.user.groups.filter(name__in=['Sergeant', 'Captain']).exists():
            return True

        return False