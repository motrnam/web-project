# users/permissions.py
from rest_framework import permissions

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

    