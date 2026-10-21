from django.db import migrations

# (código, menstruación, embarazo, menopausia)
SYMPTOMS = [
    ("cramps", True, False, False),
    ("headache", True, True, True),
    ("fatigue", True, True, True),
    ("back_pain", True, True, False),
    ("bloating", True, False, False),
    ("nausea", True, True, False),
    ("dizziness", True, True, True),
    ("mood_swings", True, True, True),
    ("cravings", True, False, False),
    ("sleep_problems", True, False, True),
    ("diarrhea", True, False, False),
    ("constipation", True, False, False),
    ("leg_pain", True, False, False),
    ("heavy_bleeding", True, False, False),
    ("spotting", True, False, False),
    ("heartburn", False, True, False),
    ("swollen_feet", False, True, False),
    ("hot_flashes", False, False, True),
    ("night_sweats", False, False, True),
    ("joint_pain", False, False, True),
]


def seed(apps, schema_editor):
    Symptom = apps.get_model("api", "Symptom")
    for order, (code, menstruation, pregnancy, menopause) in enumerate(SYMPTOMS):
        Symptom.objects.update_or_create(
            code=code,
            defaults={
                "for_menstruation": menstruation,
                "for_pregnancy": pregnancy,
                "for_menopause": menopause,
                "sort_order": order,
            },
        )


def unseed(apps, schema_editor):
    apps.get_model("api", "Symptom").objects.filter(code__in=[s[0] for s in SYMPTOMS]).delete()


class Migration(migrations.Migration):
    dependencies = [("api", "0004_redesign_add_new_schema")]

    operations = [migrations.RunPython(seed, unseed)]
