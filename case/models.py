from django.db import models
import uuid

from project.settings import AUTH_USER_MODEL

class RequestForCaseStatus(models.TextChoices):
    PENDING = 'PENDING', 'Pending'
    REJECTED = 'REJECTED', 'Rejected'
    ACCEPTED = 'ACCEPTED', 'Accepted'
    RETURN_TO_SENDER = 'RETURN_TO_SENDER', 'Return to Sender'



class RegisterComplain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    creator = models.ForeignKey(AUTH_USER_MODEL,on_delete=models.RESTRICT)
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    TTL = models.IntegerField(3)
    status = models.CharField(max_length=20, choices=RequestForCaseStatus.choices, default=RequestForCaseStatus.PENDING)

class RequestCheck(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(on_delete=models.CASCADE)
    message = models.CharField(max_length=128)
    checked_by = models.ForeignKey(on_delete=models.RESTRICT)
    created_at = models.DateTimeField(auto_now_add=True)
    
class Case(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(RegisterComplain,on_delete=models.RESTRICT,null=True,editable=False)
    
class Complain(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    complainant = models.ForeignKey(AUTH_USER_MODEL,on_delete=models.RESTRICT)
    request = models.ForeignKey(RegisterComplain,on_delete=models.CASCADE)
    case = models.ForeignKey(Case,on_delete=models.CASCADE,null=True,default=None)
    created_at = models.DateTimeField(auto_now_add=True)