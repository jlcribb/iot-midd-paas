# Script Principal - IoT Middleware

## Descripción

El script principal `main.py` es el punto de entrada central del IoT Middleware que coordina e inicia todos los servicios del sistema en paralelo. Utiliza threading para ejecutar simultáneamente el cliente MQTT, la API REST, y los servicios de auditoría, proporcionando un sistema completo y monitoreado.

## Características Principales

### 🚀 **Inicialización Automática**
- **Carga automática** de `config.yaml`
- **Inicialización secuencial** de todos los servicios
- **Verificación de dependencias** y conexiones
- **Manejo de errores** robusto durante el arranque

### 🔄 **Ejecución en Paralelo**
- **Cliente MQTT** en thread separado
- **API REST** en thread separado
- **Servicios de auditoría** integrados
- **Monitoreo continuo** del estado del sistema

### 📊 **Monitoreo en Tiempo Real**
- **Estado de servicios** actualizado cada 10 segundos
- **Información de conexiones** MQTT y API
- **Estado de threads** y recursos del sistema
- **Logging estructurado** para debugging

### 🛡️ **Gestión del Ciclo de Vida**
- **Manejo de señales** del sistema (SIGINT, SIGTERM)
- **Parada ordenada** de todos los servicios
- **Limpieza de recursos** y conexiones
- **Timeout de parada** configurable

## Arquitectura del Sistema

```
┌─────────────────────────────────────────────────────────────┐
│                    IoT Middleware Manager                   │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   Config    │  │  Database   │  │     Auditoría       │ │
│  │   Loader    │  │   Handler   │  │     Service         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │   MQTT      │  │   Ingesta   │  │      API REST       │ │
│  │   Client    │  │   Service   │  │      Server         │ │
│  └─────────────┘  └─────────────┘  └─────────────────────┘ │
├─────────────────────────────────────────────────────────────┤
│                    Service Monitor                         │
│              (Estado cada 10 segundos)                     │
└─────────────────────────────────────────────────────────────┘
```

## Servicios Iniciados

### 1. **Cliente MQTT**
- **Función**: Conexión al broker MQTT
- **Thread**: Separado y monitoreado
- **Funcionalidades**: Suscripción a tópicos, reconexión automática
- **Configuración**: Desde `config.yaml` sección `mqtt`

### 2. **Servicio de Ingesta**
- **Función**: Procesamiento de mensajes MQTT
- **Thread**: Separado y monitoreado
- **Funcionalidades**: Validación, normalización, almacenamiento
- **Configuración**: Desde `config.yaml` sección `ingesta`

### 3. **API REST**
- **Función**: Servidor HTTP para consultas
- **Thread**: Separado y monitoreado
- **Funcionalidades**: Endpoints para datos, estadísticas, tópicos
- **Configuración**: Desde `config.yaml` sección `api`

### 4. **Servicio de Auditoría**
- **Función**: Registro de cambios del sistema
- **Integración**: Con todos los servicios
- **Funcionalidades**: Logging de operaciones, cambios de datos
- **Configuración**: Desde `config.yaml` sección `auditoria`

### 5. **Monitoreo del Sistema**
- **Función**: Supervisión continua del estado
- **Thread**: Separado y monitoreado
- **Funcionalidades**: Estado de servicios, threads, conexiones
- **Intervalo**: Actualización cada 10 segundos

## Uso Básico

### **Ejecución Simple**
```bash
# Desde el directorio raíz del proyecto
python main.py
```

### **Verificación de Estado**
El script muestra automáticamente:
```
============================================================
📊 ESTADO DE SERVICIOS - IoT Middleware
============================================================
🕐 Timestamp: 2024-01-15 10:35:00 UTC

✅ CONFIG: ACTIVO
✅ DATABASE: ACTIVO
✅ MQTT: ACTIVO
✅ INGESTOR: ACTIVO
✅ API: ACTIVO
✅ AUDITORIA: ACTIVO

🧵 THREADS DE SERVICIOS:
   ✅ IngestorService: ACTIVO (ID: 12345)
   ✅ APIServer: ACTIVO (ID: 12346)

📡 MQTT:
   Broker: localhost:1883
   Estado: CONECTADO
   Tópicos suscritos: 4

🌐 API REST:
   URL: http://localhost:8000
   Documentación: http://localhost:8000/docs
   Estado: ACTIVA
============================================================
```

### **Parada del Sistema**
```bash
# Presionar Ctrl+C para parada ordenada
^C
🛑 Señal recibida: 2
🛑 Deteniendo IoT Middleware...
✅ Servicio de ingesta detenido
✅ Cliente MQTT desconectado
✅ Conexiones de base de datos cerradas
🎉 IoT Middleware detenido correctamente
```

## Configuración

### **Archivo config.yaml**
El script principal lee la configuración desde `config.yaml`:

```yaml
# Configuración MQTT
mqtt:
  broker:
    host: "localhost"
    port: 1883
    username: "iot_user"
    password: "iot_password"

# Configuración de almacenamiento
storage:
  type: "postgresql"
  postgresql:
    host: "localhost"
    port: 5432
    database: "iot_middleware"

# Configuración de la API
api:
  host: "0.0.0.0"
  port: 8000
```

### **Variables de Entorno**
```bash
# Configurar archivo de configuración personalizado
export IOT_CONFIG_PATH="/path/to/custom/config.yaml"

# Configurar nivel de logging
export IOT_LOG_LEVEL="DEBUG"

# Configurar puerto de la API
export IOT_API_PORT="8080"
```

## Estructura del Código

### **Clase Principal: IoTMiddlewareManager**

#### **Inicialización**
```python
class IoTMiddlewareManager:
    def __init__(self, config_path: str = "config.yaml"):
        self.config_path = config_path
        self.services_status = {...}
        self.service_threads = {}
        self.running = False
        self.shutdown_event = threading.Event()
```

#### **Métodos Principales**
- `load_configuration()`: Carga y valida config.yaml
- `initialize_all_services()`: Inicializa todos los servicios
- `start_all_services()`: Inicia servicios en threads
- `monitor_services()`: Monitoreo continuo del estado
- `shutdown()`: Parada ordenada del sistema

### **Flujo de Ejecución**
```python
def run(self):
    # 1. Inicializar servicios
    if not self.initialize_all_services():
        return False
    
    # 2. Iniciar servicios
    self.start_all_services()
    
    # 3. Monitoreo continuo
    self.monitor_services()
    
    # 4. Esperar señal de parada
    while self.running:
        time.sleep(1)
```

## Monitoreo y Logging

### **Logs del Sistema**
- **Archivo**: `iot_middleware.log`
- **Consola**: Estado en tiempo real
- **Base de datos**: Registros de auditoría

### **Niveles de Logging**
```python
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('iot_middleware.log')
    ]
)
```

### **Métricas Disponibles**
- **Estado de servicios**: Activo/Inactivo
- **Estado de threads**: ID y estado
- **Conexiones MQTT**: Broker y tópicos
- **API REST**: URL y estado
- **Base de datos**: Estado de conexión

## Manejo de Errores

### **Errores de Inicialización**
```python
try:
    if not self.initialize_database():
        self.logger.error("❌ Falló la inicialización de la base de datos")
        return False
except Exception as e:
    self.logger.error(f"❌ Error inesperado: {e}")
    return False
```

### **Errores de Servicios**
```python
def ingestor_worker():
    try:
        self.ingestor_service.start()
    except Exception as e:
        self.logger.error(f"❌ Error en servicio de ingesta: {e}")
        self.services_status['ingestor'] = False
```

### **Recuperación Automática**
- **Reconexión MQTT**: Automática con backoff exponencial
- **Reinicio de servicios**: Monitoreo y detección de fallos
- **Logging de errores**: Detallado para debugging

## Señales del Sistema

### **Manejo de Señales**
```python
def setup_signal_handlers(self):
    def signal_handler(signum, frame):
        self.logger.info(f"🛑 Señal recibida: {signum}")
        self.shutdown()
    
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # kill
```

### **Parada Ordenada**
```python
def shutdown(self):
    # 1. Marcar para parada
    self.running = False
    self.shutdown_event.set()
    
    # 2. Detener servicios
    if self.ingestor_service:
        self.ingestor_service.stop()
    
    # 3. Cerrar conexiones
    if self.db_handler:
        self.db_handler.close()
    
    # 4. Esperar threads
    for thread in self.service_threads.values():
        thread.join(timeout=5)
```

## Escenarios de Uso

### **1. Desarrollo Local**
```bash
# Configuración básica para desarrollo
python main.py

# Con logging detallado
export IOT_LOG_LEVEL="DEBUG"
python main.py
```

### **2. Producción**
```bash
# Ejecutar como servicio del sistema
sudo systemctl start iot-middleware

# Con configuración personalizada
python main.py /etc/iot-middleware/config.yaml
```

### **3. Testing**
```bash
# Ejecutar pruebas del sistema
python examples/main_usage_example.py

# Verificar estado de servicios
curl http://localhost:8000/health
```

### **4. Monitoreo**
```bash
# Ver logs en tiempo real
tail -f iot_middleware.log

# Ver estado del sistema
watch -n 10 "curl -s http://localhost:8000/health"
```

## Troubleshooting

### **Problemas Comunes**

#### **1. Error de Configuración**
```bash
❌ Error cargando configuración: FileNotFoundError
💡 Solución: Verificar que config.yaml existe en el directorio actual
```

#### **2. Error de Base de Datos**
```bash
❌ Error inicializando base de datos: Connection refused
💡 Solución: Verificar que PostgreSQL esté ejecutándose
```

#### **3. Error MQTT**
```bash
❌ No se pudo conectar al broker MQTT
💡 Solución: Verificar que Mosquitto esté ejecutándose
```

#### **4. Puerto API Ocupado**
```bash
❌ Error iniciando servidor de API: Address already in use
💡 Solución: Cambiar puerto en config.yaml o liberar puerto 8000
```

### **Comandos de Diagnóstico**
```bash
# Verificar estado de servicios
ps aux | grep python

# Verificar puertos en uso
netstat -tlnp | grep :8000

# Verificar logs del sistema
journalctl -u iot-middleware -f

# Verificar conexiones de base de datos
psql -h localhost -U iot_user -d iot_middleware -c "SELECT 1"
```

## Performance y Optimización

### **Threading vs Asyncio**
- **Threading**: Implementado para compatibilidad y simplicidad
- **Ventajas**: Fácil debugging, manejo de señales, compatibilidad
- **Desventajas**: Overhead de contexto, GIL de Python

### **Optimizaciones Implementadas**
- **Threads daemon**: Terminan automáticamente con el proceso principal
- **Timeout de parada**: Evita bloqueos indefinidos
- **Lazy loading**: Inicialización bajo demanda de servicios
- **Connection pooling**: Reutilización de conexiones de base de datos

### **Métricas de Performance**
```python
# Monitoreo de threads
for service_name, thread in self.service_threads.items():
    if thread.is_alive():
        print(f"✅ {service_name}: ACTIVO (ID: {thread.ident})")
    else:
        print(f"❌ {service_name}: INACTIVO")
```

## Seguridad

### **Consideraciones de Seguridad**
- **Archivos de configuración**: Contienen credenciales sensibles
- **Permisos de archivos**: Restringir acceso a config.yaml
- **Variables de entorno**: Para credenciales en producción
- **Logs**: No incluir información sensible

### **Recomendaciones**
```bash
# Restringir permisos del archivo de configuración
chmod 600 config.yaml

# Usar variables de entorno para credenciales
export IOT_DB_PASSWORD="secure_password"
export IOT_MQTT_PASSWORD="secure_password"

# Rotar logs regularmente
logrotate /etc/logrotate.d/iot-middleware
```

## Integración con Otros Sistemas

### **Sistemas de Monitoreo**
- **Prometheus**: Métricas del sistema
- **Grafana**: Dashboards de monitoreo
- **ELK Stack**: Logs centralizados
- **Nagios**: Alertas del sistema

### **CI/CD**
```yaml
# GitHub Actions
- name: Test IoT Middleware
  run: |
    python main.py &
    sleep 10
    curl http://localhost:8000/health
    pkill -f main.py
```

### **Contenedores**
```dockerfile
# Dockerfile
FROM python:3.9-slim
COPY . /app
WORKDIR /app
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
```

## Contribución y Desarrollo

### **Estructura del Proyecto**
```
iot-middleware/
├── main.py                 # Script principal
├── config.yaml            # Configuración del sistema
├── src/                   # Código fuente
├── examples/              # Ejemplos de uso
├── tests/                 # Pruebas unitarias
└── docs/                  # Documentación
```

### **Guías de Desarrollo**
1. **Fork** del repositorio
2. **Crear branch** para feature
3. **Implementar** funcionalidad
4. **Agregar tests** si corresponde
5. **Crear Pull Request**

### **Estándares de Código**
- **PEP 8**: Estilo de Python
- **Type hints**: Para todas las funciones
- **Docstrings**: Completos y descriptivos
- **Logging**: Estructurado y consistente

## Licencia

Este proyecto está bajo la licencia MIT. Ver el archivo `LICENSE` para más detalles.

## Soporte

### **Canales de Soporte**
- **Issues de GitHub**: Para bugs y feature requests
- **Discussions**: Para preguntas y discusiones
- **Wiki**: Documentación adicional
- **Email**: soporte@iot-middleware.com

### **Comunidad**
- **Slack**: #iot-middleware
- **Discord**: Servidor oficial
- **Meetups**: Eventos locales
- **Conferencias**: Presentaciones técnicas

---

**Nota**: El script principal es el corazón del IoT Middleware. Para más información sobre otros componentes, consulta la [documentación principal](README.md).
