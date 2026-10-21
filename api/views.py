from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import render
from rest_framework import viewsets, generics, permissions
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    AppRelease,
    ChatSummary,
    DailyLog,
    Doctor,
    MedicalInfo,
    MythAnswer,
    Profile,
    Reminder,
    Symptom,
)

from .serializers import (
    ChatSummarySerializer,
    DailyLogSerializer,
    DoctorSerializer,
    EmailTokenObtainPairSerializer,
    MedicalInfoSerializer,
    MythAnswerSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ReminderSerializer,
    SymptomSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(
            user=self.request.user
        )
        return profile


class UserScopedViewSet(viewsets.ModelViewSet):
    """Base class: cada usuario solo puede acceder a sus propios datos."""

    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DailyLogViewSet(UserScopedViewSet):
    queryset = DailyLog.objects.prefetch_related("symptoms__symptom")
    serializer_class = DailyLogSerializer


class ReminderViewSet(UserScopedViewSet):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo de síntomas (igual para todas las usuarias)."""

    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "code"


class DoctorViewSet(UserScopedViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class MythAnswerViewSet(UserScopedViewSet):
    queryset = MythAnswer.objects.all()
    serializer_class = MythAnswerSerializer


class ChatSummaryViewSet(UserScopedViewSet):
    queryset = ChatSummary.objects.all()
    serializer_class = ChatSummarySerializer


class MedicalInfoView(generics.RetrieveUpdateAPIView):
    serializer_class = MedicalInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        info, _ = MedicalInfo.objects.prefetch_related("surgeries", "usual_symptoms__symptom").get_or_create(
            user=self.request.user
        )
        return info


def download_app_page(request):
    return render(request, "api/download_app.html", {"release": AppRelease.objects.first()})


def download_latest_app(request):
    release = AppRelease.objects.first()
    if release is None:
        raise Http404("No app release is available.")
    return FileResponse(
        release.apk.open("rb"),
        as_attachment=True,
        filename=Path(release.apk.name).name,
        content_type="application/vnd.android.package-archive",
    )