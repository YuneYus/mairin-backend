from datetime import date, datetime, timedelta
from decimal import Decimal

from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.test import TransactionTestCase
from django.utils import timezone


class LegacyDataMigrationTests(TransactionTestCase):
    """Migra una base con el esquema antiguo (0003) y comprueba que los datos llegan al nuevo."""

    migrate_from = [("api", "0003_apprelease")]
    migrate_to = [("api", "0008_redesign_drop_legacy")]

    def setUp(self):
        executor = MigrationExecutor(connection)
        executor.migrate(self.migrate_from)
        self.create_legacy_data(executor.loader.project_state(self.migrate_from).apps)

        executor = MigrationExecutor(connection)
        executor.loader.build_graph()
        executor.migrate(self.migrate_to)
        self.apps = executor.loader.project_state(self.migrate_to).apps

    def create_legacy_data(self, apps):
        User = apps.get_model("auth", "User")
        user = User.objects.create(username="ana@test.com", email="ana@test.com")
        self.user_id = user.pk
        apps.get_model("api", "Profile").objects.create(
            user=user, first_name="Ana", last_name="López", pregnancy_week=10,
            cycle_reset_date=date(2026, 9, 1), account_type="registered",
        )

        apps.get_model("api", "MenstruationEntry").objects.create(
            user=user, date=date(2026, 10, 1), period=True, mood="\U0001F60A", notes="nota menstruación",
        )
        pregnancy = apps.get_model("api", "PregnancyEntry").objects.create(
            user=user, date=date(2026, 10, 1), baby_movement=True,
            symptoms=["Nausea", "Algo raro", "Nausea"], notes="nota embarazo",
        )
        apps.get_model("api", "Appointment").objects.create(
            pregnancy_entry=pregnancy, name="Control", reminder_offset="1day",
            time=timezone.make_aware(datetime(2026, 10, 5, 9, 0)),
        )
        menopause = apps.get_model("api", "MenopauseEntry").objects.create(
            user=user, date=date(2026, 10, 3), exercise=True, symptoms=["Sudores nocturnos"],
        )
        apps.get_model("api", "Supplement").objects.create(
            menopause_entry=menopause, name="Calcio", reminder_offset="raro",
        )
        apps.get_model("api", "MoodEntry").objects.create(user=user, date=date(2026, 10, 2), emoji="\U0001F62D")

        info = apps.get_model("api", "MedicalInfo").objects.create(
            user=user, full_name="Ana López", phone="8888-0000", birth_date="15/05/1990",
            height="1.60", weight="58kg", blood_type=" o+ ", bleeding_duration="5-7 días",
            cycle_duration="29 días", first_period_age="12", pain_level="3 - Moderado (Puede requerir descanso)",
            pregnancy_count="2", menstrual_symptoms=["Cólicos (dolor en el abdomen)", "Me duele la rodilla"],
            menopause_symptoms=["Trouble sleeping"],
        )
        apps.get_model("api", "Cirugia").objects.create(medical_info=info, reason="Parto", date="01/02/2020")
        apps.get_model("api", "Cirugia").objects.create(medical_info=info, reason="Otra", date="hace años")

    def test_profile_data_moves_to_user_and_dates(self):
        user = self.apps.get_model("auth", "User").objects.get(pk=self.user_id)
        profile = self.apps.get_model("api", "Profile").objects.get(user_id=self.user_id)
        self.assertEqual((user.first_name, user.last_name), ("Ana", "López"))
        self.assertEqual(profile.pregnancy_start_date, timezone.localdate() - timedelta(weeks=10))
        self.assertEqual(profile.cycle_tracking_start, date(2026, 9, 1))
        self.assertEqual(profile.phone, "8888-0000")
        self.assertEqual(profile.birth_date, date(1990, 5, 15))

    def test_entries_merge_into_one_daily_log_per_day(self):
        DailyLog = self.apps.get_model("api", "DailyLog")
        logs = {log.date: log for log in DailyLog.objects.filter(user_id=self.user_id)}
        self.assertEqual(set(logs), {date(2026, 10, 1), date(2026, 10, 2), date(2026, 10, 3)})

        merged = logs[date(2026, 10, 1)]
        self.assertTrue(merged.period and merged.baby_movement)
        self.assertEqual(merged.mood, "very_happy")
        self.assertIn("nota menstruación", merged.notes)
        self.assertIn("nota embarazo", merged.notes)
        symptoms = {(s.symptom.code if s.symptom_id else None, s.custom_label) for s in merged.symptoms.all()}
        self.assertEqual(symptoms, {("nausea", ""), (None, "Algo raro")})

        self.assertEqual(logs[date(2026, 10, 2)].mood, "very_sad")
        self.assertEqual(logs[date(2026, 10, 3)].stage, "menopausia")
        self.assertEqual(logs[date(2026, 10, 3)].symptoms.get().symptom.code, "night_sweats")

    def test_appointments_and_supplements_become_reminders(self):
        reminders = {r.kind: r for r in self.apps.get_model("api", "Reminder").objects.filter(user_id=self.user_id)}
        self.assertEqual(reminders["appointment"].name, "Control")
        self.assertEqual(reminders["appointment"].reminder_offset, "1day")
        self.assertEqual(reminders["supplement"].name, "Calcio")
        self.assertEqual(reminders["supplement"].reminder_offset, "none")

    def test_medical_info_text_becomes_typed_fields(self):
        info = self.apps.get_model("api", "MedicalInfo").objects.get(user_id=self.user_id)
        self.assertEqual(info.height_cm, Decimal("160.0"))
        self.assertEqual(info.weight_kg, Decimal("58.0"))
        self.assertEqual(info.blood_type, "O+")
        self.assertEqual(info.bleeding_days, 6)
        self.assertEqual(info.cycle_length_days, 29)
        self.assertEqual(info.age_at_first_period, 12)
        self.assertEqual(info.menstrual_pain_level, 3)
        self.assertEqual(info.pregnancies, 2)

        usual = {
            (s.stage, s.symptom.code if s.symptom_id else None, s.custom_label) for s in info.usual_symptoms.all()
        }
        self.assertEqual(
            usual,
            {
                ("menstruacion", "cramps", ""),
                ("menstruacion", None, "Me duele la rodilla"),
                ("menopausia", "sleep_problems", ""),
            },
        )
        surgeries = {s.reason: s.performed_on for s in info.surgeries.all()}
        self.assertEqual(surgeries, {"Parto": date(2020, 2, 1), "Otra": None})
