#users/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager

class User(AbstractUser):
    objects = UserManager()
    national_id = models.CharField(
        max_length=10,
        unique=True,
        verbose_name="کد ملی",
        help_text="کد ملی ۱۰ رقمی"
    )
    phone_number = models.CharField(
        max_length=11,
        unique=True,
        verbose_name="شماره همراه",
        help_text="شماره همراه با صفر ابتدایی، مثلاً 09123456789"
    )
    full_name = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="نام و نام خانوادگی"
    )
    email = models.EmailField(
        unique=True,
        verbose_name="ایمیل"
    )

    def __str__(self):
        if self.full_name:
            return f"{self.full_name} ({self.username})"
        return self.username

    def get_roles_display(self):
        if self.groups.exists():
            return ", ".join(group.name for group in self.groups.all())
        return "normal user"

    class Meta:
        verbose_name = "کاربر"
        verbose_name_plural = "کاربران"
        ordering = ['-date_joined']