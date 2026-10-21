from django.contrib.auth.models import User
from django.db import transaction
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import (
    ChatSummary,
    DailyLog,
    DailyLogSymptom,
    Doctor,
    HEALTH_STAGE_CHOICES,
    MedicalInfo,
    MedicalInfoSymptom,
    MythAnswer,
    Profile,
    Reminder,
    Surgery,
    Symptom,
)


class EmailTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = User.EMAIL_FIELD


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(source="first_name", required=True)
    last_name = serializers.CharField(required=True)
    birth_date = serializers.DateField(source="profile.birth_date", required=False, allow_null=True)

    class Meta:
        model = User
        fields = ["email", "password", "name", "last_name", "birth_date"]

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        profile_data = validated_data.pop("profile", {})
        email = validated_data["email"]
        user = User.objects.create_user(
            username=email,
            email=email,
            password=validated_data["password"],
            first_name=validated_data["first_name"],
            last_name=validated_data["last_name"],
        )
        Profile.objects.create(user=user, **profile_data)
        return user


class ProfileSerializer(serializers.ModelSerializer):
    # Nombre, apellido y correo se guardan en User; se exponen aquí para que la app los lea en un solo lugar.
    first_name = serializers.CharField(source="user.first_name", required=False, allow_blank=True)
    last_name = serializers.CharField(source="user.last_name", required=False, allow_blank=True)
    email = serializers.EmailField(source="user.email", read_only=True)

    class Meta:
        model = Profile
        exclude = ["user"]

    def update(self, instance, validated_data):
        user_data = validated_data.pop("user", {})
        if user_data:
            for field, value in user_data.items():
                setattr(instance.user, field, value)
            instance.user.save(update_fields=list(user_data))
        return super().update(instance, validated_data)


class UniquePerUserDateMixin:
    """Devuelve 400 (no 500) si ya existe un registro de la usuaria para esa fecha."""

    def validate(self, attrs):
        attrs = super().validate(attrs)
        day = attrs.get("date", getattr(self.instance, "date", None))
        request = self.context.get("request")
        if request and day:
            existing = self.Meta.model.objects.filter(user=request.user, date=day)
            if self.instance is not None:
                existing = existing.exclude(pk=self.instance.pk)
            if existing.exists():
                raise serializers.ValidationError({"date": "Ya existe un registro para esta fecha."})
        return attrs


class SymptomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Symptom
        fields = ["code", "for_menstruation", "for_pregnancy", "for_menopause", "sort_order"]


class SymptomChoiceSerializer(serializers.Serializer):
    """Un síntoma elegido: `code` del catálogo o `custom_label` escrito por la usuaria (no ambos)."""

    code = serializers.SlugRelatedField(
        source="symptom", slug_field="code", queryset=Symptom.objects.all(),
        required=False, allow_null=True,
    )
    custom_label = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")

    def validate(self, attrs):
        has_code = attrs.get("symptom") is not None
        has_custom = bool(attrs.get("custom_label", "").strip())
        if has_code == has_custom:
            raise serializers.ValidationError("Indica `code` o `custom_label`, uno de los dos.")
        attrs["custom_label"] = attrs.get("custom_label", "").strip()
        return attrs


def _unique_choices(items, key):
    seen, result = set(), []
    for item in items:
        identity = key(item)
        if identity not in seen:
            seen.add(identity)
            result.append(item)
    return result


class DailyLogSerializer(UniquePerUserDateMixin, serializers.ModelSerializer):
    symptoms = SymptomChoiceSerializer(many=True, required=False)

    class Meta:
        model = DailyLog
        exclude = ["user"]

    def _save_symptoms(self, log, symptoms):
        log.symptoms.all().delete()
        symptoms = _unique_choices(symptoms, lambda s: (s.get("symptom"), s["custom_label"]))
        DailyLogSymptom.objects.bulk_create(
            DailyLogSymptom(daily_log=log, symptom=s.get("symptom"), custom_label=s["custom_label"])
            for s in symptoms
        )

    @transaction.atomic
    def create(self, validated_data):
        symptoms = validated_data.pop("symptoms", [])
        log = super().create(validated_data)
        self._save_symptoms(log, symptoms)
        return log

    @transaction.atomic
    def update(self, instance, validated_data):
        symptoms = validated_data.pop("symptoms", None)
        log = super().update(instance, validated_data)
        if symptoms is not None:  # sin `symptoms` en la petición se conservan los actuales
            self._save_symptoms(log, symptoms)
        return log


class ReminderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reminder
        exclude = ["user"]


class DoctorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Doctor
        exclude = ["user"]


class MythAnswerSerializer(UniquePerUserDateMixin, serializers.ModelSerializer):
    class Meta:
        model = MythAnswer
        exclude = ["user"]


class ChatSummarySerializer(UniquePerUserDateMixin, serializers.ModelSerializer):
    class Meta:
        model = ChatSummary
        exclude = ["user"]


class SurgerySerializer(serializers.ModelSerializer):
    class Meta:
        model = Surgery
        fields = ["id", "reason", "performed_on"]


class UsualSymptomSerializer(SymptomChoiceSerializer):
    stage = serializers.ChoiceField(choices=HEALTH_STAGE_CHOICES)


class MedicalInfoSerializer(serializers.ModelSerializer):
    surgeries = SurgerySerializer(many=True, required=False)
    usual_symptoms = UsualSymptomSerializer(many=True, required=False)

    class Meta:
        model = MedicalInfo
        exclude = ["user"]

    @transaction.atomic
    def update(self, instance, validated_data):
        surgeries = validated_data.pop("surgeries", None)
        usual_symptoms = validated_data.pop("usual_symptoms", None)
        info = super().update(instance, validated_data)
        # Las listas anidadas se reemplazan completas cuando vienen en la petición.
        if surgeries is not None:
            info.surgeries.all().delete()
            Surgery.objects.bulk_create(Surgery(medical_info=info, **s) for s in surgeries)
        if usual_symptoms is not None:
            info.usual_symptoms.all().delete()
            usual_symptoms = _unique_choices(
                usual_symptoms, lambda s: (s["stage"], s.get("symptom"), s["custom_label"])
            )
            MedicalInfoSymptom.objects.bulk_create(
                MedicalInfoSymptom(
                    medical_info=info, stage=s["stage"], symptom=s.get("symptom"), custom_label=s["custom_label"]
                )
                for s in usual_symptoms
            )
        return info
