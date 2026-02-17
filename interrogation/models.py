from django.db import models
from django.contrib.auth import get_user_model
from case.models import Case
from django.core.validators import MaxValueValidator, MinValueValidator
import uuid
from django.core.exceptions import ValidationError


# Create your models here.
User = get_user_model()


class VerdictStatus(models.TextChoices):
    GUILTY = "GUILTY", "guilty"
    NOT_GUILTY = "NOT_GUILTY", "not guilty"


class PoliceChiefApproval(models.TextChoices):
    APPROVED = "APPROVED", "approved"
    NOT_APPROVED = "NOT_APPROVED", "not approved"


class SuspectStatus(models.TextChoices):
    CAPTURED = "CAPTURED", "captured"
    WANTED = "WANTED", "wanted"
    MOST_WANTED = "MOST_WANTED", "most wanted"


class Suspect(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    person = models.ForeignKey(User, on_delete=models.RESTRICT)
    case = models.ForeignKey(Case, on_delete=models.RESTRICT)
    detail = models.CharField(max_length=200)
    suspect_status = models.CharField(
        max_length=20, choices=SuspectStatus.choices, default=SuspectStatus.WANTED
    )


class Interrogation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    suspect = models.ForeignKey(Suspect, on_delete=models.RESTRICT)
    interrogator_sergeant = models.ForeignKey(User, on_delete=models.RESTRICT,related_name="interrogation_sergeant")
    interrogator_detective = models.ForeignKey(User, on_delete=models.RESTRICT,related_name="interrogation_detective")
    sergeant_score = models.IntegerField(
        default=5, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )

    detective_score = models.IntegerField(
        default=5, validators=[MaxValueValidator(10), MinValueValidator(1)]
    )

    capitan_comment = models.CharField(max_length=100, null=True, blank=True)
    capitan_verdict = models.CharField(
        max_length=20, choices=VerdictStatus.choices, null=True
    )
    chief_approved = models.CharField(
        max_length=20, choices=PoliceChiefApproval.choices, null=True
    )
    
    def clean(self):
        if not self.interrogator_detective.groups.filter(name = "Detective").exists():
            raise ValidationError("`interrogator_detective` must contain `Detective` group")
        if not self.interrogator_sergeant.groups.filter(name = "Sergeant").exists():
            raise ValidationError("`interrogator_detective` must contain `Sergeant` group")
        
    

class Court(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    judge = models.ForeignKey(User, on_delete=models.RESTRICT)
    interrogation = models.ForeignKey(Interrogation, on_delete=models.RESTRICT)
    created_at = models.DateField(auto_now_add=True)
    final_verdict = models.CharField(
        max_length=20, choices=VerdictStatus.choices, null=True
    )
    date = models.DateField()
