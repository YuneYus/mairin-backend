

from django.contrib import admin
from .models import (
    Profile, MenstruationEntry, PregnancyEntry, Appointment,
    MenopauseEntry, Supplement, Doctor, MoodEntry, MythAnswer,
    ChatSummary, MedicalInfo, Cirugia, AppRelease,
)

admin.site.register(Profile)
admin.site.register(MenstruationEntry)
admin.site.register(PregnancyEntry)
admin.site.register(Appointment)
admin.site.register(MenopauseEntry)
admin.site.register(Supplement)
admin.site.register(Doctor)
admin.site.register(MoodEntry)
admin.site.register(MythAnswer)
admin.site.register(ChatSummary)
admin.site.register(MedicalInfo)
admin.site.register(Cirugia)


@admin.register(AppRelease)
class AppReleaseAdmin(admin.ModelAdmin):
    list_display = ("version", "uploaded_at")
    readonly_fields = ("uploaded_at",)