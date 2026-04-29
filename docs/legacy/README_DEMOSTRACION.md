# 🚀 Sistema de Demostración - IoT Middleware

## 📋 Descripción General

Este sistema de demostración permite mostrar el **flujo completo de datos** desde el origen (simulado) hasta la persistencia, demostrando la capacidad del IoT Middleware para integrar múltiples protocolos de comunicación de manera modular.

## 🎯 Características Principales

### ✨ **Simuladores de Datos**
- **MQTT**: Sensores de temperatura, humedad, presión y actuadores
- **HTTP/REST**: Endpoints simulados para sensores y dispositivos
- **BLE**: Dispositivos Bluetooth Low Energy con datos de batería y RSSI
- **LoRa**: Gateways LoRaWAN con eventos uplink, join, ack y error
- **MIDI**: Controladores musicales con notas, control changes y pitch bend
- **Modbus**: Dispositivos industriales con registros de temperatura, presión y energía
- **ZigBee**: Dispositivos domóticos (sensores, switches, termostatos)

### 🔄 **Pipeline de Datos**
- **Normalización**: Conversión de datos a formato unificado
- **Validación**: Verificación de calidad y consistencia
- **Persistencia**: Almacenamiento en PostgreSQL e InfluxDB
- **Métricas**: Monitoreo en tiempo real del procesamiento

### 📊 **Generación de Informes**
- **JSON**: Datos estructurados para análisis
- **Texto**: Informes legibles por humanos
- **Gráficos**: Visualizaciones de métricas y rendimiento
- **Métricas**: Estadísticas detalladas por protocolo

## 🚀 Inicio Rápido

### 1. **Instalación de Dependencias**

```bash
# Dependencias básicas
pip install matplotlib numpy

# Dependencias opcionales para persistencia
pip install sqlalchemy psycopg2-binary influxdb-client
```

### 2. **Demostración Rápida**

```bash
# Ejecutar demostración interactiva
cd examples
python demo_rapida.py

# Seleccionar opción 1 para demo MQTT+HTTP (3 minutos)
```

### 3. **Demostración Completa**

```bash
# Demostración interactiva completa
python demo_completa.py

# Demostración con parámetros específicos
python demo_completa.py --protocols mqtt,http,ble --duration 10 --count 100
```

## 📁 Estructura del Sistema

```
src/iot_middleware/demo/
├── __init__.py              # Módulo principal
├── data_simulators.py       # Simuladores de protocolos
├── data_pipeline.py         # Pipeline de procesamiento
├── demo_manager.py          # Gestor de demostración
└── report_generator.py      # Generador de informes

examples/
├── demo_completa.py         # Script principal completo
└── demo_rapida.py          # Script de demostración rápida
```

## 🔧 Configuración

### **Configuración Básica**

```python
from iot_middleware.demo import DemoConfig, DemoManager

config = DemoConfig(
    name="Mi Demostración",
    duration_minutes=15,
    enable_protocols=["mqtt", "http", "ble"],
    data_interval=2.0,
    data_count_per_protocol=100,
    enable_pipeline=True,
    enable_postgresql=True,
    enable_influxdb=True,
    output_directory="mi_demo_output",
    generate_reports=True,
    real_time_monitoring=True
)

demo_manager = DemoManager(config)
demo_manager.initialize()
demo_manager.start()
```

### **Parámetros de Configuración**

| Parámetro | Descripción | Valor por Defecto |
|-----------|-------------|-------------------|
| `name` | Nombre de la demostración | "IoT Middleware Demo" |
| `duration_minutes` | Duración en minutos | 10 |
| `enable_protocols` | Lista de protocolos | Todos los disponibles |
| `data_interval` | Intervalo entre datos (seg) | 2.0 |
| `data_count_per_protocol` | Datos por protocolo | 50 |
| `enable_pipeline` | Habilitar pipeline | True |
| `enable_postgresql` | Habilitar PostgreSQL | True |
| `enable_influxdb` | Habilitar InfluxDB | True |
| `output_directory` | Directorio de salida | "demo_outputs" |
| `generate_reports` | Generar informes | True |
| `real_time_monitoring` | Monitoreo en tiempo real | True |

## 📊 Flujo de Datos

### **1. Simulación de Datos**
```
Simuladores → Datos Unificados → Callback Central
```

### **2. Procesamiento**
```
Callback → Cola de Procesamiento → Validación → Normalización
```

### **3. Persistencia**
```
Datos Normalizados → PostgreSQL (Entidades) + InfluxDB (Time Series)
```

### **4. Monitoreo**
```
Métricas en Tiempo Real → Logs → Informes → Gráficos
```

## 🎮 Uso Interactivo

### **Menú de Opciones**

```
🎯 DEMOSTRACIÓN RÁPIDA - IoT MIDDLEWARE
==================================================
Seleccione el tipo de demostración:
1. MQTT + HTTP (3 min)
2. Todos los protocolos (5 min)
3. Solo simulación (2 min)
4. Salir
```

### **Monitoreo en Tiempo Real**

```
⏱️  [2.5min] 📊 150 generados, 148 procesados, ⚡ 12.3 msg/s
🔌 Protocolos: MQTT:20/20, HTTP:20/20, BLE:15/20
```

## 📈 Informes Generados

### **Archivos de Salida**

```
demo_outputs/
├── reports/
│   ├── demo_report_20250116_143022.json    # Informe JSON
│   ├── demo_report_20250116_143022.txt     # Informe texto
│   └── summary_report_20250116_143022.json # Resumen
├── charts/
│   ├── protocol_data_chart_20250116_143022.png      # Gráfico protocolos
│   ├── processing_metrics_chart_20250116_143022.png # Gráfico pipeline
│   └── devices_chart_20250116_143022.png           # Gráfico dispositivos
└── demo_20250116_143022.log                         # Log completo
```

### **Contenido de Informes**

#### **Informe JSON**
```json
{
  "demo_config": {
    "name": "Demo Rápida MQTT+HTTP",
    "duration_minutes": 3,
    "enabled_protocols": ["mqtt", "http"],
    "data_interval": 1.0,
    "data_count_per_protocol": 20
  },
  "demo_metrics": {
    "total_data_generated": 40,
    "total_data_processed": 38,
    "errors": [],
    "warnings": []
  },
  "protocol_metrics": {
    "mqtt": {
      "data_generated": 20,
      "device_count": 20,
      "devices": ["mqtt_device_001", "mqtt_device_002", ...]
    },
    "http": {
      "data_generated": 20,
      "device_count": 15,
      "devices": ["http_device_001", "http_device_002", ...]
    }
  }
}
```

#### **Informe de Texto**
```
================================================================================
INFORME DE DEMOSTRACIÓN - IoT MIDDLEWARE
================================================================================

CONFIGURACIÓN DE LA DEMOSTRACIÓN
----------------------------------------
Nombre: Demo Rápida MQTT+HTTP
Duración: 3 minutos
Protocolos habilitados: mqtt, http
Intervalo de datos: 1.0 segundos
Datos por protocolo: 20

MÉTRICAS GENERALES
----------------------------------------
Total de datos generados: 40
Total de datos procesados: 38
Total de datos persistidos: 38
Errores: 0
Advertencias: 0

RESUMEN EJECUTIVO
----------------------------------------
La demostración procesó exitosamente 38 de 40 datos
generados por 2 protocolos diferentes.
Tasa de éxito: 95.0%
```

## 🔍 Puntos de Control por Módulos

### **1. Simuladores**
- ✅ **Estado**: Activo/Inactivo
- 📊 **Datos generados**: Contador en tiempo real
- 🔌 **Dispositivos**: Lista de dispositivos únicos
- ⏱️ **Última actividad**: Timestamp del último dato

### **2. Pipeline de Datos**
- ✅ **Estado**: Activo/Inactivo
- 📈 **Rate de procesamiento**: Mensajes por segundo
- 🗄️ **Operaciones BD**: Contadores PostgreSQL/InfluxDB
- ⚠️ **Tasa de error**: Porcentaje de errores
- 📦 **Tamaño de cola**: Mensajes pendientes

### **3. Almacenamiento**
- 🔗 **PostgreSQL**: Estado de conexión
- 📊 **InfluxDB**: Estado de conexión
- 📝 **Operaciones**: Contadores de éxito/fallo
- ⏱️ **Última operación**: Timestamp de la última BD

## 🚀 Ejemplos de Uso

### **Ejemplo 1: Demostración Básica**

```bash
# Demostración rápida de 3 minutos con MQTT y HTTP
python demo_rapida.py
# Seleccionar opción 1
```

### **Ejemplo 2: Demostración Personalizada**

```bash
# Demostración de 15 minutos con todos los protocolos
python demo_completa.py \
  --protocols mqtt,http,ble,lora,midi,modbus,zigbee \
  --duration 15 \
  --count 200 \
  --interval 1.5
```

### **Ejemplo 3: Solo Simulación**

```bash
# Demostración sin persistencia (solo simulación)
python demo_completa.py \
  --no-pipeline \
  --duration 10 \
  --protocols mqtt,http,ble
```

### **Ejemplo 4: Demostración Interactiva**

```bash
# Configuración paso a paso
python demo_completa.py
# Seguir el menú interactivo
```

## 📊 Métricas y Monitoreo

### **Métricas en Tiempo Real**

- **Datos generados**: Total por protocolo
- **Datos procesados**: Total procesados por el pipeline
- **Rate de procesamiento**: Mensajes por segundo
- **Errores y advertencias**: Contadores y descripciones
- **Estado de protocolos**: Activo/Inactivo con contadores

### **Gráficos Generados**

1. **Datos por Protocolo**: Barras comparando generados vs procesados
2. **Métricas del Pipeline**: Distribución de mensajes, rate, operaciones BD
3. **Dispositivos por Protocolo**: Conteo de dispositivos únicos

## 🛠️ Solución de Problemas

### **Problemas Comunes**

#### **1. Error de Importación**
```bash
# Asegurarse de estar en el directorio correcto
cd examples
python demo_rapida.py
```

#### **2. Dependencias Faltantes**
```bash
# Instalar matplotlib para gráficos
pip install matplotlib numpy
```

#### **3. Permisos de Directorio**
```bash
# Crear directorio de salida manualmente
mkdir -p demo_outputs
```

#### **4. Interrumpir Demostración**
```bash
# Usar Ctrl+C para detener manualmente
# El sistema se detendrá de forma segura
```

### **Logs y Debugging**

- **Logs detallados**: En `demo_outputs/demo_YYYYMMDD_HHMMSS.log`
- **Estado en tiempo real**: Monitoreo cada 30 segundos
- **Métricas por protocolo**: Estado individual de cada simulador

## 🔧 Personalización Avanzada

### **Crear Simulador Personalizado**

```python
from iot_middleware.demo.data_simulators import BaseSimulator, SimulatorConfig

class MiSimulador(BaseSimulator):
    def _generate_data(self):
        # Implementar lógica de generación personalizada
        return UnifiedDataFormat(...)

# Usar en configuración
config = DemoConfig(
    enable_protocols=["mi_protocolo"],
    # ... otras configuraciones
)
```

### **Configurar Pipeline Personalizado**

```python
from iot_middleware.demo.data_pipeline import PipelineConfig

pipeline_config = PipelineConfig(
    batch_size=200,
    batch_timeout=10.0,
    enable_postgresql=True,
    enable_influxdb=True
)
```

## 📚 Referencias

### **Archivos Relacionados**
- `README_MULTI_PROTOCOL.md`: Documentación de la arquitectura multi-protocolo
- `examples/config_multi_protocol.yaml`: Configuración de ejemplo
- `examples/multi_protocol_example.py`: Ejemplo básico de uso

### **Dependencias Principales**
- `matplotlib`: Generación de gráficos
- `numpy`: Procesamiento numérico
- `sqlalchemy`: Persistencia PostgreSQL (opcional)
- `influxdb-client`: Persistencia InfluxDB (opcional)

## 🎉 Conclusión

Este sistema de demostración proporciona una **visión completa y práctica** del IoT Middleware, permitiendo:

1. **Verificar la funcionalidad** de cada protocolo individualmente
2. **Demostrar la integración** multi-protocolo
3. **Validar el pipeline** de procesamiento de datos
4. **Generar informes** detallados con métricas y gráficos
5. **Monitorear en tiempo real** el rendimiento del sistema

**¡Con esta herramienta puedes demostrar fácilmente la capacidad de tu IoT Middleware para integrar cualquier protocolo de comunicación manteniendo la compatibilidad con tu sistema existente!** 🚀
