from rest_framework import permissions
from case.models import ComplainStatus


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