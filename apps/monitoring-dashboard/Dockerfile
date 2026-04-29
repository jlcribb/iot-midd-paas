# Dockerfile para Dashboard de Monitoreo - IoT Middleware
FROM python:3.12-slim

# Metadatos
LABEL maintainer="IoT Middleware Team"
LABEL description="Dashboard de monitoreo en tiempo real para IoT Middleware"
LABEL version="1.0.0"

# Variables de entorno
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DASHBOARD_PORT=8080 \
    DASHBOARD_HOST=0.0.0.0

# Directorio de trabajo
WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requisitos
COPY apps/monitoring-dashboard/requirements.txt /app/requirements-dashboard.txt

# Instalar dependencias de Python
RUN pip install --no-cache-dir -r /app/requirements-dashboard.txt

# Copiar código fuente
COPY src/ /app/src/
COPY apps/monitoring-dashboard/ /app/apps/monitoring-dashboard/
COPY config.yaml /app/config.yaml
RUN mkdir -p /app/containers && ln -s /app/apps/monitoring-dashboard /app/containers/dashboard

# Variables de entorno para configuración
ENV PYTHONPATH=/app/src \
    DASHBOARD_CONFIG=/app/config.yaml

# Exponer puerto
EXPOSE 8080

# Health check (urllib estándar; evita depender de requests)
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=5).read()" || exit 1

# Comando de inicio
CMD ["python", "-m", "containers.dashboard.main"]
