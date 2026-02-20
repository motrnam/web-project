# rewards/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RewardTipViewSet

router = DefaultRouter()
router.register(r'tips', RewardTipViewSet, basename='reward-tip')

urlpatterns = router.urls