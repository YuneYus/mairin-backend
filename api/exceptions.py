"""Formato único de errores de la API.

Todas las respuestas de error tienen esta forma (el código HTTP no cambia):

    {"error": "<código>", "detail": "<mensaje>", "fields": {"<campo>": ["<mensaje>", ...]}}

`error` es estable y es lo que la app debe revisar; `detail` es para mostrar o registrar;
`fields` solo aparece en errores de validación (400).
"""

from django.core.exceptions import PermissionDenied
from django.db import IntegrityError
from django.http import Http404, JsonResponse
from django.views import defaults
from rest_framework import exceptions, status
from rest_framework.views import exception_handler as drf_exception_handler

# Rutas que responden JSON aunque la URL no exista o el servidor falle.
API_PREFIXES = ("/api/", "/register/", "/profile/", "/medical-info/")


class Conflict(exceptions.APIException):
    """El registro ya existe (por ejemplo, otro registro diario para la misma fecha)."""

    status_code = status.HTTP_409_CONFLICT
    default_detail = "El registro ya existe."
    default_code = "already_exists"


def _first_code(codes):
    """Primer código de error de una estructura anidada de get_codes()."""
    if isinstance(codes, dict):
        codes = next(iter(codes.values()), None)
    if isinstance(codes, list):
        codes = codes[0] if codes else None
    return codes if isinstance(codes, str) else None


def exception_handler(exc, context):
    if isinstance(exc, IntegrityError):
        # Por ejemplo, dos peticiones simultáneas que crean lo mismo: conflicto, no error 500.
        exc = Conflict("El cambio entra en conflicto con datos existentes.", code="conflict")
    elif isinstance(exc, Http404):
        exc = exceptions.NotFound()
    elif isinstance(exc, PermissionDenied):
        exc = exceptions.PermissionDenied()

    response = drf_exception_handler(exc, context)
    if response is None:
        return None  # error inesperado: lo maneja handler500

    if isinstance(exc, exceptions.ValidationError):
        fields = response.data if isinstance(response.data, dict) else {"non_field_errors": response.data}
        response.data = {"error": "validation_error", "detail": "Hay datos inválidos.", "fields": fields}
        return response

    data = response.data if isinstance(response.data, dict) else {}
    code = data.get("code") or _first_code(exc.get_codes()) or getattr(exc, "default_code", "error")
    detail = data.get("detail", getattr(exc, "default_detail", ""))
    response.data = {"error": code, "detail": str(detail)}
    return response


def _is_api(request):
    return request.path.startswith(API_PREFIXES)


def handler404(request, exception=None):
    if _is_api(request):
        return JsonResponse({"error": "not_found", "detail": "La ruta no existe."}, status=404)
    return defaults.page_not_found(request, exception)


def handler500(request):
    if _is_api(request):
        return JsonResponse({"error": "server_error", "detail": "Error interno del servidor."}, status=500)
    return defaults.server_error(request)
