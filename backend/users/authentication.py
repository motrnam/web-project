# backend/users/authentication.py
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

UserModel = get_user_model()


class MultiFieldAuthBackend(ModelBackend):
    """
    امکان ورود با یکی از این ۴ فیلد:
    - username
    - national_id
    - phone_number
    - email
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None or password is None:
            return None

        try:
            # جستجو در یکی از ۴ فیلد (اولین تطابق کافی است)
            user = UserModel.objects.get(
                Q(username__iexact=username) |
                Q(national_id__iexact=username) |
                Q(phone_number__iexact=username) |
                Q(email__iexact=username)
            )
        except UserModel.DoesNotExist:
            return None
        except UserModel.MultipleObjectsReturned:
            # اگر به هر دلیلی چند کاربر پیدا شد (نباید اتفاق بیفتد چون unique هستند)
            return None

        # چک رمز عبور
        if user.check_password(password):
            return user

        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None