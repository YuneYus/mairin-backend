from pathlib import Path

from django.http import FileResponse, Http404
from django.shortcuts import render
from rest_framework import viewsets, generics, permissions
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    Profile,
    MenstruationEntry,
    PregnancyEntry,
    MenopauseEntry,
    Doctor,
    MoodEntry,
    MythAnswer,
    ChatSummary,
    MedicalInfo,
    AppRelease,
)

from .serializers import (
    RegisterSerializer,
    ProfileSerializer,
    MenstruationEntrySerializer,
    PregnancyEntrySerializer,
    MenopauseEntrySerializer,
    DoctorSerializer,
    MoodEntrySerializer,
    MythAnswerSerializer,
    ChatSummarySerializer,
    MedicalInfoSerializer,
    EmailTokenObtainPairSerializer,
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


class MenstruationEntryViewSet(UserScopedViewSet):
    queryset = MenstruationEntry.objects.all()
    serializer_class = MenstruationEntrySerializer


class PregnancyEntryViewSet(UserScopedViewSet):
    queryset = PregnancyEntry.objects.all()
    serializer_class = PregnancyEntrySerializer


class MenopauseEntryViewSet(UserScopedViewSet):
    queryset = MenopauseEntry.objects.all()
    serializer_class = MenopauseEntrySerializer


class DoctorViewSet(UserScopedViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class MoodEntryViewSet(UserScopedViewSet):
    queryset = MoodEntry.objects.all()
    serializer_class = MoodEntrySerializer


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
        info, _ = MedicalInfo.objects.get_or_create(
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