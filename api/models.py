from django.contrib.auth.models import User
from django.core.validators import FileExtensionValidator, MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

HEALTH_STAGE_CHOICES = [
    ("menstruacion", "Menstruación"),
    ("embarazo", "Embarazo"),
    ("menopausia", "Menopausia"),
]


class Profile(models.Model):
    """Datos de la usuaria que no están en User (nombre, apellido y correo viven en User)."""

    HEALTH_STAGE_CHOICES = HEALTH_STAGE_CHOICES
    APP_LANGUAGE_CHOICES = [("es", "Español"), ("mis", "Miskito"), ("en", "Criollo")]
    AUDIO_LANGUAGE_CHOICES = [("es", "Español"), ("none", "None")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    phone = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)

    health_stage = models.CharField(max_length=20, choices=HEALTH_STAGE_CHOICES, default="menstruacion")
    onboarding_complete = models.BooleanField(default=False)
    # Desde cuándo se cuentan los ciclos (la usuaria puede reiniciar el seguimiento).
    cycle_tracking_start = models.DateField(null=True, blank=True)
    # Fecha estimada de la última menstruación antes del embarazo: la semana se calcula a partir de ella.
    pregnancy_start_date = models.DateField(null=True, blank=True)

    app_language = models.CharField(max_length=10, choices=APP_LANGUAGE_CHOICES, default="es")
    audio_language = models.CharField(max_length=10, choices=AUDIO_LANGUAGE_CHOICES, default="es")

    def __str__(self):
        return f"Profile({self.user.username})"


class Doctor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doctors")
    name = models.CharField(max_length=200)
    professionalism = models.CharField(max_length=200, blank=True)
    phonenumber = models.CharField(max_length=30, blank=True)
    details = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name


class MythAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="myth_answers")
    date = models.DateField()
    flashcard_id = models.PositiveIntegerField(null=True, blank=True)
    answered_true = models.BooleanField()

    class Meta:
        unique_together = ("user", "date")


class ChatSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_summaries")
    date = models.DateField()
    text = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("user", "date")


class MedicalInfo(models.Model):
    """Historial médico. Los datos personales (nombre, teléfono, nacimiento) están en User/Profile."""

    BLOOD_TYPE_CHOICES = [(t, t) for t in ("A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="medical_info")
    occupation = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    insurance = models.CharField(max_length=200, blank=True)
    emergency_name = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(max_length=30, blank=True)

    height_cm = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPE_CHOICES, blank=True)
    current_illnesses = models.TextField(blank=True)

    age_at_first_period = models.PositiveSmallIntegerField(null=True, blank=True)
    cycle_length_days = models.PositiveSmallIntegerField(null=True, blank=True)
    bleeding_days = models.PositiveSmallIntegerField(null=True, blank=True)
    menstrual_pain_level = models.PositiveSmallIntegerField(
        null=True, blank=True, validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    pregnancies = models.PositiveSmallIntegerField(null=True, blank=True)

    medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)


class Surgery(models.Model):
    medical_info = models.ForeignKey(MedicalInfo, on_delete=models.CASCADE, related_name="surgeries")
    reason = models.CharField(max_length=200, blank=True)
    performed_on = models.DateField(null=True, blank=True)


class AppRelease(models.Model):
    version = models.CharField(max_length=40)
    apk = models.FileField(
        upload_to="app-releases/",
        validators=[FileExtensionValidator(["apk"])],
    )
    release_notes = models.TextField(blank=True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ("-uploaded_at", "-pk")
        verbose_name = "app release"
        verbose_name_plural = "app releases"

    def __str__(self):
        return f"Mairin {self.version}"


class Symptom(models.Model):
    """Catálogo fijo de síntomas. La app traduce cada código para mostrarlo."""

    code = models.SlugField(max_length=40, unique=True)
    for_menstruation = models.BooleanField(default=False)
    for_pregnancy = models.BooleanField(default=False)
    for_menopause = models.BooleanField(default=False)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ("sort_order", "code")

    def __str__(self):
        return self.code


class DailyLog(models.Model):
    """Un registro por usuaria y día, sea cual sea la etapa (reemplaza las entradas por etapa)."""

    MOOD_CHOICES = [
        ("very_happy", "😊"),
        ("good", "🙂"),
        ("neutral", "😐"),
        ("tired", "🥱"),
        ("sad", "😔"),
        ("very_sad", "😭"),
        ("angry", "😠"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="daily_logs")
    date = models.DateField()
    stage = models.CharField(max_length=20, choices=HEALTH_STAGE_CHOICES)
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES, blank=True)
    exercise = models.BooleanField(default=False)
    notes = models.TextField(blank=True)
    # Menstruación
    period = models.BooleanField(default=False)
    # Embarazo
    baby_movement = models.BooleanField(default=False)
    doctor_appointment = models.BooleanField(default=False)
    # Menopausia
    took_vitamins = models.BooleanField(default=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("-date",)
        constraints = [
            models.UniqueConstraint(fields=["user", "date"], name="dailylog_one_per_user_per_day"),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class DailyLogSymptom(models.Model):
    """Síntoma de un día: uno del catálogo o uno escrito por la usuaria (custom_label)."""

    daily_log = models.ForeignKey(DailyLog, on_delete=models.CASCADE, related_name="symptoms")
    symptom = models.ForeignKey(Symptom, on_delete=models.PROTECT, null=True, blank=True)
    custom_label = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(symptom__isnull=False) & Q(custom_label=""))
                | (Q(symptom__isnull=True) & ~Q(custom_label="")),
                name="dailylogsymptom_catalog_xor_custom",
            ),
            models.UniqueConstraint(
                fields=["daily_log", "symptom"],
                condition=Q(symptom__isnull=False),
                name="dailylogsymptom_unique_catalog",
            ),
            models.UniqueConstraint(
                fields=["daily_log", "custom_label"],
                condition=~Q(custom_label=""),
                name="dailylogsymptom_unique_custom",
            ),
        ]


class Reminder(models.Model):
    """Citas (embarazo) y suplementos (menopausia) con aviso."""

    KIND_CHOICES = [("appointment", "Cita"), ("supplement", "Suplemento")]
    OFFSET_CHOICES = [
        ("5min", "5 minutos antes"),
        ("10min", "10 minutos antes"),
        ("1hour", "1 hora antes"),
        ("2hours", "2 horas antes"),
        ("1day", "1 día antes"),
        ("2days", "2 días antes"),
        ("1week", "1 semana antes"),
        ("none", "Sin aviso"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="reminders")
    kind = models.CharField(max_length=20, choices=KIND_CHOICES)
    name = models.CharField(max_length=200, blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    reminder_offset = models.CharField(max_length=10, choices=OFFSET_CHOICES, default="none")
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ("scheduled_at",)

    def __str__(self):
        return f"{self.get_kind_display()}: {self.name}"


class MedicalInfoSymptom(models.Model):
    """Síntomas habituales del historial médico, separados por etapa."""

    medical_info = models.ForeignKey(MedicalInfo, on_delete=models.CASCADE, related_name="usual_symptoms")
    stage = models.CharField(max_length=20, choices=HEALTH_STAGE_CHOICES)
    symptom = models.ForeignKey(Symptom, on_delete=models.PROTECT, null=True, blank=True)
    custom_label = models.CharField(max_length=100, blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(Q(symptom__isnull=False) & Q(custom_label=""))
                | (Q(symptom__isnull=True) & ~Q(custom_label="")),
                name="medicalinfosymptom_catalog_xor_custom",
            ),
            models.UniqueConstraint(
                fields=["medical_info", "stage", "symptom"],
                condition=Q(symptom__isnull=False),
                name="medicalinfosymptom_unique_catalog",
            ),
            models.UniqueConstraint(
                fields=["medical_info", "stage", "custom_label"],
                condition=~Q(custom_label=""),
                name="medicalinfosymptom_unique_custom",
            ),
        ]

