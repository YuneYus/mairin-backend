import re
from pathlib import Path

from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import FileResponse, Http404
from django.shortcuts import render
from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime
from rest_framework import viewsets, generics, permissions, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import (
    AppRelease,
    ChatSummary,
    DailyLog,
    Doctor,
    MedicalInfo,
    MythAnswer,
    Profile,
    Reminder,
    Symptom,
)

from .serializers import (
    ChatSummarySerializer,
    DailyLogSerializer,
    DoctorSerializer,
    EmailTokenObtainPairSerializer,
    MedicalInfoSerializer,
    MythAnswerSerializer,
    ProfileSerializer,
    RegisterSerializer,
    ReminderSerializer,
    SymptomSerializer,
)


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def to_date(value):
    """'2026-10-20' -> date; None si el texto no es una fecha válida (incluye 2026-02-30)."""
    try:
        return parse_date(value) if value and DATE_RE.match(value) else None
    except ValueError:
        return None


def to_datetime(value):
    try:
        return parse_datetime(value) if value else None
    except ValueError:
        return None


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]


class EmailTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailTokenObtainPairSerializer


class ProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        profile, _ = Profile.objects.get_or_create(
            user=self.request.user
        )
        return profile


class UserScopedViewSet(viewsets.ModelViewSet):
    """Base: cada usuaria solo accede a sus propios datos.

    Filtros de lista (todos opcionales):
      ?from=AAAA-MM-DD&to=AAAA-MM-DD  rango de fechas, ambos incluidos
      ?updated_since=<fecha y hora ISO>  solo lo modificado después de ese momento (para sincronizar)
    """

    permission_classes = [permissions.IsAuthenticated]
    # Campo usado por ?from= y ?to= (None = el recurso no se filtra por fecha).
    date_filter_field = None

    def get_queryset(self):
        queryset = self.queryset.filter(user=self.request.user)
        if self.action == "list":
            queryset = self.filter_list(queryset)
        return queryset

    def filter_list(self, queryset):
        params = self.request.query_params
        errors = {}
        if self.date_filter_field:
            for param, lookup in (("from", "gte"), ("to", "lte")):
                if param in params:
                    day = to_date(params[param])
                    if day is None:
                        errors[param] = ["Usa el formato AAAA-MM-DD."]
                    else:
                        queryset = queryset.filter(**{f"{self.date_filter_field}__{lookup}": day})
        if "updated_since" in params:
            moment = to_datetime(params["updated_since"])
            if moment is None:
                errors["updated_since"] = ["Usa una fecha y hora ISO, por ejemplo 2026-10-20T08:00:00-06:00."]
            else:
                if timezone.is_naive(moment):
                    moment = timezone.make_aware(moment)
                queryset = queryset.filter(updated_at__gt=moment)
        if errors:
            raise ValidationError(errors)
        return queryset

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class DateKeyedViewSet(UserScopedViewSet):
    """Recursos con un solo registro por usuaria y día: la fecha es su dirección.

    GET/PATCH/DELETE /<recurso>/AAAA-MM-DD/
    PUT /<recurso>/AAAA-MM-DD/ crea el registro si no existe o lo reemplaza si existe (201 / 200),
    así la app puede reintentar el mismo envío sin crear duplicados.
    """

    date_filter_field = "date"
    lookup_field = "date"
    lookup_value_regex = r"\d{4}-\d{2}-\d{2}"

    def update(self, request, *args, **kwargs):
        if kwargs.get("partial"):
            return super().update(request, *args, **kwargs)

        day = to_date(kwargs["date"])
        if day is None:
            raise ValidationError({"date": ["Fecha inválida."]})
        data = request.data.copy()
        data["date"] = day.isoformat()

        instance = self.get_queryset().filter(date=day).first()
        if instance is not None:
            # PUT reemplaza el registro completo: lo que no se envía vuelve a su valor por defecto.
            data = {**self.empty_values(), **data}
        serializer = self.get_serializer(instance, data=data)
        serializer.is_valid(raise_exception=True)
        if instance is None:
            self.perform_create(serializer)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        self.perform_update(serializer)
        return Response(serializer.data)


    def empty_values(self):
        """Valor por defecto de cada campo editable, como si el registro fuera nuevo."""
        model = self.get_queryset().model
        values = {}
        for name, field in self.get_serializer().fields.items():
            if field.read_only:
                continue
            if getattr(field, "many", False):
                values[name] = []
                continue
            try:
                model_field = model._meta.get_field(field.source)
            except Exception:
                continue
            if model_field.has_default():
                values[name] = model_field.get_default()
            elif model_field.null:
                values[name] = None
            elif model_field.blank and model_field.empty_strings_allowed:
                values[name] = ""
        return values


class ClientIdViewSet(UserScopedViewSet):
    """Recursos que crea la app sin conexión: un POST repetido con el mismo `client_id`
    devuelve el registro ya creado (200) en vez de duplicarlo."""

    def create(self, request, *args, **kwargs):
        client_id = request.data.get("client_id")
        if client_id:
            try:
                existing = self.get_queryset().filter(client_id=client_id).first()
            except DjangoValidationError:
                existing = None  # client_id mal formado: el serializer devolverá el error
            if existing is not None:
                return Response(self.get_serializer(existing).data, status=status.HTTP_200_OK)
        return super().create(request, *args, **kwargs)


class DailyLogViewSet(DateKeyedViewSet):
    queryset = DailyLog.objects.prefetch_related("symptoms__symptom")
    serializer_class = DailyLogSerializer


class ReminderViewSet(ClientIdViewSet):
    queryset = Reminder.objects.all()
    serializer_class = ReminderSerializer
    date_filter_field = "scheduled_at__date"


class SymptomViewSet(viewsets.ReadOnlyModelViewSet):
    """Catálogo de síntomas (igual para todas las usuarias)."""

    queryset = Symptom.objects.all()
    serializer_class = SymptomSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = "code"


class DoctorViewSet(ClientIdViewSet):
    queryset = Doctor.objects.all()
    serializer_class = DoctorSerializer


class MythAnswerViewSet(DateKeyedViewSet):
    queryset = MythAnswer.objects.all()
    serializer_class = MythAnswerSerializer


class ChatSummaryViewSet(DateKeyedViewSet):
    queryset = ChatSummary.objects.all()
    serializer_class = ChatSummarySerializer


class MedicalInfoView(generics.RetrieveUpdateAPIView):
    serializer_class = MedicalInfoSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        info, _ = MedicalInfo.objects.prefetch_related("surgeries", "usual_symptoms__symptom").get_or_create(
            user=self.request.user
        )
        return info


def download_app_page(request):
    return render(request, "api/download_app.html", {"release": AppRelease.objects.first()})


def download_latest_app(request):
    release = AppRelease.objects.first()
    if release is None:
        raise Http404("No app release is available.")
    return FileResponse(
        release.apk.open("rb"),
        as_attachment=True,
        filename=Path(release.apk.name).name,
        content_type="application/vnd.android.package-archive",
    )