

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Profile, MenstruationEntry, PregnancyEntry, Appointment,
    MenopauseEntry, Supplement, Doctor, MoodEntry, MythAnswer,
    ChatSummary, MedicalInfo, Cirugia,
)


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password"]

    def create(self, validated_data):
        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data.get("email", ""),
            password=validated_data["password"],
        )
        Profile.objects.create(user=user)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        exclude = ["user"]


class AppointmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        exclude = ["pregnancy_entry"]


class PregnancyEntrySerializer(serializers.ModelSerializer):
    appointments = AppointmentSerializer(many=True, required=False)

    class Meta:
        model = PregnancyEntry
        exclude = ["user"]

    def create(self, validated_data):
        appointments_data = validated_data.pop("appointments", [])
        entry = PregnancyEntry.objects.create(
            user=self.context["request"].user, **validated_data
        )
        for appt in appointments_data:
            Appointment.objects.create(pregnancy_entry=entry, **appt)
        return entry


class SupplementSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplement
        exclude = ["menopause_entry"]


class MenopauseEntrySerializer(serializers.ModelSerializer):
    supplements = SupplementSerializer(many=True, required=False)

    class Meta:
        model = MenopauseEntry
        exclude = ["user"]

    def create(self, validated_data):
        supplements_data = validated_data.pop("supplements", [])
        entry = MenopauseEntry.objects.create(
            user=self.context["request"].user, **validated_data
        )
        for sup in supplements_data:
            Supplement.objects.create(menopause_entry=entry, **sup)
        return entry


class MenstruationEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MenstruationEntry
        exclude = ["user"]


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        exclude = ["user"]


class MoodEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodEntry
        exclude = ["user"]


class MythAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MythAnswer
        exclude = ["user"]


class ChatSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatSummary
        exclude = ["user"]


class CirugiaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cirugia
        exclude = ["medical_info"]


class MedicalInfoSerializer(serializers.ModelSerializer):
    cirugias = CirugiaSerializer(many=True, required=False)

    class Meta:
        model = MedicalInfo
        exclude = ["user"]

    def create(self, validated_data):
        cirugias_data = validated_data.pop("cirugias", [])
        info = MedicalInfo.objects.create(
            user=self.context["request"].user, **validated_data
        )
        for c in cirugias_data:
            Cirugia.objects.create(medical_info=info, **c)
        return info