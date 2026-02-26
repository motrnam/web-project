from django.db import migrations


def create_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
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
        'Base User',
        'Administrator',
    ]
    for group_name in groups:
        Group.objects.get_or_create(name=group_name)


def delete_groups(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name__in=groups).delete()


class Migration(migrations.Migration):
    dependencies = [
        ('users', '0001_initial'),
        ('users', '0002_user_photo'),
    ]

    operations = [
        migrations.RunPython(create_groups, delete_groups),
    ]
