
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Archivos estáticos del panel /admin (en producción los sirve WhiteNoise)
# Railway no pasa sus variables al build: collectstatic solo necesita una clave cualquiera.
# La SECRET_KEY real se lee al arrancar el contenedor.
RUN SECRET_KEY=solo-para-el-build python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]