

from django.contrib import admin
from .models import (
    Profile, MenstruationEntry, PregnancyEntry, Appointment,
    MenopauseEntry, Supplement, Doctor, MoodEntry, MythAnswer,
    ChatSummary, MedicalInfo, Cirugia,
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