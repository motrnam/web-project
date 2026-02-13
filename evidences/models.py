import uuid

from django.core.exceptions import ValidationError
from django.db import models

from case.models import Case
# from project.settings import AUTH_USER_MODEL
from django.contrib.auth import get_user_model
User = get_user_model()



# Create your models here.
class Evidence(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    entered_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    technician = models.ForeignKey(User, on_delete=models.RESTRICT)  
    case = models.ForeignKey(Case,on_delete=models.RESTRICT,null=True) # TODO later change it to false

    def allowed_media_types(self):
        """MUST be implemented by child classes"""
        raise NotImplementedError("Child classes must implement allowed_media_types()")


class Witness(models.Model):
    user = models.OneToOneField(User,
                                on_delete=models.CASCADE)  # TODO: check they have witness or non-intern police role
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    detail = models.TextField()
    case = models.ForeignKey(Case,on_delete=models.RESTRICT,null=True) # TODO later cahnge it to false
    def allowed_media_types(self):
        return ['PHOTO', 'VID', 'AUD']


class BiologicalEvidence(Evidence):
    is_accepted = models.BooleanField(default=False)

    # TODO: نتیجۀ پیگیری

    def allowed_media_types(self):
        return ['PHOTO']


class VehicleEvidence(Evidence):
    model = models.CharField(max_length=255)
    license_plate = models.CharField(max_length=13)
    color = models.CharField(max_length=30)
    serial_number = models.CharField(max_length=255)

    def allowed_media_types(self):
        return []

    def clean(self):
        return (self.license_plate is not None and self.serial_number is None) or (
                self.license_plate is None and self.serial_number is not None)


class IdDocumentEvidence(Evidence):
    owner_name = models.CharField(max_length=255)

    def allowed_media_types(self):
        return []


class IdDocumentProperty(models.Model):
    id_document = models.ForeignKey(IdDocumentEvidence, on_delete=models.CASCADE, related_name='properties')
    key = models.CharField(max_length=255)
    value = models.CharField(max_length=255)


class OtherEvidences(Evidence):
    detail = models.CharField(max_length=255)
    # TODO 


class EvidenceMedia(models.Model):
    MEDIA_TYPES = [
        ('PHOTO', 'Photo'),
        ('VID', 'Video'),
        ('AUD', 'Audio'),
    ]
    evidence = models.ForeignKey(Evidence, on_delete=models.CASCADE, related_name='media')
    file = models.FileField(upload_to='evidence_media/%Y/%m/%d')
    media_type = models.CharField(max_length=20, choices=MEDIA_TYPES)

    def clean(self):
        if self.media_type not in self.evidence.allowed_media_types():
            raise ValidationError("Evidence media type '{}' is not allowed".format(self.media_type))
