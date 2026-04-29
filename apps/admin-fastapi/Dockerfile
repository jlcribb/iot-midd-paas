FROM docker.io/python:3.12-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependencias
COPY apps/admin-fastapi/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código de la aplicación
COPY apps/admin-fastapi /app/apps/admin-fastapi
COPY src /app/src
COPY config.yaml /app/config.yaml
RUN mkdir -p /app/containers && ln -s /app/apps/admin-fastapi /app/containers/admin

# Exponer puerto
EXPOSE 9000

# Comando por defecto
CMD ["python", "-m", "containers.admin.main"]
