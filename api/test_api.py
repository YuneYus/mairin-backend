from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from django.test import TestCase
from rest_framework.test import APIClient

from api.models import DailyLog, DailyLogSymptom, Symptom


class AuthAndProfileCompatibilityTests(TestCase):
    """Las rutas que usa la app actual (registro, token, perfil, doctores) mantienen su formato."""

    def setUp(self):
        self.client = APIClient()
        response = self.client.post(
            "/register/",
            {
                "username": "ana@test.com", "email": "ana@test.com", "password": "Clave-Segura-123",
                "name": "Ana", "last_name": "López", "birth_date": "1990-05-15",
            },
            format="multipart",
        )
        self.assertEqual(response.status_code, 201, response.content)
        tokens = self.client.post(
            "/api/token/", {"email": "ana@test.com", "password": "Clave-Segura-123"}, format="multipart"
        ).json()
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_profile_exposes_user_names_and_accepts_creole(self):
        profile = self.client.get("/profile/").json()
        self.assertEqual(profile["first_name"], "Ana")
        self.assertEqual(profile["last_name"], "López")
        self.assertEqual(profile["email"], "ana@test.com")
        self.assertEqual(profile["birth_date"], "1990-05-15")

        response = self.client.patch("/profile/", {"first_name": "Ana María", "app_language": "en"}, format="json")
        self.assertEqual(response.status_code, 200, response.content)
        self.assertEqual(User.objects.get(email="ana@test.com").first_name, "Ana María")
        self.assertEqual(response.json()["app_language"], "en")

    def test_doctor_crud_returns_created_at(self):
        payload = {"name": "Dra. Ruiz", "professionalism": "Ginecóloga", "phonenumber": "123", "details": ""}
        created = self.client.post("/api/doctors/", payload, format="json")
        self.assertEqual(created.status_code, 201, created.content)
        self.assertIn("created_at", created.json())
        doctor_id = created.json()["id"]
        self.assertEqual(
            self.client.put(f"/api/doctors/{doctor_id}/", {**payload, "name": "Dra. R"}, format="json").status_code, 200
        )
        self.assertEqual(self.client.delete(f"/api/doctors/{doctor_id}/").status_code, 204)


class HealthDataApiTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana@test.com", "ana@test.com", "x")
        self.eva = User.objects.create_user("eva@test.com", "eva@test.com", "x")
        self.client = APIClient()
        self.client.force_authenticate(self.ana)

    def test_symptom_catalog_is_seeded(self):
        codes = [s["code"] for s in self.client.get("/api/symptoms/").json()]
        self.assertEqual(len(codes), 20)
        self.assertIn("hot_flashes", codes)

    def test_daily_log_with_catalog_and_custom_symptoms(self):
        response = self.client.post(
            "/api/daily-logs/",
            {
                "date": "2026-10-20", "stage": "embarazo", "mood": "good", "baby_movement": True,
                "symptoms": [{"code": "nausea"}, {"custom_label": "Calambres"}, {"code": "nausea"}],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        body = response.json()
        self.assertEqual(
            {(s["code"], s["custom_label"]) for s in body["symptoms"]},
            {(None, "Calambres"), ("nausea", "")},
        )
        self.assertEqual(len(body["symptoms"]), 2)  # el "nausea" repetido se guarda una sola vez

        # Actualizar sin `symptoms` conserva los síntomas; con `symptoms` los reemplaza.
        url = f"/api/daily-logs/{body['id']}/"
        self.client.patch(url, {"notes": "todo bien"}, format="json")
        self.assertEqual(DailyLogSymptom.objects.count(), 2)
        self.client.patch(url, {"symptoms": [{"code": "headache"}]}, format="json")
        self.assertEqual(
            list(DailyLogSymptom.objects.values_list("symptom__code", flat=True)), ["headache"]
        )

    def test_daily_log_validation_errors_are_400(self):
        self.client.post("/api/daily-logs/", {"date": "2026-10-20", "stage": "menstruacion"}, format="json")
        duplicate = self.client.post("/api/daily-logs/", {"date": "2026-10-20", "stage": "menstruacion"}, format="json")
        self.assertEqual(duplicate.status_code, 400)
        both = self.client.post(
            "/api/daily-logs/",
            {"date": "2026-10-21", "stage": "menstruacion", "symptoms": [{"code": "cramps", "custom_label": "x"}]},
            format="json",
        )
        self.assertEqual(both.status_code, 400)
        unknown = self.client.post(
            "/api/daily-logs/",
            {"date": "2026-10-22", "stage": "menstruacion", "symptoms": [{"code": "no_existe"}]},
            format="json",
        )
        self.assertEqual(unknown.status_code, 400)

    def test_users_cannot_see_each_others_data(self):
        log = DailyLog.objects.create(user=self.eva, date="2026-10-20", stage="menstruacion")
        self.assertEqual(self.client.get("/api/daily-logs/").json(), [])
        self.assertEqual(self.client.get(f"/api/daily-logs/{log.pk}/").status_code, 404)
        # La misma fecha sí está libre para otra usuaria.
        response = self.client.post("/api/daily-logs/", {"date": "2026-10-20", "stage": "menstruacion"}, format="json")
        self.assertEqual(response.status_code, 201)

    def test_medical_info_nested_lists_are_replaced(self):
        response = self.client.put(
            "/medical-info/",
            {
                "height_cm": "160.5", "blood_type": "O+", "menstrual_pain_level": 3,
                "surgeries": [{"reason": "Parto", "performed_on": "2020-02-01"}],
                "usual_symptoms": [
                    {"stage": "menstruacion", "code": "cramps"},
                    {"stage": "menopausia", "custom_label": "Rodilla"},
                ],
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200, response.content)
        body = self.client.get("/medical-info/").json()
        self.assertEqual(body["height_cm"], "160.5")
        self.assertEqual(len(body["surgeries"]), 1)
        self.assertEqual(len(body["usual_symptoms"]), 2)

        bad = self.client.patch("/medical-info/", {"menstrual_pain_level": 7, "blood_type": "Z"}, format="json")
        self.assertEqual(bad.status_code, 400)
        self.assertEqual(set(bad.json()), {"menstrual_pain_level", "blood_type"})

    def test_reminders_myths_and_chat_summaries(self):
        reminder = self.client.post(
            "/api/reminders/",
            {"kind": "supplement", "name": "Calcio", "scheduled_at": "2026-10-21T08:00:00-06:00", "reminder_offset": "1hour"},
            format="json",
        )
        self.assertEqual(reminder.status_code, 201, reminder.content)
        myth = {"date": "2026-10-20", "flashcard_id": 4, "answered_true": False}
        self.assertEqual(self.client.post("/api/myths/", myth, format="json").status_code, 201)
        self.assertEqual(self.client.post("/api/myths/", myth, format="json").status_code, 400)
        summary = {"date": "2026-10-20", "text": "Hoy me sentí bien"}
        self.assertEqual(self.client.post("/api/chat-summaries/", summary, format="json").status_code, 201)


class ConstraintTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana@test.com", "ana@test.com", "x")
        self.log = DailyLog.objects.create(user=self.user, date="2026-10-20", stage="menstruacion")

    def assert_integrity_error(self, **kwargs):
        with self.assertRaises(IntegrityError), transaction.atomic():
            DailyLogSymptom.objects.create(daily_log=self.log, **kwargs)

    def test_symptom_must_be_catalog_xor_custom(self):
        cramps = Symptom.objects.get(code="cramps")
        self.assert_integrity_error(symptom=cramps, custom_label="x")
        self.assert_integrity_error(symptom=None, custom_label="")

    def test_one_daily_log_per_user_and_day(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            DailyLog.objects.create(user=self.user, date="2026-10-20", stage="embarazo")
