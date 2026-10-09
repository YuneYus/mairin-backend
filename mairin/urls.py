from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, include
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)

from api.views import (
    MedicalInfoView,
    ProfileView,
    RegisterView,
    EmailTokenObtainPairView,
    download_app_page,
    download_latest_app,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("api.urls")),
    path("api/token/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("register/", RegisterView.as_view(), name="register"),
    path("profile/", ProfileView.as_view(), name="profile"),
    path("medical-info/", MedicalInfoView.as_view(), name="medical-info"),
    path("download-app/", download_app_page, name="download-app"),
    path("download-app/latest/", download_latest_app, name="download-latest-app"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)