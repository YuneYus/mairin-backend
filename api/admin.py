from django.contrib import admin
from .models import (
    AppRelease,
    ChatSummary,
    DailyLog,
    DailyLogSymptom,
    Doctor,
    MedicalInfo,
    MedicalInfoSymptom,
    MythAnswer,
    Profile,
    Reminder,
    Surgery,
    Symptom,
)


class DailyLogSymptomInline(admin.TabularInline):
    model = DailyLogSymptom
    extra = 0


@admin.register(DailyLog)
class DailyLogAdmin(admin.ModelAdmin):
    list_display = ("user", "date", "stage", "mood", "period", "exercise")
    list_filter = ("stage",)
    search_fields = ("user__email",)
    inlines = [DailyLogSymptomInline]


class SurgeryInline(admin.TabularInline):
    model = Surgery
    extra = 0


class MedicalInfoSymptomInline(admin.TabularInline):
    model = MedicalInfoSymptom
    extra = 0


@admin.register(MedicalInfo)
class MedicalInfoAdmin(admin.ModelAdmin):
    list_display = ("user", "blood_type", "updated_at")
    search_fields = ("user__email",)
    inlines = [SurgeryInline, MedicalInfoSymptomInline]


@admin.register(Reminder)
class ReminderAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "name", "scheduled_at")
    list_filter = ("kind",)


@admin.register(Symptom)
class SymptomAdmin(admin.ModelAdmin):
    list_display = ("code", "for_menstruation", "for_pregnancy", "for_menopause", "sort_order")


admin.site.register(Profile)
admin.site.register(Doctor)
admin.site.register(MythAnswer)
admin.site.register(ChatSummary)


@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ("version", "uploaded_at")
    readonly_fields = ("uploaded_at",)
