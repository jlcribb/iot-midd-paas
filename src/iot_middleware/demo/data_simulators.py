"""
Simuladores de Datos - IoT Middleware
=====================================

Este módulo contiene simuladores que generan datos realistas para cada protocolo,
permitiendo demostrar el flujo completo de datos sin necesidad de dispositivos físicos.
"""

import json
import random
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
import math

from ..input.base_connector import UnifiedDataFormat, DataQuality


@dataclass
class SimulatorConfig:
    """Configuración base para simuladores"""
    enabled: bool = True
    name: str = ""
    protocol: str = ""
    data_interval: float = 5.0  # Segundos entre datos
    data_count: int = 100  # Número total de datos a generar
    jitter: float = 0.1  # Variación aleatoria en el intervalo
    quality_variation: bool = True  # Simular variaciones en calidad de datos


class BaseSimulator:
    """Simulador base para todos los protocolos"""
    
    def __init__(self, config: SimulatorConfig, data_callback: Optional[Callable[[UnifiedDataFormat], None]] = None):
        self.config = config
        self.data_callback = data_callback
        self.running = False
        self.simulation_thread = None
        self.data_generated = 0
        self.start_time = None
        self.last_data_time = None
        
    def start(self):
        """Iniciar simulación"""
        if self.running:
            return False
            
        self.running = True
        self.start_time = datetime.now()
        self.simulation_thread = threading.Thread(target=self._simulation_loop, daemon=True)
        self.simulation_thread.start()
        return True
        
    def stop(self):
        """Detener simulación"""
        self.running = False
        if self.simulation_thread:
            self.simulation_thread.join(timeout=5.0)
            
    def _simulation_loop(self):
        """Bucle principal de simulación"""
        while self.running and self.data_generated < self.config.data_count:
            try:
                # Generar datos
                data = self._generate_data()
                if data and self.data_callback:
                    self.data_callback(data)
                    
                self.data_generated += 1
                self.last_data_time = datetime.now()
                
                # Esperar hasta el próximo intervalo
                interval = self.config.data_interval * (1 + random.uniform(-self.config.jitter, self.config.jitter))
                time.sleep(interval)
                
            except Exception as e:
                print(f"Error en simulación {self.config.name}: {e}")
                time.sleep(1.0)
                
    def _generate_data(self) -> Optional[UnifiedDataFormat]:
        """Generar datos específicos del protocolo - debe ser implementado por subclases"""
        raise NotImplementedError
        
    def get_status(self) -> Dict[str, Any]:
        """Obtener estado del simulador"""
        return {
            'name': self.config.name,
            'protocol': self.config.protocol,
            'running': self.running,
            'data_generated': self.data_generated,
            'data_count': self.config.data_count,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'last_data_time': self.last_data_time.isoformat() if self.last_data_time else None
        }


class MQTTSimulator(BaseSimulator):
    """Simulador de datos MQTT"""
    
    def __init__(self, config: SimulatorConfig, data_callback=None):
        super().__init__(config, data_callback)
        self.topics = [
            "sensors/temperature/+/data",
            "sensors/humidity/+/data", 
            "sensors/pressure/+/data",
            "actuators/+/status",
            "devices/+/telemetry"
        ]
        self.device_ids = [f"mqtt_device_{i:03d}" for i in range(1, 21)]
        
    def _generate_data(self) -> Optional[UnifiedDataFormat]:
        topic = random.choice(self.topics)
        device_id = random.choice(self.device_ids)
        
        # Generar datos según el tipo de sensor
        if "temperature" in topic:
            measurements = {
                "temperature": round(random.uniform(15.0, 35.0), 2),
                "timestamp_device": datetime.now().isoformat()
            }
        elif "humidity" in topic:
            measurements = {
                "humidity": round(random.uniform(30.0, 80.0), 2),
                "timestamp_device": datetime.now().isoformat()
            }
        elif "pressure" in topic:
            measurements = {
                "pressure": round(random.uniform(980.0, 1020.0), 2),
                "timestamp_device": datetime.now().isoformat()
            }
        elif "actuators" in topic:
            measurements = {
                "status": random.choice(["on", "off", "error"]),
                "power": round(random.uniform(0.0, 100.0), 2),
                "timestamp_device": datetime.now().isoformat()
            }
        else:
            measurements = {
                "voltage": round(random.uniform(3.0, 5.0), 3),
                "current": round(random.uniform(0.0, 2.0), 3),
                "timestamp_device": datetime.now().isoformat()
            }
            
        return UnifiedDataFormat(
            device_id=device_id,
            project_id="demo_mqtt_project",
            timestamp=datetime.now(),
            measurements=measurements,
            metadata={
                "topic": topic,
                "qos": random.choice([0, 1, 2]),
                "retain": random.choice([True, False])
            },
            quality=DataQuality.VALID if random.random() > 0.05 else DataQuality.ERROR,
            source_protocol="mqtt",
            source_address="mqtt://localhost:1883"
        )


class HTTPSimulator(BaseSimulator):
    """Simulador de datos HTTP/REST"""
    
    def __init__(self, config: SimulatorConfig, data_callback=None):
        super().__init__(config, data_callback)
        self.endpoints = [
            "/api/v1/sensors",
            "/api/v1/actuators", 
            "/api/v1/devices",
            "/webhook/iot",
            "/ingest/data"
        ]
        self.device_ids = [f"http_device_{i:03d}" for i in range(1, 16)]
        
    def _generate_data(self) -> Optional[UnifiedDataFormat]:
        endpoint = random.choice(self.endpoints)
        device_id = random.choice(self.device_ids)
        
        # Generar datos según el endpoint
        if "sensors" in endpoint:
            measurements = {
                "temperature": round(random.uniform(18.0, 32.0), 2),
                "humidity": round(random.uniform(40.0, 70.0), 2),
                "light": round(random.uniform(0.0, 1000.0), 2),
                "motion": random.choice([True, False])
            }
        elif "actuators" in endpoint:
            measurements = {
                "relay_state": random.choice([True, False]),
                "dimmer_level": random.randint(0, 100),
                "fan_speed": random.randint(0, 3)
            }
        elif "devices" in endpoint:
            measurements = {
                "battery": round(random.uniform(20.0, 100.0), 2),
                "signal_strength": random.randint(-80, -30),
                "uptime": random.randint(1000, 86400)
            }
        else:
            measurements = {
                "value": round(random.uniform(0.0, 100.0), 2),
                "unit": random.choice(["celsius", "percent", "lux", "volts"])
            }
            
        return UnifiedDataFormat(
            device_id=device_id,
            project_id="demo_http_project",
            timestamp=datetime.now(),
            measurements=measurements,
            metadata={
                "endpoint": endpoint,
                "method": "POST",
                "content_type": "application/json",
                "user_agent": "IoT-Simulator/1.0"
            },
            quality=DataQuality.VALID if random.random() > 0.03 else DataQuality.INVALID,
            source_protocol="http",
            source_address="http://localhost:8080"
        )


class BLESimulator(BaseSimulator):
    """Simulador de datos BLE"""
    
    def __init__(self, config: SimulatorConfig, data_callback=None):
        super().__init__(config, data_callback)
        self.device_macs = [f"AA:BB:CC:DD:EE:{i:02X}" for i in range(1, 16)]
        self.device_names = [
            "BLE_Temp_Sensor", "BLE_Humidity", "BLE_Beacon", 
            "BLE_Tag", "BLE_Health_Monitor"
        ]
        
    def _generate_data(self) -> Optional[UnifiedDataFormat]:
        mac = random.choice(self.device_macs)
        name = random.choice(self.device_names)
        device_id = f"ble_{mac.replace(':', '')}"
        
        # Generar datos según el tipo de dispositivo
        if "Temp" in name:
            measurements = {
                "temperature": round(random.uniform(20.0, 30.0), 2),
                "battery": round(random.uniform(50.0, 100.0), 2),
                "rssi": random.randint(-70, -30)
            }
        elif "Humidity" in name:
            measurements = {
                "humidity": round(random.uniform(45.0, 75.0), 2),
                "battery": round(random.uniform(60.0, 100.0), 2),
                "rssi": random.randint(-65, -25)
            }
        elif "Beacon" in name:
            measurements = {
                "major": random.randint(1, 65535),
                "minor": random.randint(1, 65535),
                "rssi": random.randint(-80, -40),
                "tx_power": random.randint(-60, -20)
            }
        else:
            measurements = {
                "value": round(random.uniform(0.0, 100.0), 2),
                "battery": round(random.uniform(30.0, 100.0), 2),
                "rssi": random.randint(-75, -35)
            }
            
        return UnifiedDataFormat(
            device_id=device_id,
            project_id="demo_ble_project",
            timestamp=datetime.now(),
            measurements=measurements,
            metadata={
                "mac_address": mac,
                "device_name": name,
                "manufacturer_data": f"0x{random.randint(0, 0xFFFF):04X}",
                "service_uuid": f"0000{random.randint(0, 0xFFFF):04X}-0000-1000-8000-00805f9b34fb"
            },
            quality=DataQuality.VALID if random.random() > 0.08 else DataQuality.OUT_OF_RANGE,
            source_protocol="ble",
            source_address=mac
        )


class LoRaSimulator(BaseSimulator):
    """Simulador de datos LoRa/LoRaWAN"""
    
    def __init__(self, config: SimulatorConfig, data_callback=None):
        super().__init__(config, data_callback)
        self.device_euis = [f"000000000000{random.randint(1000, 9999):04d}" for _ in range(10)]
        self.application_ids = ["demo_app_01", "demo_app_02", "demo_app_03"]
        
    def _generate_data(self) -> Optional[UnifiedDataFormat]:
        device_eui = random.choice(self.device_euis)
        app_id = random.choice(self.application_ids)
        device_id = f"lora_{device_eui[-8:]}"
        
        # Simular diferentes tipos de eventos LoRa
        event_type = random.choice(["uplink", "join", "ack", "error"])
        
        if event_type == "uplink":
            # Simular payload codificado en base64
            payload_data = {
                "temperature": round(random.uniform(10.0, 40.0), 2),
                "humidity": round(random.uniform(20.0, 90.0), 2),
                "battery": round(random.uniform(10.0, 100.0), 2)
            }
            import base64
            payload_bytes = json.dumps(payload_data).encode()
            payload_base64 = base64.b64encode(payload_bytes).decode()
            
            measurements = {
                "event_type": "uplink",
                "payload": payload_base64,
                "payload_decoded": payload_data,
                "f_cnt": random.randint(1, 10000),
                "f_port": random.randint(1, 223),
                "dr": random.randint(0, 7),
                "rssi": random.randint(-120, -80),
                "snr": round(random.uniform(-20.0, 10.0), 2)
            }
        elif event_type == "join":
            measurements = {
                "event_type": "join",
                "join_eui": f"000000000000{random.randint(1000, 9999):04d}",
                "dev_nonce": random.randint(0, 65535),
                "join_accept_delay": random.randint(1, 5)
            }
        elif event_type == "ack":
            measurements = {
                "event_type": "ack",
                "f_cnt": random.randint(1, 10000),
                "ack_status": random.choice(["confirmed", "unconfirmed"])
            }
        else:  # error
            measurements = {
                "event_type": "error",
                "error_code": random.randint(1, 10),
                "error_message": random.choice([
                    "CRC error", "Invalid frame", "No network", "Rate limit exceeded"
                ])
            }
            
        return UnifiedDataFormat(
            device_id=device_id,
            project_id="demo_lora_project",
            timestamp=datetime.now(),
            measurements=measurements,
            metadata={
                "device_eui": device_eui,
                "application_id": app_id,
                "gateway_id": f"gateway_{random.randint(1, 5):02d}",
                "frequency": round(random.uniform(868.0, 870.0), 3),
                "bandwidth": random.choice([125, 250, 500])
            },
            quality=DataQuality.VALID if event_type != "error" else DataQuality.ERROR,
            source_protocol="lora",
            source_address=f"{app_id}:{device_eui}"
        )


class MIDISimulator(BaseSimulator):
    """Simulador de datos MIDI"""
    
    def __init__(self, config: SimulatorConfig, data_callback=None):
        super().__init__(config, data_callback)
        self.channels = list(range(16))
        self.note_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
        self.message_types = ["note_on", "note_off", "control_change", "program_change", "pitch_bend"]
        
    def _generate_data(self) -> Optional[UnifiedDataFormat]:
        channel = random.choice(self.channels)
        message_type = random.choice(self.message_types)
        device_id = f"midi_channel_{channel:02d}"
        
        if message_type in ["note_on", "note_off"]:
            note = random.randint(21, 108)  # MIDI note range
            note_name = self.note_names[note % 12]
            octave = (note // 12) - 1
            frequency = 440 * (2 ** ((note - 69) / 12))
            
            measurements = {
                "message_type": message_type,
                "note": note,
                "note_name": f"{note_name}{octave}",
                "frequency": round(frequency, 2),
                "velocity": random.randint(1, 127),
                "channel": channel
            }
        elif message_type == "control_change":
            controller = random.randint(0, 127)
            value = random.randint(0, 127)
            controller_names = {
                1: "modulation", 7: "volume", 10: "pan", 
                11: "expression", 64: "sustain", 91: "reverb"
            }
            
            measurements = {
                "message_type": message_type,
                "controller": controller,
                "controller_name": controller_names.get(controller, "unknown"),
                "value": value,
                "channel": channel
            }
        elif message_type == "program_change":
            program = random.randint(1, 128)
            measurements = {
                "message_type": message_type,
                "program": program,
                "channel": channel
            }
        else:  # pitch_bend
            bend_value = random.randint(-8192, 8191)
            bend_semitones = round((bend_value / 8192) * 12, 2)
            
            measurements = {
                "message_type": message_type,
                "bend_value": bend_value,
                "bend_semitones": bend_semitones,
                "channel": channel
            }
            
        return UnifiedDataFormat(
            device_id=device_id,
            project_id="demo_midi_project",
            timestamp=datetime.now(),
            measurements=measurements,
            metadata={
                "port_name": f"MIDI Port {random.randint(1, 4)}",
                "device_type": "MIDI Controller",
                "timestamp_device": datetime.now().isoformat()
            },
            quality=DataQuality.VALID if random.random() > 0.02 else DataQuality.INVALID,
            source_protocol="midi",
            source_address=f"midi://channel_{channel}"
        )


class ModbusSimulator(BaseSimulator):
    """Simulador de datos Modbus"""
    
    def __init__(self, config: SimulatorConfig, data_callback=None):
        super().__init__(config, data_callback)
        self.register_configs = {
            "temperature": {"address": 1000, "type": "float32", "unit": "°C"},
            "pressure": {"address": 1002, "type": "float32", "unit": "bar"},
            "flow_rate": {"address": 1004, "type": "float32", "unit": "L/min"},
            "status": {"address": 1006, "type": "int16", "unit": "status"},
            "alarm": {"address": 1007, "type": "int16", "unit": "alarm"},
            "energy": {"address": 1008, "type": "int32", "unit": "kWh"}
        }
        self.device_ids = [f"modbus_device_{i:03d}" for i in range(1, 11)]
        
    def _generate_data(self) -> Optional[UnifiedDataFormat]:
        device_id = random.choice(self.device_ids)
        register_name = random.choice(list(self.register_configs.keys()))
        register_config = self.register_configs[register_name]
        
        # Generar valor según el tipo de registro
        if register_config["type"] == "float32":
            if register_name == "temperature":
                value = round(random.uniform(20.0, 80.0), 2)
            elif register_name == "pressure":
                value = round(random.uniform(1.0, 10.0), 2)
            else:  # flow_rate
                value = round(random.uniform(0.0, 100.0), 2)
        elif register_config["type"] == "int16":
            if register_name == "status":
                value = random.choice([0, 1, 2, 3])  # off, on, error, maintenance
            else:  # alarm
                value = random.choice([0, 1])  # no alarm, alarm
        else:  # int32 - energy
            value = random.randint(1000, 99999)
            
        measurements = {
            "register_name": register_name,
            "register_address": register_config["address"],
            "register_type": register_config["type"],
            "value": value,
            "unit": register_config["unit"],
            "timestamp_device": datetime.now().isoformat()
        }
        
        return UnifiedDataFormat(
            device_id=device_id,
            project_id="demo_modbus_project",
            timestamp=datetime.now(),
            measurements=measurements,
            metadata={
                "protocol": random.choice(["tcp", "rtu", "ascii"]),
                "device_id": random.randint(1, 247),
                "baud_rate": random.choice([9600, 19200, 38400, 57600, 115200])
            },
            quality=DataQuality.VALID if random.random() > 0.04 else DataQuality.OUT_OF_RANGE,
            source_protocol="modbus",
            source_address=f"modbus://{device_id}"
        )


class ZigBeeSimulator(BaseSimulator):
    """Simulador de datos ZigBee"""
    
    def __init__(self, config: SimulatorConfig, data_callback=None):
        super().__init__(config, data_callback)
        self.device_names = [
            "Living_Room_Temp", "Kitchen_Humidity", "Bedroom_Motion",
            "Garage_Door", "Smart_Plug_01", "Thermostat_01"
        ]
        self.device_types = {
            "Living_Room_Temp": "sensor",
            "Kitchen_Humidity": "sensor", 
            "Bedroom_Motion": "sensor",
            "Garage_Door": "lock",
            "Smart_Plug_01": "switch",
            "Thermostat_01": "thermostat"
        }
        
    def _generate_data(self) -> Optional[UnifiedDataFormat]:
        device_name = random.choice(self.device_names)
        device_type = self.device_types[device_name]
        device_id = f"zigbee_{device_name.lower().replace('_', '')}"
        
        # Generar datos según el tipo de dispositivo
        if device_type == "sensor":
            if "Temp" in device_name:
                measurements = {
                    "temperature": round(random.uniform(18.0, 28.0), 2),
                    "battery": round(random.uniform(60.0, 100.0), 2),
                    "linkquality": random.randint(10, 100)
                }
            elif "Humidity" in device_name:
                measurements = {
                    "humidity": round(random.uniform(40.0, 70.0), 2),
                    "battery": round(random.uniform(70.0, 100.0), 2),
                    "linkquality": random.randint(15, 100)
                }
            else:  # Motion
                measurements = {
                    "motion": random.choice([True, False]),
                    "battery": round(random.uniform(80.0, 100.0), 2),
                    "linkquality": random.randint(20, 100)
                }
        elif device_type == "lock":
            measurements = {
                "lock_state": random.choice(["locked", "unlocked", "jammed"]),
                "battery": round(random.uniform(50.0, 100.0), 2),
                "linkquality": random.randint(25, 100)
            }
        elif device_type == "switch":
            measurements = {
                "state": random.choice(["on", "off"]),
                "power": round(random.uniform(0.0, 100.0), 2),
                "energy": round(random.uniform(0.0, 10.0), 3),
                "linkquality": random.randint(30, 100)
            }
        else:  # thermostat
            measurements = {
                "current_temperature": round(random.uniform(18.0, 26.0), 2),
                "target_temperature": round(random.uniform(20.0, 24.0), 2),
                "mode": random.choice(["heat", "cool", "auto", "off"]),
                "battery": round(random.uniform(40.0, 100.0), 2),
                "linkquality": random.randint(35, 100)
            }
            
        return UnifiedDataFormat(
            device_id=device_id,
            project_id="demo_zigbee_project",
            timestamp=datetime.now(),
            measurements=measurements,
            metadata={
                "device_name": device_name,
                "device_type": device_type,
                "ieee_address": f"0x{random.randint(0, 0xFFFFFFFFFFFFFFFF):016X}",
                "friendly_name": device_name,
                "manufacturer": random.choice(["Philips", "IKEA", "Xiaomi", "Tuya"])
            },
            quality=DataQuality.VALID if random.random() > 0.06 else DataQuality.ERROR,
            source_protocol="zigbee",
            source_address=f"zigbee://{device_name}"
        )
