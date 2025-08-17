#!/usr/bin/env python3
"""
Script de Integración Simulada - InputManager con Middleware Core
================================================================

Este script demuestra la integración del InputManager con el middleware core
sin depender de conexiones externas (MQTT, HTTP, etc.).
"""

import sys
import os
import json
import time
from datetime import datetime

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

def demostrar_integracion():
    """Demuestra la integración del InputManager con el middleware core"""
    try:
        from iot_middleware.input import UnifiedDataFormat, DataQuality
        
        print("✅ Módulos importados correctamente")
        
        # Simular datos de diferentes protocolos
        print("\n🧪 SIMULANDO INTEGRACIÓN DE PROTOCOLOS")
        print("=" * 50)
        
        # Crear datos simulados de diferentes protocolos
        datos_protocolos = crear_datos_simulados()
        
        # Simular procesamiento en el middleware core
        print("\n🔄 PROCESANDO DATOS EN EL MIDDLEWARE CORE")
        print("=" * 50)
        
        for i, datos in enumerate(datos_protocolos):
            print(f"\n📨 Procesando datos {i+1}/{len(datos_protocolos)}")
            print(f"  - Protocolo: {datos.source_address.split('://')[0]}")
            print(f"  - Dispositivo: {datos.device_id}")
            print(f"  - Proyecto: {datos.project_id}")
            print(f"  - Mediciones: {datos.measurements}")
            print(f"  - Calidad: {datos.quality.value}")
            
            # Simular procesamiento en el core
            resultado = procesar_en_core_simulado(datos)
            print(f"  ✅ Resultado: {resultado}")
            
            time.sleep(0.5)  # Pausa para visualización
        
        # Mostrar resumen de integración
        mostrar_resumen_integracion(datos_protocolos)
        
        return True
        
    except Exception as e:
        print(f"❌ Error en demostración: {e}")
        import traceback
        traceback.print_exc()
        return False

def crear_datos_simulados():
    """Crea datos simulados de diferentes protocolos"""
    try:
        from iot_middleware.input import UnifiedDataFormat, DataQuality
        
        datos = []
        
        # Datos MQTT
        datos.append(UnifiedDataFormat(
            device_id="sensor_temperatura_001",
            project_id="proyecto_clima",
            timestamp=datetime.now().isoformat(),
            measurements={"temperature": 23.5, "humidity": 65.0},
            source_address="mqtt://localhost:1883/iot/proyecto_clima/sensor_temperatura_001",
            quality=DataQuality.VALID
        ))
        
        # Datos HTTP
        datos.append(UnifiedDataFormat(
            device_id="actuador_luz_001",
            project_id="proyecto_domotica",
            timestamp=datetime.now().isoformat(),
            measurements={"status": "on", "brightness": 80},
            source_address="http://localhost:8080/ingest",
            quality=DataQuality.VALID
        ))
        
        # Datos BLE
        datos.append(UnifiedDataFormat(
            device_id="tag_ble_001",
            project_id="proyecto_tracking",
            timestamp=datetime.now().isoformat(),
            measurements={"rssi": -45, "battery": 85},
            source_address="ble://00:11:22:33:44:55",
            quality=DataQuality.VALID
        ))
        
        # Datos LoRa
        datos.append(UnifiedDataFormat(
            device_id="nodo_lora_001",
            project_id="proyecto_agricultura",
            timestamp=datetime.now().isoformat(),
            measurements={"soil_moisture": 45.2, "air_temperature": 28.1},
            source_address="lora://gateway_001/app_001",
            quality=DataQuality.VALID
        ))
        
        # Datos MIDI
        datos.append(UnifiedDataFormat(
            device_id="teclado_midi_001",
            project_id="proyecto_musica",
            timestamp=datetime.now().isoformat(),
            measurements={"note": "C4", "velocity": 127, "channel": 0},
            source_address="midi://teclado_001",
            quality=DataQuality.VALID
        ))
        
        # Datos Modbus
        datos.append(UnifiedDataFormat(
            device_id="plc_modbus_001",
            project_id="proyecto_industrial",
            timestamp=datetime.now().isoformat(),
            measurements={"pressure": 2.5, "flow_rate": 15.3},
            source_address="modbus://192.168.1.100:502",
            quality=DataQuality.VALID
        ))
        
        # Datos ZigBee
        datos.append(UnifiedDataFormat(
            device_id="bombilla_zigbee_001",
            project_id="proyecto_iluminacion",
            timestamp=datetime.now().isoformat(),
            measurements={"power": "on", "brightness": 75, "color_temp": 2700},
            source_address="zigbee://coordinator_001",
            quality=DataQuality.VALID
        ))
        
        print(f"✅ Creados {len(datos)} tipos de datos de protocolos")
        return datos
        
    except Exception as e:
        print(f"❌ Error creando datos simulados: {e}")
        return []

def procesar_en_core_simulado(datos):
    """Simula el procesamiento en el middleware core existente"""
    try:
        # Simular diferentes tipos de procesamiento según el protocolo
        protocolo = datos.source_address.split('://')[0]
        
        if protocolo == "mqtt":
            # Simular procesamiento MQTT
            resultado = f"MQTT procesado - Tópico: iot/{datos.project_id}/{datos.device_id}/data"
            
        elif protocolo == "http":
            # Simular procesamiento HTTP
            resultado = f"HTTP procesado - Endpoint: /ingest/{datos.project_id}/{datos.device_id}"
            
        elif protocolo == "ble":
            # Simular procesamiento BLE
            resultado = f"BLE procesado - Dispositivo: {datos.source_address.split('://')[1]}"
            
        elif protocolo == "lora":
            # Simular procesamiento LoRa
            resultado = f"LoRa procesado - Gateway: {datos.source_address.split('://')[1]}"
            
        elif protocolo == "midi":
            # Simular procesamiento MIDI
            resultado = f"MIDI procesado - Nota: {datos.measurements.get('note', 'N/A')}"
            
        elif protocolo == "modbus":
            # Simular procesamiento Modbus
            resultado = f"Modbus procesado - PLC: {datos.source_address.split('://')[1]}"
            
        elif protocolo == "zigbee":
            # Simular procesamiento ZigBee
            resultado = f"ZigBee procesado - Coordinador: {datos.source_address.split('://')[1]}"
            
        else:
            resultado = f"Protocolo {protocolo} procesado - Desconocido"
        
        # Simular tiempo de procesamiento
        time.sleep(0.1)
        
        return resultado
        
    except Exception as e:
        return f"Error en procesamiento: {e}"

def mostrar_resumen_integracion(datos_protocolos):
    """Muestra un resumen de la integración"""
    try:
        print("\n" + "=" * 60)
        print("📊 RESUMEN DE INTEGRACIÓN - InputManager con Middleware Core")
        print("=" * 60)
        
        # Estadísticas por protocolo
        protocolos = {}
        for datos in datos_protocolos:
            protocolo = datos.source_address.split('://')[0]
            if protocolo not in protocolos:
                protocolos[protocolo] = 0
            protocolos[protocolo] += 1
        
        print(f"\n🔌 Protocolos Integrados: {len(protocolos)}")
        for protocolo, count in protocolos.items():
            print(f"  • {protocolo.upper()}: {count} dispositivo(s)")
        
        # Estadísticas generales
        print(f"\n📈 Estadísticas Generales:")
        print(f"  • Total de dispositivos: {len(datos_protocolos)}")
        print(f"  • Total de proyectos: {len(set(d.project_id for d in datos_protocolos))}")
        print(f"  • Calidad de datos: {len([d for d in datos_protocolos if d.quality.value == 'valid'])}/{len(datos_protocolos)} válidos")
        
        # Beneficios de la integración
        print(f"\n🎯 Beneficios de la Integración:")
        print(f"  ✅ Datos de múltiples protocolos convergiendo al mismo sistema")
        print(f"  ✅ Formato unificado para todos los datos")
        print(f"  ✅ Sin modificación del middleware core existente")
        print(f"  ✅ Escalabilidad para nuevos protocolos")
        print(f"  ✅ Monitoreo centralizado de todos los protocolos")
        
        # Próximos pasos
        print(f"\n🚀 Próximos Pasos Recomendados:")
        print(f"  1. Conectar con bases de datos reales (PostgreSQL, InfluxDB)")
        print(f"  2. Integrar con MQTTIngestaService existente")
        print(f"  3. Configurar persistencia automática de datos")
        print(f"  4. Implementar alertas y monitoreo en tiempo real")
        
        print("\n" + "=" * 60)
        
    except Exception as e:
        print(f"❌ Error mostrando resumen: {e}")

def main():
    """Función principal"""
    print("🔌 INTEGRACIÓN SIMULADA - InputManager con Middleware Core")
    print("=" * 60)
    print("Demostrando la integración multiprotocolo sin conexiones externas...")
    
    success = demostrar_integracion()
    
    if success:
        print("\n🎉 ¡Demostración de integración completada exitosamente!")
        print("📊 El InputManager está listo para integrarse con tu middleware core")
        print("🚀 Los datos de múltiples protocolos convergen al formato unificado")
    else:
        print("\n❌ Error en la demostración")
        sys.exit(1)

if __name__ == "__main__":
    main()
