FROM docker.io/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY apps/admin-fastapi/requirements.txt /app/requirements.txt
RUN python -m pip install --no-cache-dir -r requirements.txt \
    && python -m pip check

# Copiar código de la aplicación
COPY apps/admin-fastapi /app/apps/admin-fastapi
COPY src /app/src
RUN mkdir -p /app/containers && ln -s /app/apps/admin-fastapi /app/containers/admin

# Exponer puerto
EXPOSE 9000

# Comando por defecto
CMD ["python", "-m", "containers.admin.main"]
