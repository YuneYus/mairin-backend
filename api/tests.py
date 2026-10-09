import tempfile

from django.contrib import admin
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from api.models import AppRelease


class AppReleaseDownloadTests(TestCase):
    def setUp(self):
        media_directory = tempfile.TemporaryDirectory()
        self.addCleanup(media_directory.cleanup)
        media_settings = override_settings(MEDIA_ROOT=media_directory.name)
        media_settings.enable()
        self.addCleanup(media_settings.disable)

    def test_download_page_shows_empty_state_and_file_route_is_not_found(self):
        response = self.client.get(reverse("download-app"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "PRÓXIMAMENTE")
        self.assertEqual(self.client.get(reverse("download-latest-app")).status_code, 404)

    def test_admin_can_manage_releases_and_latest_apk_is_downloadable(self):
        self.assertIn(AppRelease, admin.site._registry)
        AppRelease.objects.create(
            version="1.2.2",
            apk=SimpleUploadedFile("older.apk", b"older-apk-content"),
        )
        AppRelease.objects.create(
            version="1.2.3",
            apk=SimpleUploadedFile(
                "mairin.apk",
                b"test-apk-content",
                content_type="application/vnd.android.package-archive",
            ),
            release_notes="Mejoras generales",
        )

        page_response = self.client.get(reverse("download-app"))
        self.assertContains(page_response, "1.2.3")
        download_response = self.client.get(reverse("download-latest-app"))

        self.assertEqual(download_response.status_code, 200)
        self.assertIn("attachment", download_response["Content-Disposition"])
        self.assertEqual(b"".join(download_response.streaming_content), b"test-apk-content")