

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, ProfileView, MedicalInfoView,
    MenstruationEntryViewSet, PregnancyEntryViewSet, MenopauseEntryViewSet,
    DoctorViewSet, MoodEntryViewSet, MythAnswerViewSet, ChatSummaryViewSet,
)

router = DefaultRouter()
router.register("menstruation", MenstruationEntryViewSet, basename="menstruation")
router.register("pregnancy", PregnancyEntryViewSet, basename="pregnancy")
router.register("menopause", MenopauseEntryViewSet, basename="menopause")
router.register("doctors", DoctorViewSet, basename="doctors")
router.register("moods", MoodEntryViewSet, basename="moods")
router.register("myths", MythAnswerViewSet, basename="myths")
router.register("chat-summaries", ChatSummaryViewSet, basename="chat-summaries")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("medical-info/", MedicalInfoView.as_view(), name="medical-info"),
    path("", include(router.urls)),
]