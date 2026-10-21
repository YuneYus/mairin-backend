# API de Mairin

Base en producción: `https://mairin-backend-production.up.railway.app`

Todas las rutas, salvo `/register/` y `/api/token/`, requieren el encabezado:

```text
Authorization: Bearer <access token>
```

Cada usuaria solo ve y modifica sus propios datos. El modelo de datos está en
[`modelo-de-datos.md`](modelo-de-datos.md).

## Cuenta

| Método | Ruta | Uso |
|---|---|---|
| POST | `/register/` | Crear cuenta: `email`, `password`, `name`, `last_name`, `birth_date` (opcional) |
| POST | `/api/token/` | Iniciar sesión con `email` y `password` → `access` y `refresh` |
| POST | `/api/token/refresh/` | Renovar el `access` con `refresh` |
| GET / PATCH | `/profile/` | Perfil: nombre, teléfono, etapa, idiomas, fechas de ciclo y embarazo |
| GET / PUT / PATCH | `/medical-info/` | Historial médico con `surgeries` y `usual_symptoms` |

## Datos de salud

| Recurso | Ruta | Se identifica por |
|---|---|---|
| Registro diario | `/api/daily-logs/` | **fecha** (`/api/daily-logs/2026-10-20/`) |
| Respuestas de mitos | `/api/myths/` | **fecha** |
| Resúmenes del chat | `/api/chat-summaries/` | **fecha** |
| Recordatorios | `/api/reminders/` | id (y `client_id` opcional) |
| Doctores | `/api/doctors/` | id (y `client_id` opcional) |
| Catálogo de síntomas | `/api/symptoms/` | código, solo lectura |

### Recursos por fecha

Solo hay un registro por usuaria y día, así que la fecha es su dirección:

```text
GET    /api/daily-logs/2026-10-20/   leer
PUT    /api/daily-logs/2026-10-20/   crear (201) o reemplazar (200)
PATCH  /api/daily-logs/2026-10-20/   cambiar algunos campos (404 si no existe)
DELETE /api/daily-logs/2026-10-20/   borrar
```

**Para sincronizar, usa `PUT`.** Reenviar el mismo `PUT` no crea duplicados. `PUT` reemplaza el
registro completo: los campos que no se envían vuelven a su valor por defecto. La fecha de la URL
manda sobre la del cuerpo.

`POST /api/daily-logs/` también crea, pero devuelve **409** si ese día ya tiene registro.

Ejemplo de registro diario:

```json
{
  "stage": "embarazo",
  "mood": "good",
  "exercise": false,
  "notes": "",
  "baby_movement": true,
  "symptoms": [{"code": "nausea"}, {"custom_label": "Calambres en la noche"}]
}
```

- `stage`: `menstruacion` | `embarazo` | `menopausia`
- `mood`: `very_happy` | `good` | `neutral` | `tired` | `sad` | `very_sad` | `angry` | `""`
- Cada síntoma lleva `code` (del catálogo) **o** `custom_label` (texto libre), no los dos.
- Enviar `symptoms` reemplaza la lista completa; en un `PATCH` sin `symptoms` se conservan.

### Recursos con `client_id`

Doctores y recordatorios se crean con `POST`. Si la app crea el registro sin conexión, debe
generar un UUID y mandarlo como `client_id`. Si el mismo `POST` se reenvía (por ejemplo tras un
corte de red), el servidor devuelve el registro ya creado con **200** en lugar de duplicarlo.
Después se usa el `id` del servidor para `PUT`, `PATCH` y `DELETE`.

```json
POST /api/reminders/
{
  "client_id": "6f1c2c1e-6a0b-4a52-9a40-3c1f5a1c9d11",
  "kind": "supplement",
  "name": "Calcio",
  "scheduled_at": "2026-10-21T08:00:00-06:00",
  "reminder_offset": "1hour"
}
```

- `kind`: `appointment` | `supplement`
- `reminder_offset`: `5min` | `10min` | `1hour` | `2hours` | `1day` | `2days` | `1week` | `none`

## Filtros de las listas

Todos opcionales y combinables:

| Parámetro | Ejemplo | Efecto |
|---|---|---|
| `from` | `?from=2026-10-01` | Desde esa fecha, incluida |
| `to` | `?to=2026-10-31` | Hasta esa fecha, incluida |
| `updated_since` | `?updated_since=2026-10-20T08:00:00-06:00` | Solo lo modificado después de ese momento |

`from` y `to` usan la fecha del registro (en recordatorios, el día de `scheduled_at`). Para
cargar el calendario de un mes: `GET /api/daily-logs/?from=2026-10-01&to=2026-10-31`.
`updated_since` sirve para descargar solo lo que cambió desde la última sincronización
(en el `+` de la zona horaria, codifícalo como `%2B` en la URL).

## Errores

Todos los errores tienen la misma forma:

```json
{"error": "validation_error", "detail": "Hay datos inválidos.", "fields": {"blood_type": ["..."]}}
```

La app debe decidir según `error` (estable), no según `detail` (texto para mostrar).
`fields` solo aparece en errores de validación.

| HTTP | `error` | Qué significa | Qué hace la app |
|---|---|---|---|
| 400 | `validation_error` | Datos inválidos; detalle por campo en `fields` | No reintentar; corregir o descartar el cambio |
| 401 | `not_authenticated` | Falta el token | Iniciar sesión |
| 401 | `token_not_valid` | Token vencido o inválido | Renovar con `/api/token/refresh/`; si falla, iniciar sesión |
| 401 | `no_active_account` | Correo o contraseña incorrectos (en `/api/token/`) | Mostrar mensaje |
| 404 | `not_found` | No existe (o es de otra usuaria) | En un `DELETE`, tratarlo como ya borrado |
| 405 | `method_not_allowed` | Método no permitido en esa ruta | Error de programación |
| 409 | `already_exists` | Ya hay un registro para esa fecha | Usar `PUT /<recurso>/<fecha>/` |
| 409 | `conflict` | Choque con otro cambio simultáneo | Reintentar más tarde |
| 500 | `server_error` | Falla del servidor | Reintentar más tarde |

Sin conexión no hay respuesta HTTP: `fetch` lanza un error de red y el cambio debe quedar en cola.
