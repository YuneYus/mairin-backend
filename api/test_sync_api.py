import uuid
from datetime import timedelta

from django.contrib.auth.models import User
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from api.exceptions import exception_handler
from api.models import DailyLog, Doctor


class DateKeyedResourceTests(TestCase):
    """Registros diarios, mitos y resúmenes se manejan por fecha: PUT crea o reemplaza."""

    def setUp(self):
        self.user = User.objects.create_user("ana@test.com", "ana@test.com", "x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)

    def test_put_by_date_creates_then_replaces(self):
        url = "/api/daily-logs/2026-10-20/"
        created = self.client.put(
            url, {"stage": "menstruacion", "period": True, "symptoms": [{"code": "cramps"}]}, format="json"
        )
        self.assertEqual(created.status_code, 201, created.content)
        self.assertEqual(created.json()["date"], "2026-10-20")

        replaced = self.client.put(url, {"stage": "menstruacion", "mood": "sad", "symptoms": []}, format="json")
        self.assertEqual(replaced.status_code, 200, replaced.content)
        self.assertEqual(replaced.json()["id"], created.json()["id"])
        self.assertFalse(replaced.json()["period"])  # PUT reemplaza todo el registro
        self.assertEqual(replaced.json()["symptoms"], [])
        self.assertEqual(DailyLog.objects.count(), 1)

        self.assertEqual(self.client.get(url).json()["mood"], "sad")
        self.assertEqual(self.client.delete(url).status_code, 204)
        missing = self.client.get(url)
        self.assertEqual(missing.status_code, 404)
        self.assertEqual(missing.json()["error"], "not_found")

    def test_url_date_wins_over_body_and_invalid_dates_are_400(self):
        response = self.client.put(
            "/api/myths/2026-10-20/", {"date": "1999-01-01", "answered_true": True, "flashcard_id": 3}, format="json"
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["date"], "2026-10-20")

        invalid = self.client.put("/api/chat-summaries/2026-02-30/", {"text": "x"}, format="json")
        self.assertEqual(invalid.status_code, 400)
        self.assertEqual(invalid.json()["fields"], {"date": ["Fecha inválida."]})

    def test_patch_requires_existing_record(self):
        self.assertEqual(self.client.patch("/api/daily-logs/2026-10-20/", {"notes": "x"}, format="json").status_code, 404)


class ListFilterTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("ana@test.com", "ana@test.com", "x")
        self.client = APIClient()
        self.client.force_authenticate(self.user)
        for day in ("2026-09-30", "2026-10-01", "2026-10-15", "2026-11-01"):
            DailyLog.objects.create(user=self.user, date=day, stage="menstruacion")

    def dates(self, query):
        response = self.client.get(f"/api/daily-logs/{query}")
        self.assertEqual(response.status_code, 200, response.content)
        return sorted(log["date"] for log in response.json())

    def test_from_and_to_include_both_ends(self):
        self.assertEqual(self.dates("?from=2026-10-01&to=2026-10-31"), ["2026-10-01", "2026-10-15"])
        self.assertEqual(self.dates("?from=2026-10-15"), ["2026-10-15", "2026-11-01"])

    def test_updated_since_returns_only_recent_changes(self):
        old = timezone.now() - timedelta(days=2)
        DailyLog.objects.exclude(date="2026-10-15").update(updated_at=old)
        since = (timezone.now() - timedelta(days=1)).isoformat()
        self.assertEqual(self.dates(f"?updated_since={since.replace('+', '%2B')}"), ["2026-10-15"])

    def test_invalid_filters_are_400_with_field_errors(self):
        response = self.client.get("/api/daily-logs/?from=10/01/2026&to=2026-02-30&updated_since=ayer")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(set(response.json()["fields"]), {"from", "to", "updated_since"})

    def test_reminders_filter_by_scheduled_day(self):
        for when in ("2026-10-20T08:00:00-06:00", "2026-10-25T08:00:00-06:00"):
            self.client.post("/api/reminders/", {"kind": "supplement", "name": when, "scheduled_at": when}, format="json")
        names = [r["name"] for r in self.client.get("/api/reminders/?to=2026-10-21").json()]
        self.assertEqual(names, ["2026-10-20T08:00:00-06:00"])

    def test_reminder_keeps_the_calendar_day_it_was_logged_on(self):
        response = self.client.post(
            "/api/reminders/",
            {"kind": "appointment", "name": "Control", "scheduled_at": "2026-11-05T09:00:00-06:00", "log_date": "2026-10-20"},
            format="json",
        )
        self.assertEqual(response.status_code, 201, response.content)
        self.assertEqual(response.json()["log_date"], "2026-10-20")


class ClientIdTests(TestCase):
    def setUp(self):
        self.ana = User.objects.create_user("ana@test.com", "ana@test.com", "x")
        self.eva = User.objects.create_user("eva@test.com", "eva@test.com", "x")
        self.client = APIClient()

    def post_doctor(self, user, client_id, name="Dra. Ruiz"):
        self.client.force_authenticate(user)
        return self.client.post("/api/doctors/", {"name": name, "client_id": client_id}, format="json")

    def test_repeated_post_with_same_client_id_does_not_duplicate(self):
        client_id = str(uuid.uuid4())
        first = self.post_doctor(self.ana, client_id)
        retry = self.post_doctor(self.ana, client_id, name="Otro nombre")
        self.assertEqual((first.status_code, retry.status_code), (201, 200))
        self.assertEqual(retry.json()["id"], first.json()["id"])
        self.assertEqual(retry.json()["name"], "Dra. Ruiz")  # el reintento no cambia el registro
        self.assertEqual(Doctor.objects.filter(user=self.ana).count(), 1)

    def test_client_id_is_per_user_and_must_be_a_uuid(self):
        client_id = str(uuid.uuid4())
        self.assertEqual(self.post_doctor(self.ana, client_id).status_code, 201)
        self.assertEqual(self.post_doctor(self.eva, client_id).status_code, 201)
        bad = self.post_doctor(self.ana, "no-es-un-uuid")
        self.assertEqual(bad.status_code, 400)
        self.assertIn("client_id", bad.json()["fields"])

    def test_post_without_client_id_still_works(self):
        self.assertEqual(self.post_doctor(self.ana, None).status_code, 201)
        self.assertEqual(self.post_doctor(self.ana, None).status_code, 201)


class ErrorFormatTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        User.objects.create_user("ana@test.com", "ana@test.com", "Clave-Segura-123")

    def test_auth_errors_have_codes(self):
        missing = self.client.get("/api/daily-logs/")
        self.assertEqual((missing.status_code, missing.json()["error"]), (401, "not_authenticated"))

        self.client.credentials(HTTP_AUTHORIZATION="Bearer basura")
        bad_token = self.client.get("/api/daily-logs/")
        self.assertEqual((bad_token.status_code, bad_token.json()["error"]), (401, "token_not_valid"))

        self.client.credentials()
        wrong = self.client.post("/api/token/", {"email": "ana@test.com", "password": "mala"}, format="json")
        self.assertEqual((wrong.status_code, wrong.json()["error"]), (401, "no_active_account"))

    def test_validation_and_method_errors(self):
        duplicate = self.client.post(
            "/register/",
            {"email": "ana@test.com", "password": "x", "name": "Ana", "last_name": "L"},
            format="json",
        )
        self.assertEqual(duplicate.status_code, 400)
        self.assertEqual(duplicate.json()["error"], "validation_error")
        self.assertIn("email", duplicate.json()["fields"])

        self.client.force_authenticate(User.objects.get())
        not_allowed = self.client.delete("/api/symptoms/cramps/")
        self.assertEqual((not_allowed.status_code, not_allowed.json()["error"]), (405, "method_not_allowed"))

    def test_unknown_api_url_is_json_and_web_url_is_html(self):
        api = self.client.get("/api/no-existe/")
        self.assertEqual(api.status_code, 404)
        self.assertEqual(api.json()["error"], "not_found")
        web = self.client.get("/no-existe/")
        self.assertEqual(web.status_code, 404)
        self.assertNotIn("application/json", web["Content-Type"])

    def test_database_conflicts_become_409(self):
        response = exception_handler(IntegrityError("duplicate key"), {})
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.data["error"], "conflict")
