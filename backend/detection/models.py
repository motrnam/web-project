# backend/detection/models.py
from django.contrib.auth import get_user_model
from django.db import models
from django.core.exceptions import ValidationError

from case.models import Case
from evidences.models import Evidence
from interrogation.models import Suspect

User = get_user_model()


class DetectionBoard(models.Model):
    title = models.CharField(max_length=255)


class Lead(models.Model):
    LEAD_TYPES = [
        ('E', "Evidence"),
        ('N', "Detective Note"),
    ]

    title = models.CharField(max_length=255)
    board = models.ForeignKey(DetectionBoard, null=False, on_delete=models.CASCADE)
    lead_type = models.CharField(max_length=1, choices=LEAD_TYPES)
    evidence = models.ForeignKey(Evidence, null=True, blank=True, on_delete=models.RESTRICT)
    content = models.TextField(blank=True, null=True)  # Only for notes
    position_x = models.FloatField()
    position_y = models.FloatField()

    def clean(self):
        if self.position_x <= 0 or self.position_x >= 1 or self.position_y <= 0 or self.position_y >= 1:
            raise ValidationError("Position arguments must be between 0 and 1")
        if self.lead_type == 'E' and not (self.evidence is not None and not self.content):
            raise ValidationError('Lead must have evidence and no content for "Evidence" lead type.')
        if self.lead_type == 'N' and not (self.evidence is None and self.content):
            raise ValidationError('Lead must have content and no evidence for "Note" lead type.')


class Yarn(models.Model):
    lead1 = models.ForeignKey(Lead, null=False, related_name='yarns_as_first', on_delete=models.CASCADE)
    lead2 = models.ForeignKey(Lead, null=False, related_name='yarns_as_second', on_delete=models.CASCADE)

    def clean(self):
        if self.lead1.board != self.lead2.board:
            raise ValidationError("Board arguments must match")
        if self.lead1 == self.lead2:
            raise ValidationError("You cannot connect a lead to itself")


class Detection(models.Model):
    detective = models.ForeignKey(
        User,
        related_name="detections_as_detective",
        on_delete=models.RESTRICT,
        verbose_name="کارآگاه"
    )
    case = models.OneToOneField(Case, null=False, on_delete=models.RESTRICT, verbose_name="پرونده", related_name="detection")
    detection_board = models.OneToOneField(DetectionBoard, on_delete=models.RESTRICT, verbose_name="تخته", related_name="detection")
    sergeant = models.ForeignKey(
        User,
        null=True,
        blank=True,
        related_name="detections_as_sergeant",
        on_delete=models.SET_NULL,
        verbose_name="گروهبان"
    )

    def clean(self):
        if not self.detective.groups.filter(name='Detective').exists():
            raise ValidationError("کارآگاه باید کارآگاه باشد")
        if self.sergeant and not self.sergeant.groups.filter(name='Sergeant').exists():
            raise ValidationError("گروهبان باید گروهبان باشد")

    def can_delete(self):
        return False


class SuspectsSuggested(models.Model):
    states = [
        (0, "PENDING"),
        (1, "CONFIRMED"),
        (2, "REJECTED"),
    ]
    detection = models.ForeignKey(Detection, null=False, on_delete=models.RESTRICT)
    time_suggested = models.DateTimeField(auto_now_add=True)
    detective_reasons = models.TextField()
    state = models.SmallIntegerField(choices=states, default=0)
    feedback = models.TextField(blank=True)
    suspects = models.ManyToManyField(User, blank=True)

    class Meta:
        ordering = ["-time_suggested"]

    def clean(self):
        if self.detective_reasons is None or self.detective_reasons == '':
            raise ValidationError("Detective must provide reasons for their choice")
        if self.state == 2 and (self.feedback is None or self.feedback == ''):
            raise ValidationError("Rejected ones must have a reason why they're rejected")
