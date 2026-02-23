# backend/detection/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    DetectionBoardViewSet, LeadViewSet, YarnViewSet,
    SuspectsSuggestionViewSet, SergeantSuggestionViewSet, test_view
)

router = DefaultRouter()
router.register(r'boards', DetectionBoardViewSet, basename='detection-board')
router.register(r'leads', LeadViewSet, basename='lead')
router.register(r'yarns', YarnViewSet, basename='yarn')
router.register(r'suggestions', SuspectsSuggestionViewSet, basename='suggestion')
router.register(r'sergeant/suggestions', SergeantSuggestionViewSet, basename='sergeant-suggestion')

urlpatterns = [
    path('test/', test_view, name='test'),  # Temporary test endpoint
    path('', include(router.urls)),
]
