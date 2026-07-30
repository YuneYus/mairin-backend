

from rest_framework import viewsets, generics, permissions
from rest_framework.response import Response
from django.contrib.auth.models import User
from .models import (
    Profile, MenstruationEntry, PregnancyEntry,
    MenopauseEntry, Doctor, MoodEntry, MythAnswer,
    ChatSummary, MedicalInfo,
)
from .serializers import (
    RegisterSerializer, ProfileSerializer, MenstruationEntrySerializer,
    PregnancyEntrySerializer, MenopauseEntrySerializer, DoctorSerializer,
    MoodEntrySerializer, MythAnswerSerializer, ChatSummarySerializer,
    MedicalInfoSerializer,
)


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(user=self.request.user)
        return profile


class UserScopedViewSet(viewsets.ModelViewSet):
    """Base class: every queryset is automatically filtered to request.user,
    and new objects are automatically saved under request.user."""

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

    def get_object(self):
        info, _ = MedicalInfo.objects.get_or_create(user=self.request.user)
        return info