from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    RegisterView, ProfileView, MedicalInfoView,
    DailyLogViewSet, ReminderViewSet, SymptomViewSet,
    DoctorViewSet, MythAnswerViewSet, ChatSummaryViewSet,
)

router = DefaultRouter()
router.register("daily-logs", DailyLogViewSet, basename="daily-logs")
router.register("reminders", ReminderViewSet, basename="reminders")
router.register("symptoms", SymptomViewSet, basename="symptoms")
router.register("doctors", DoctorViewSet, basename="doctors")
router.register("myths", MythAnswerViewSet, basename="myths")
router.register("chat-summaries", ChatSummaryViewSet, basename="chat-summaries")

urlpatterns = [
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("medical-info/", MedicalInfoView.as_view(), name="medical-info"),
    path("", include(router.urls)),
]
