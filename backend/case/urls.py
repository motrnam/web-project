# backend/case/urls.py
from django.urls import path
from .views import (
    RegisterComplainViewSet,
    CrimeSceneReportViewSet,
    CaseViewSet,
    StatsView
)

urlpatterns = [
    # ... سایر URLها ...
    path('stats/', StatsView.as_view(), name='stats'),
]