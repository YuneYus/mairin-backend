

from django.db import models
from django.contrib.auth.models import User


class Profile(models.Model):
    HEALTH_STAGE_CHOICES = [
        ("menstruacion", "Menstruación"),
        ("embarazo", "Embarazo"),
        ("menopausia", "Menopausia"),
    ]
    ACCOUNT_TYPE_CHOICES = [
        ("guest", "Guest"),
        ("registered", "Registered"),
    ]
    APP_LANGUAGE_CHOICES = [("es", "Español"), ("mis", "Miskito")]
    AUDIO_LANGUAGE_CHOICES = [("es", "Español"), ("none", "None")]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    first_name = models.CharField(max_length=100, blank=True)
    last_name = models.CharField(max_length=100, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    photo_uri = models.TextField(blank=True)

    health_stage = models.CharField(max_length=20, choices=HEALTH_STAGE_CHOICES, default="menstruacion")
    account_type = models.CharField(max_length=20, choices=ACCOUNT_TYPE_CHOICES, default="guest")
    onboarding_complete = models.BooleanField(default=False)
    pregnancy_week = models.PositiveSmallIntegerField(null=True, blank=True)
    cycle_reset_date = models.DateField(null=True, blank=True)

    app_language = models.CharField(max_length=10, choices=APP_LANGUAGE_CHOICES, default="es")
    audio_language = models.CharField(max_length=10, choices=AUDIO_LANGUAGE_CHOICES, default="es")

    def __str__(self):
        return f"Profile({self.user.username})"


class MenstruationEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="menstruation_entries")
    date = models.DateField()
    period = models.BooleanField(default=False)
    exercise = models.BooleanField(default=False)
    mood = models.CharField(max_length=10, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class PregnancyEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="pregnancy_entries")
    date = models.DateField()
    baby_movement = models.BooleanField(default=False)
    doctor_appointment = models.BooleanField(default=False)
    symptoms = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class Appointment(models.Model):
    pregnancy_entry = models.ForeignKey(PregnancyEntry, on_delete=models.CASCADE, related_name="appointments")
    name = models.CharField(max_length=200, blank=True)
    time = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    reminder_offset = models.CharField(max_length=20, blank=True)
    notification_id = models.CharField(max_length=100, blank=True)


class MenopauseEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="menopause_entries")
    date = models.DateField()
    exercise = models.BooleanField(default=False)
    symptoms = models.JSONField(default=list, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "date")

    def __str__(self):
        return f"{self.user.username} - {self.date}"


class Supplement(models.Model):
    menopause_entry = models.ForeignKey(MenopauseEntry, on_delete=models.CASCADE, related_name="supplements")
    name = models.CharField(max_length=200, blank=True)
    time = models.DateTimeField(null=True, blank=True)
    description = models.TextField(blank=True)
    reminder_offset = models.CharField(max_length=20, blank=True)
    notification_id = models.CharField(max_length=100, blank=True)


class Doctor(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="doctors")
    name = models.CharField(max_length=200)
    professionalism = models.CharField(max_length=200, blank=True)
    phonenumber = models.CharField(max_length=30, blank=True)
    details = models.TextField(blank=True)

    def __str__(self):
        return self.name


class MoodEntry(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="mood_entries")
    date = models.DateField()
    emoji = models.CharField(max_length=10)

    class Meta:
        unique_together = ("user", "date")


class MythAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="myth_answers")
    date = models.DateField()
    answered_true = models.BooleanField()

    class Meta:
        unique_together = ("user", "date")


class ChatSummary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="chat_summaries")
    date = models.DateField()
    text = models.TextField(blank=True)

    class Meta:
        unique_together = ("user", "date")


class MedicalInfo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="medical_info")
    full_name = models.CharField(max_length=200, blank=True)
    birth_date = models.CharField(max_length=20, blank=True)
    height = models.CharField(max_length=20, blank=True)
    weight = models.CharField(max_length=20, blank=True)
    blood_type = models.CharField(max_length=10, blank=True)
    occupation = models.CharField(max_length=200, blank=True)
    city = models.CharField(max_length=200, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    insurance = models.CharField(max_length=200, blank=True)
    email = models.CharField(max_length=200, blank=True)
    emergency_name = models.CharField(max_length=200, blank=True)
    emergency_phone = models.CharField(max_length=30, blank=True)
    current_illnesses = models.TextField(blank=True)
    first_period_age = models.CharField(max_length=10, blank=True)
    cycle_duration = models.CharField(max_length=20, blank=True)
    bleeding_duration = models.CharField(max_length=20, blank=True)
    pain_level = models.CharField(max_length=100, blank=True)
    menstrual_symptoms = models.JSONField(default=list, blank=True)
    pregnancy_count = models.CharField(max_length=10, blank=True)
    pregnancy_symptoms = models.JSONField(default=list, blank=True)
    menopause_symptoms = models.JSONField(default=list, blank=True)
    medications = models.TextField(blank=True)
    allergies = models.TextField(blank=True)


class Cirugia(models.Model):
    medical_info = models.ForeignKey(MedicalInfo, on_delete=models.CASCADE, related_name="cirugias")
    reason = models.CharField(max_length=200, blank=True)
    date = models.CharField(max_length=20, blank=True)