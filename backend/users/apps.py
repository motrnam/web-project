#backend/users/apps.py
from django.apps import AppConfig
from django.db.models.signals import post_migrate

class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        from django.contrib.auth.models import Group
        groups = [
            'Detective',
            'Sergeant',
            'Captain',
            'Chief',
            'Coroner',
            'Judge',
            'Police Officer',
            'Patrol Officer',
            'Cadet',
        ]
        for group_name in groups:
            Group.objects.get_or_create(name=group_name)