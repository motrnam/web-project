from django.db import models
from django.contrib.auth.models import User
import uuid

# Create your models here.
class CrimeType(models.TextChoices):
    TYPE1 = 'Type1', 'Type 1'
    TYPE2 = 'Type2', 'Type 2'
    TYPE3 = 'Type3', 'Type 3'
    CRITICAL = 'Critical', 'Critical'
    


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    national_id = models.CharField(max_length=20, unique=True)
    phone_number = models.CharField(max_length=15, unique=True)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Witness(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=15)
    detail = models.CharField(max_length=200)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class CaseReport(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    cadet_message = models.CharField(max_length=200, blank=True, null=True)
    number_of_edits = models.IntegerField(default=0)
    
class CriminalCase(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    case_report = models.ForeignKey(CaseReport, on_delete=models.CASCADE , related_name='criminal_cases' , null=True)
    Witness = models.ForeignKey(Witness, on_delete=models.CASCADE , related_name='criminal_cases' , null=True)
    description = models.CharField(max_length=200)
    crime_type = models.CharField(max_length=20, choices=CrimeType.choices)
    
    
