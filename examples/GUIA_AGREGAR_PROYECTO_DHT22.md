# Guía: Agregar Proyecto, Unidad y Dispositivo DHT22

Esta guía te ayudará a configurar el proyecto, unidad de producción y dispositivo DHT22 en la interfaz de administración para que puedas visualizar los datos de temperatura y humedad en el dashboard.

## 📋 Resumen

Según el código del ESP32, los tópicos MQTT son:
- **Temperatura:** `iot/proyecto_demo/casa_living/dht22_esp32/temperatura`
- **Humedad:** `iot/proyecto_demo/casa_living/dht22_esp32/humedad`

Por lo tanto, necesitas crear:
1. **Proyecto:** `proyecto_demo`
2. **Unidad:** `casa_living` (del proyecto `proyecto_demo`)
3. **Dispositivo:** `dht22_esp32` (de la unidad `casa_living`)

## 🔧 Paso 1: Acceder a la Interfaz de Administración

1. Abre tu navegador y accede a:
   ```
   http://localhost:9000
   ```

2. Si no está corriendo, inicia el contenedor:
   ```bash
   docker compose -f infra/containers/docker-compose.yaml up -d admin
   ```

## 📁 Paso 2: Crear el Proyecto

1. En la interfaz de administración, haz clic en la sección **"📁 Proyectos"**.

2. Haz clic en el botón **"+ Nuevo Proyecto"**.

3. Completa el formulario con los siguientes datos:

   | Campo | Valor | Descripción |
   |-------|-------|-------------|
   | **Nombre** | `proyecto_demo` | ID del proyecto (debe coincidir con el tópico MQTT) |
   | **Cliente** | `Cliente Demo` | Nombre del cliente |
   | **Estado** | `Activo` | Estado del proyecto |
   | **Fecha Inicio** | `2025-01-01` | Fecha de inicio (ajustar según tu caso) |
   | **Fecha Fin** | *(dejar vacío)* | Fecha de fin (opcional) |
   | **Descripción** | `Proyecto de demostración con DHT22` | Descripción del proyecto |

4. Haz clic en **"Guardar"** o **"Crear"**.

5. Verifica que el proyecto se haya creado correctamente en la lista.

## 🏢 Paso 3: Crear la Unidad de Producción

1. Haz clic en la sección **"🏢 Unidades de Proyecto"**.

2. Haz clic en el botón **"+ Nueva Unidad"**.

3. Completa el formulario con los siguientes datos:

   | Campo | Valor | Descripción |
   |-------|-------|-------------|
   | **Nombre** | `casa_living` | ID de la unidad (debe coincidir con el tópico MQTT) |
   | **Proyecto** | `proyecto_demo` | Selecciona el proyecto creado anteriormente |
   | **Ubicación** | `Living Room` | Ubicación física |
   | **Descripción** | `Sala de estar - sensor DHT22` | Descripción de la unidad |
   | **Responsable** | *(tu nombre)* | Nombre del responsable |
   | **Email** | *(tu email)* | Email del responsable (opcional) |
   | **Teléfono** | *(tu teléfono)* | Teléfono del responsable (opcional) |

4. Haz clic en **"Guardar"** o **"Crear"**.

5. Verifica que la unidad se haya creado correctamente en la lista.

## 🔌 Paso 4: Crear el Dispositivo DHT22

Antes de crear el dispositivo, necesitas crear primero un **Dispositivo Base** (tipo de dispositivo). Sin embargo, según el código del ESP32, el sistema debería crear automáticamente los canales cuando reciba datos.

1. Haz clic en la sección **"🔌 Dispositivos"**.

2. Haz clic en el botón **"+ Nuevo Dispositivo"**.

3. Completa el formulario con los siguientes datos:

   | Campo | Valor | Descripción |
   |-------|-------|-------------|
   | **ID del Dispositivo** | `dht22_esp32` | ID del dispositivo (debe coincidir con el tópico MQTT) |
   | **Proyecto** | `proyecto_demo` | Selecciona el proyecto creado |
   | **Unidad** | `casa_living` | Selecciona la unidad creada |
   | **Nombre Personalizado** | `Sensor DHT22 ESP32` | Nombre descriptivo |
   | **Descripción** | `Sensor de temperatura y humedad DHT22 conectado a ESP32` | Descripción del dispositivo |
   | **Fecha Instalación** | `2025-01-01` | Fecha de instalación (ajustar según tu caso) |
   | **Ubicación Física** | `GPIO 4 - ESP32` | Ubicación física del sensor |
   | **Responsable** | *(tu nombre)* | Nombre del responsable |
   | **Email** | *(tu email)* | Email del responsable (opcional) |
   | **Teléfono** | *(tu teléfono)* | Teléfono del responsable (opcional) |

4. Haz clic en **"Guardar"** o **"Crear"**.

5. Verifica que el dispositivo se haya creado correctamente en la lista.

## ✅ Paso 5: Verificar la Configuración

### 1. Verificar que los datos MQTT se están recibiendo

En el servidor del middleware, verifica los logs:

```bash
docker logs -f iotmw-ingestor
```

Deberías ver mensajes como:
```
✅ Mensaje recibido en iot/proyecto_demo/casa_living/dht22_esp32/temperatura
📊 Datos procesados y almacenados
```

### 2. Consultar datos mediante API

```bash
# Temperatura
curl "http://localhost:8000/api/data?topic=iot/proyecto_demo/casa_living/dht22_esp32/temperatura&limit=10"

# Humedad
curl "http://localhost:8000/api/data?topic=iot/proyecto_demo/casa_living/dht22_esp32/humedad&limit=10"
```

### 3. Verificar en la interfaz de administración

1. Ve a la sección **"📊 Dashboard"** en la interfaz de administración.

2. Deberías ver estadísticas generales del sistema.

3. Para ver los datos específicos del sensor, usa la API o el dashboard principal del middleware.

## 📊 Paso 6: Visualizar Datos en el Dashboard

El dashboard principal del middleware está disponible en:

```
http://localhost:8000/dashboard/
```

Sin embargo, este dashboard actualmente muestra métricas del sistema. Para visualizar los datos específicos de temperatura y humedad, puedes:

### Opción 1: Usar la API directamente

```bash
# Obtener última temperatura
curl "http://localhost:8000/api/data?topic=iot/proyecto_demo/casa_living/dht22_esp32/temperatura&limit=1"

# Obtener última humedad
curl "http://localhost:8000/api/data?topic=iot/proyecto_demo/casa_living/dht22_esp32/humedad&limit=1"
```

### Opción 2: Crear una vista personalizada (próximamente)

Se puede extender el dashboard para mostrar gráficos de temperatura y humedad en tiempo real.

## 🔍 Verificación Final

### Checklist

- [ ] Proyecto `proyecto_demo` creado en la interfaz de administración
- [ ] Unidad `casa_living` creada y asignada al proyecto `proyecto_demo`
- [ ] Dispositivo `dht22_esp32` creado y asignado a la unidad `casa_living`
- [ ] ESP32 enviando datos MQTT correctamente
- [ ] Middleware recibiendo datos en los logs
- [ ] Datos consultables mediante API

### Verificar formato de tópicos

Los tópicos deben coincidir exactamente con:

- ✅ `iot/proyecto_demo/casa_living/dht22_esp32/temperatura`
- ✅ `iot/proyecto_demo/casa_living/dht22_esp32/humedad`

### Verificar formato JSON

El ESP32 envía datos en formato JSON. Verifica que el formato sea correcto:

```json
{
  "valor": 24.50,
  "unidad": "celsius",
  "timestamp": 1234567890,
  "tipo": "temperatura",
  "sensor_id": "esp32_dht22_001",
  "metadata": {
    "sensor_type": "DHT22",
    "location": "living_room",
    "pin": 4,
    "platform": "micropython_esp32"
  }
}
```

## 🐛 Solución de Problemas

### Los datos no aparecen en el middleware

1. **Verificar que el ESP32 esté enviando datos:**
   - Revisa el monitor serie del ESP32
   - Deberías ver mensajes como "📤 Temperatura: 24.50°C"

2. **Verificar conexión MQTT:**
   ```bash
   # Suscribirse a los tópicos manualmente
   mosquitto_sub -h 192.168.1.100 -p 1883 -u iot_user -P iot_password \
     -t "iot/proyecto_demo/casa_living/dht22_esp32/#" -v
   ```

3. **Verificar que el ingestor esté escuchando:**
   ```bash
   docker logs -f iotmw-ingestor
   ```

### El proyecto/unidad/dispositivo no aparece

1. **Verificar que se hayan creado correctamente:**
   - Revisa la lista en la interfaz de administración
   - Verifica que los IDs coincidan exactamente con los del tópico MQTT

2. **Verificar la base de datos:**
   ```bash
   # Conectar a PostgreSQL
   docker exec -it postgresql psql -U iot_user -d iot_middleware
   
   # Consultar proyectos
   SELECT * FROM iot_schema.proyectos;
   
   # Consultar unidades
   SELECT * FROM iot_schema.unidades_proyecto;
   
   # Consultar dispositivos
   SELECT * FROM iot_schema.dispositivos_proyecto;
   ```

### Los datos no se visualizan correctamente

1. **Verificar formato JSON:**
   - El JSON debe ser válido
   - Los campos requeridos deben estar presentes

2. **Verificar que los canales existan:**
   - Los canales (`temperatura`, `humedad`) se crean automáticamente cuando se reciben los primeros datos
   - Verifica en la base de datos:
     ```sql
     SELECT * FROM iot_schema.canales;
     ```

## 📚 Referencias

- Código ESP32: `examples/micropython_esp32_dht22.py`
- Interfaz de administración: `http://localhost:9000`
- Dashboard del middleware: `http://localhost:8000/dashboard/`
- API REST: `http://localhost:8000/api/`

## ✅ Resumen de IDs Necesarios

Para que todo funcione correctamente, asegúrate de usar estos IDs exactos:

| Tipo | ID | Ubicación en Tópico |
|------|----|-------------------|
| **Proyecto** | `proyecto_demo` | `iot/{proyecto_demo}/...` |
| **Unidad** | `casa_living` | `iot/proyecto_demo/{casa_living}/...` |
| **Dispositivo** | `dht22_esp32` | `iot/proyecto_demo/casa_living/{dht22_esp32}/...` |
| **Canal** | `temperatura` | `iot/.../dht22_esp32/{temperatura}` |
| **Canal** | `humedad` | `iot/.../dht22_esp32/{humedad}` |

¡Listo! Ahora deberías poder ver los datos de temperatura y humedad en el sistema. 🚀
