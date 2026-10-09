# 🌸 MAIRIN Backend

Backend de **MAIRIN**, una aplicación integral de salud femenina diseñada para acompañar a las usuarias en las diferentes etapas de su vida.

Este proyecto está desarrollado con **Django** y **Django REST Framework**, y proporciona una API REST para gestionar usuarios, autenticación, información médica, ciclo menstrual, embarazo, menopausia, estado de ánimo, doctores y otros módulos de la aplicación.

---

## 🛠️ Tecnologías utilizadas

* Python
* Django
* Django REST Framework
* PostgreSQL
* Docker
* Docker Compose
* JWT Authentication
* SimpleJWT
* Psycopg2

---

## 📁 Estructura del proyecto

```text
mairin-backend/
│
├── api/
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── urls.py
│
├── mairin/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
│
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
├── manage.py
└── README.md
```

---

# 🚀 Instalación y ejecución con Docker

## 1. Clonar el repositorio

```bash
git clone <URL_DEL_REPOSITORIO>
cd mairin-backend
```

## 2. Variables de entorno

No hace falta configurar nada: el archivo `.env` del repositorio ya trae los valores de desarrollo (SQLite local, `DEBUG=True`).

---

## 3. Construir e iniciar los contenedores

```bash
docker compose up --build
```

Para ejecutarlo en segundo plano:

```bash
docker compose up -d --build
```

---

## 4. Verificar los contenedores

```bash
docker ps
```

Deberías ver los servicios del backend y PostgreSQL ejecutándose.

---

# 🗄️ Migraciones

Aplicar las migraciones de la base de datos:

```bash
docker compose exec web python manage.py migrate
```

Crear nuevas migraciones cuando se modifiquen los modelos:

```bash
docker compose exec web python manage.py makemigrations
```

Luego:

```bash
docker compose exec web python manage.py migrate
```

---

# 👤 Crear un superusuario

Para acceder al panel administrativo de Django:

```bash
docker compose exec web python manage.py createsuperuser
```

Después de crear el usuario, ingresa al panel administrativo:

```text
http://localhost:8000/admin/
```

---

# ▶️ Ejecutar el servidor

Si utilizas Docker:

```bash
docker compose up
```

El backend estará disponible en:

```text
http://localhost:8000/
```

---

# 🔐 Autenticación JWT

MAIRIN utiliza **JSON Web Tokens (JWT)** para la autenticación de usuarios.

## Obtener token

```text
POST /api/token/
```

Ejemplo:

```json
{
  "username": "usuario",
  "password": "contraseña"
}
```

Respuesta:

```json
{
  "access": "ACCESS_TOKEN",
  "refresh": "REFRESH_TOKEN"
}
```

---

## Renovar token

```text
POST /api/token/refresh/
```

Ejemplo:

```json
{
  "refresh": "REFRESH_TOKEN"
}
```

---

# 👩‍⚕️ API Endpoints

## 👤 Usuarios

```text
POST /register/
GET /profile/
```

---

## 🩺 Información médica

```text
GET /medical-info/
POST /medical-info/
```

---

## 🩸 Ciclo menstrual

```text
/api/menstruation/
```

Permite registrar información relacionada con el ciclo menstrual, síntomas y otros datos.

---

## 🤰 Embarazo

```text
/api/pregnancy/
```

Permite gestionar información relacionada con el seguimiento del embarazo.

---

## 🌸 Menopausia

```text
/api/menopause/
```

Permite registrar información relacionada con síntomas y seguimiento durante la menopausia.

---

## 😊 Estado de ánimo

```text
/api/moods/
```

Permite registrar el estado de ánimo de la usuaria.

---

## 👩‍⚕️ Doctores

```text
/api/doctors/
```

Permite gestionar información de profesionales de salud.

---

## 💬 Chat

```text
/api/chat-summaries/
```

Permite almacenar o consultar información relacionada con las conversaciones y resúmenes del chat.

---

# 🧪 Probar la API

Puedes probar los endpoints utilizando:

* Postman
* Insomnia
* Thunder Client
* Django REST Framework Browsable API

Para endpoints protegidos debes incluir el token JWT:

```text
Authorization: Bearer ACCESS_TOKEN
```

---

# 📱 Conexión con el Frontend

La aplicación móvil debe apuntar a la dirección IP de la computadora donde se encuentra ejecutándose el backend.

Ejemplo:

```text
http://192.168.X.X:8000
```

Para obtener la dirección IP en Windows:

```powershell
ipconfig
```

Busca la dirección:

```text
IPv4 Address
```

La computadora que ejecuta el frontend y la que ejecuta el backend deben estar conectadas a la misma red.

---

# 🔗 Endpoints principales

| Servicio           | Endpoint               |
| ------------------ | ---------------------- |
| Registro           | `/register/`           |
| Perfil             | `/profile/`            |
| Información médica | `/medical-info/`       |
| Obtener token      | `/api/token/`          |
| Renovar token      | `/api/token/refresh/`  |
| Menstruación       | `/api/menstruation/`   |
| Embarazo           | `/api/pregnancy/`      |
| Menopausia         | `/api/menopause/`      |
| Doctores           | `/api/doctors/`        |
| Estado de ánimo    | `/api/moods/`          |
| Mitos              | `/api/myths/`          |
| Chat               | `/api/chat-summaries/` |
| Administración     | `/admin/`              |

---

# 🛑 Detener los contenedores

```bash
docker compose down
```

Para detenerlos sin eliminar los datos de PostgreSQL:

```bash
docker compose stop
```

---

# 🧹 Reconstruir el proyecto

Si realizas cambios importantes:

```bash
docker compose down
docker compose up --build
```

---

# 📦 Instalación sin Docker

## Crear entorno virtual

```bash
python -m venv .venv
```

Activar en Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Instalar dependencias:

```bash
pip install -r requirements.txt
```

Ejecutar migraciones:

```bash
python manage.py migrate
```

Iniciar el servidor:

```bash
python manage.py runserver
```

El backend estará disponible en:

```text
http://127.0.0.1:8000
```

---

# ☁️ Deploy en Railway

El repositorio ya incluye `railway.json`: Railway construye con el `Dockerfile` y, en cada arranque, aplica las migraciones (`migrate`) y luego inicia `gunicorn`.

1. En Railway: **New Project → Deploy from GitHub repo** → elegir `mairin-backend`.
2. En el mismo proyecto: **New → Database → PostgreSQL**.
3. En el servicio del backend → **Variables**, agregar:

| Variable | Valor |
| --- | --- |
| `SECRET_KEY` | Una clave larga y nueva (no la del `.env`) |
| `DEBUG` | `False` |
| `DATABASE_URL` | `${{Postgres.DATABASE_URL}}` |
| `ALLOWED_HOSTS` | El dominio de Railway, ej. `tu-app.up.railway.app` |
| `CSRF_TRUSTED_ORIGINS` | `https://tu-app.up.railway.app` |

4. En **Settings → Networking → Generate Domain** para obtener la URL pública.
5. Crear el superusuario desde la terminal del servicio en Railway: `python manage.py createsuperuser`.

Las variables de Railway tienen prioridad sobre el `.env`, así que el `.env` del repo no afecta a producción.

---

# 🌸 MAIRIN

MAIRIN es una plataforma integral de salud femenina que busca acompañar a las usuarias durante diferentes etapas de su vida, proporcionando herramientas para el seguimiento de su salud y acceso a información y servicios relacionados.

## Funcionalidades principales

* Registro e inicio de sesión.
* Autenticación segura mediante JWT.
* Gestión de perfiles.
* Registro de información médica.
* Seguimiento del ciclo menstrual.
* Seguimiento del embarazo.
* Seguimiento de la menopausia.
* Registro del estado de ánimo.
* Información y orientación en salud femenina.
* Gestión de doctores.
* Integración con la aplicación móvil.

---

# 👥 Equipo

Proyecto desarrollado como parte de **MAIRIN**, una aplicación enfocada en el bienestar y la salud integral de las mujeres.

---

## 📄 Licencia

Proyecto académico y de desarrollo.

## Despliegue en Azure

- **Servidor:** máquina virtual Ubuntu 24.04 en Azure (`MAIRIN`), IP pública `68.211.89.151`.
- **Puertos abiertos (NSG):** 22 (SSH) y 80 (HTTP). La base de datos no está expuesta a internet.
- **Stack:** Python 3.12, Django 5.1, Django REST Framework, SimpleJWT, SQLite, nginx.
- **Código:** `/home/mairin/mairin-backend/mairin-backend`, con entorno virtual en `.venv`.
- **Servicio:** `mairin.service` (systemd) ejecuta Django en `127.0.0.1:8000`; nginx hace de proxy en el puerto 80 y sirve `/static/` y `/downloads/`.
- **Variables (`.env`, no se sube a GitHub):** `SECRET_KEY`, `ALLOWED_HOSTS=68.211.89.151,127.0.0.1,localhost`, `CSRF_TRUSTED_ORIGINS=http://68.211.89.151`.
- **Comandos útiles en el servidor:**
```bash
  sudo systemctl status mairin nginx
  sudo systemctl restart mairin
  python manage.py migrate
  python manage.py collectstatic --noinput
```
- **APK:** se compila con `eas build -p android --profile azure` (la app usa `EXPO_PUBLIC_API_URL=http://68.211.89.151`) y se publica en `http://68.211.89.151/downloads/mairin.apk`.
