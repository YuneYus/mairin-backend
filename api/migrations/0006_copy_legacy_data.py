"""Copia los datos de las tablas antiguas a las nuevas antes de borrarlas (0008).

- MenstruationEntry / PregnancyEntry / MenopauseEntry / MoodEntry -> DailyLog (+ DailyLogSymptom)
- Appointment / Supplement -> Reminder
- Textos de MedicalInfo -> campos numéricos, MedicalInfoSymptom y Profile/User
- Cirugia.date (texto) -> Cirugia.performed_on (fecha)
- Profile.first_name/last_name -> User; Profile.pregnancy_week -> Profile.pregnancy_start_date
"""

import re
import unicodedata
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation

from django.db import migrations
from django.utils import timezone


def normalize(text):
    text = unicodedata.normalize("NFKD", str(text)).encode("ascii", "ignore").decode()
    return re.sub(r"\s+", " ", text).strip().casefold()


# Etiquetas que la app guardó hasta ahora (identificadores del calendario, claves de traducción
# y textos traducidos en es / en / mis) -> código del catálogo.
_LABELS = {
    "cramps": ["colicos", "Cólicos (dolor en el abdomen)", "Cramps (pain in di abdomen)", "Batka painka"],
    "headache": [
        "dolorCabeza", "dolorCabezaEmbarazo", "doloresCabeza", "Dolor de cabeza", "Dolores de cabeza",
        "Headache", "Headaches", "Ulba painka",
    ],
    "fatigue": [
        "cansancio", "fatiga", "fatigaMenopausia", "fatigaCansancio", "Cansancio", "Fatiga/cansancio",
        "Tiredness", "Fatigue/tiredness", "Baha sutka",
    ],
    "back_pain": ["dolorEspalda", "dolorEspaldaEmbarazo", "Dolor de espalda", "Back pain", "Kum painka"],
    "bloating": [
        "hinchazon", "Hinchazón (sensación de inflamación abdominal)",
        "Bloating (feeling of abdominal swelling)", "Kabia wal sa",
    ],
    "nausea": ["nauseas", "nausea", "Nausea", "Náuseas", "Náusea"],
    "dizziness": ["mareos", "mareosEmbarazo", "mareosMenopausia", "Mareos", "Dizzy", "Wina luhpia"],
    "mood_swings": [
        "cambiosHumor", "cambiosHumorEmbarazo", "cambiosHumorMenopausia", "cambioHumor",
        "Cambios de humor", "Mood changes", "Laka yamni sakan",
    ],
    "cravings": ["antojos", "Antojos (deseo de ciertos alimentos)", "Cravings (desire fi certain foods)", "Manka plun ai"],
    "sleep_problems": [
        "pocoSueno", "problemasDormir", "problemaDormir", "Poco sueño", "Problemas para dormir",
        "Likkle sleep", "Trouble sleeping", "Sip kum ai",
    ],
    "diarrhea": ["diarrea", "Diarrea", "Diarrhea"],
    "constipation": ["estrenimiento", "Estreñimiento (dificultad para evacuar)", "Constipation (difficulty passing stool)", "Estreñimiento"],
    "leg_pain": ["dolorPiernas", "Dolor en las piernas", "Leg pain", "Tangka painka"],
    "heavy_bleeding": ["sangreAbundante", "Sangre abundante (mucha sangre)", "Heavy bleeding (nuff blood)", "Tara bila"],
    "spotting": ["manchado", "Manchado (pequeño sangrado menstrual)", "Spotting (light menstrual bleeding)", "Bila kum"],
    "heartburn": ["acidezEstomacal", "aceidezEstomacal", "Acidez estomacal", "Heartburn", "Kabia asan painka"],
    "swollen_feet": ["hinchazonPies", "Hinchazón de los pies", "Swollen feet", "Tangka kabia wal sa"],
    "hot_flashes": [
        "sofocos", "sofoco", "Sofocos (sensación repentina de calor en el cuerpo)",
        "Sofocos(sensación repentina de calor en el cuerpo)",
        "Hot flashes (sudden feeling of heat in di body)", "Bisi tara",
    ],
    "night_sweats": ["sudoresNocturnos", "sudonesNocturno", "Sudores nocturnos", "Night sweats", "Taya bila"],
    "joint_pain": ["dolorArticular", "Dolor articular (rodillas, muñecas, hombros, etc.)", "Wal painka"],
}
LABEL_TO_CODE = {normalize(code): code for code in _LABELS}
LABEL_TO_CODE.update({normalize(label): code for code, labels in _LABELS.items() for label in labels})

MOOD_TO_CODE = {
    "\U0001F60A": "very_happy", "muy_feliz": "very_happy",
    "\U0001F642": "good", "bien": "good",
    "\U0001F610": "neutral",
    "\U0001F971": "tired", "cansada": "tired",
    "\U0001F614": "sad", "triste": "sad",
    "\U0001F62D": "very_sad", "muy_triste": "very_sad",
    "\U0001F620": "angry", "\U0001F621": "angry", "enojada": "angry",
}

BLOOD_TYPES = {"A+", "A-", "B+", "B-", "AB+", "AB-", "O+", "O-"}
OFFSETS = {"5min", "10min", "1hour", "2hours", "1day", "2days", "1week", "none"}


def parse_numbers(text):
    return [float(n.replace(",", ".")) for n in re.findall(r"\d+(?:[.,]\d+)?", str(text or ""))]


def parse_int(text):
    """'29 días' -> 29, '5-7 días' -> 6 (promedio del rango), '' -> None."""
    numbers = parse_numbers(text)[:2]
    if not numbers:
        return None
    value = round(sum(numbers) / len(numbers))
    return value if 0 <= value <= 32767 else None


def parse_decimal(text, meters_to_cm=False):
    numbers = parse_numbers(text)
    if not numbers:
        return None
    value = numbers[0]
    if meters_to_cm and value < 3:  # "1.60" -> 160 cm
        value *= 100
    try:
        result = Decimal(str(round(value, 1)))
    except InvalidOperation:
        return None
    return result if Decimal("0") < result < Decimal("1000") else None


def parse_date(text):
    text = str(text or "").strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y", "%Y-%m-%d", "%d/%m/%y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    return None


def add_symptom(Model, Symptom, owner_kwargs, label, cache):
    label = str(label or "").strip()
    if not label:
        return
    code = LABEL_TO_CODE.get(normalize(label))
    if code:
        if code not in cache:
            cache[code] = Symptom.objects.get(code=code)
        Model.objects.get_or_create(symptom=cache[code], custom_label="", **owner_kwargs)
    else:
        Model.objects.get_or_create(symptom=None, custom_label=label[:100], **owner_kwargs)


def merge_log(DailyLog, user_id, day, stage, **values):
    log, created = DailyLog.objects.get_or_create(user_id=user_id, date=day, defaults={"stage": stage})
    for field in ("exercise", "period", "baby_movement", "doctor_appointment", "took_vitamins"):
        if values.get(field):
            setattr(log, field, True)
    mood = values.get("mood")
    if mood and not log.mood:
        log.mood = mood
    notes = (values.get("notes") or "").strip()
    if notes and notes not in log.notes:
        log.notes = f"{log.notes}\n{notes}".strip()
    log.save()
    return log


def copy_forward(apps, schema_editor):
    User = apps.get_model("auth", "User")
    Profile = apps.get_model("api", "Profile")
    Symptom = apps.get_model("api", "Symptom")
    DailyLog = apps.get_model("api", "DailyLog")
    DailyLogSymptom = apps.get_model("api", "DailyLogSymptom")
    Reminder = apps.get_model("api", "Reminder")
    MedicalInfo = apps.get_model("api", "MedicalInfo")
    MedicalInfoSymptom = apps.get_model("api", "MedicalInfoSymptom")
    Cirugia = apps.get_model("api", "Cirugia")
    symptom_cache = {}
    today = timezone.localdate()

    # Perfil: nombres al User, semana de embarazo -> fecha de inicio
    for profile in Profile.objects.all():
        user = User.objects.get(pk=profile.user_id)
        if not user.first_name and profile.first_name:
            user.first_name = profile.first_name
        if not user.last_name and profile.last_name:
            user.last_name = profile.last_name
        user.save(update_fields=["first_name", "last_name"])
        if profile.pregnancy_week and not profile.pregnancy_start_date:
            profile.pregnancy_start_date = today - timedelta(weeks=profile.pregnancy_week)
            profile.save(update_fields=["pregnancy_start_date"])

    # Registros diarios
    for entry in apps.get_model("api", "MenstruationEntry").objects.all():
        merge_log(
            DailyLog, entry.user_id, entry.date, "menstruacion",
            period=entry.period, exercise=entry.exercise,
            mood=MOOD_TO_CODE.get(entry.mood.strip(), ""), notes=entry.notes,
        )

    for entry in apps.get_model("api", "PregnancyEntry").objects.all():
        log = merge_log(
            DailyLog, entry.user_id, entry.date, "embarazo",
            baby_movement=entry.baby_movement, doctor_appointment=entry.doctor_appointment, notes=entry.notes,
        )
        for label in entry.symptoms or []:
            add_symptom(DailyLogSymptom, Symptom, {"daily_log": log}, label, symptom_cache)
        for appt in apps.get_model("api", "Appointment").objects.filter(pregnancy_entry=entry):
            Reminder.objects.create(
                user_id=entry.user_id, kind="appointment", name=appt.name, scheduled_at=appt.time,
                description=appt.description,
                reminder_offset=appt.reminder_offset if appt.reminder_offset in OFFSETS else "none",
            )

    for entry in apps.get_model("api", "MenopauseEntry").objects.all():
        log = merge_log(DailyLog, entry.user_id, entry.date, "menopausia", exercise=entry.exercise, notes=entry.notes)
        for label in entry.symptoms or []:
            add_symptom(DailyLogSymptom, Symptom, {"daily_log": log}, label, symptom_cache)
        for sup in apps.get_model("api", "Supplement").objects.filter(menopause_entry=entry):
            Reminder.objects.create(
                user_id=entry.user_id, kind="supplement", name=sup.name, scheduled_at=sup.time,
                description=sup.description,
                reminder_offset=sup.reminder_offset if sup.reminder_offset in OFFSETS else "none",
            )

    stages = dict(Profile.objects.values_list("user_id", "health_stage"))
    for entry in apps.get_model("api", "MoodEntry").objects.all():
        merge_log(
            DailyLog, entry.user_id, entry.date, stages.get(entry.user_id, "menstruacion"),
            mood=MOOD_TO_CODE.get(entry.emoji.strip(), ""),
        )

    # Historial médico
    stage_lists = (
        ("menstruacion", "menstrual_symptoms"),
        ("embarazo", "pregnancy_symptoms"),
        ("menopausia", "menopause_symptoms"),
    )
    for info in MedicalInfo.objects.all():
        info.height_cm = parse_decimal(info.height, meters_to_cm=True)
        info.weight_kg = parse_decimal(info.weight)
        info.age_at_first_period = parse_int(info.first_period_age)
        info.cycle_length_days = parse_int(info.cycle_duration)
        info.bleeding_days = parse_int(info.bleeding_duration)
        pain = parse_numbers(info.pain_level)
        info.menstrual_pain_level = int(pain[0]) if pain and 1 <= pain[0] <= 5 else None
        info.pregnancies = parse_int(info.pregnancy_count)
        blood = info.blood_type.replace(" ", "").upper()
        info.blood_type = blood if blood in BLOOD_TYPES else ""
        info.save()

        for stage, field in stage_lists:
            for label in getattr(info, field) or []:
                add_symptom(
                    MedicalInfoSymptom, Symptom, {"medical_info": info, "stage": stage}, label, symptom_cache
                )

        # Datos personales repetidos en el historial -> perfil, solo si allí faltan
        profile, _ = Profile.objects.get_or_create(user_id=info.user_id)
        user = User.objects.get(pk=info.user_id)
        if info.phone and not profile.phone:
            profile.phone = info.phone
        birth = parse_date(info.birth_date)
        if birth and not profile.birth_date:
            profile.birth_date = birth
        profile.save(update_fields=["phone", "birth_date"])
        if info.full_name and not (user.first_name or user.last_name):
            first, _, last = info.full_name.strip().partition(" ")
            user.first_name, user.last_name = first[:150], last[:150]
            user.save(update_fields=["first_name", "last_name"])

    for surgery in Cirugia.objects.all():
        surgery.performed_on = parse_date(surgery.date)
        surgery.save(update_fields=["performed_on"])


class Migration(migrations.Migration):
    dependencies = [("api", "0005_seed_symptoms")]

    operations = [migrations.RunPython(copy_forward, migrations.RunPython.noop)]
