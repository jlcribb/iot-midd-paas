"""
Conector MIDI - IoT Middleware
==============================

Permite recibir datos desde dispositivos MIDI (Interfaz Digital de Instrumentos Musicales).
Útil para monitorear instrumentos musicales, controladores, y equipos de audio.
"""

import json
import logging
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List
from dataclasses import dataclass

from ..base_connector import BaseConnector, ConnectorConfig, UnifiedDataFormat, DataQuality, ConnectorStatus


@dataclass
class MIDIConnectorConfig(ConnectorConfig):
    """Configuración específica para el conector MIDI"""
    # Configuración del puerto MIDI
    port_name: Optional[str] = None  # Nombre específico del puerto
    port_number: Optional[int] = None  # Número del puerto
    virtual_port: bool = False  # Crear puerto virtual
    
    # Configuración de filtros
    channel_filter: List[int] = None  # Canales MIDI a escuchar (1-16)
    message_types: List[str] = None  # Tipos de mensajes a procesar
    note_range: tuple = (0, 127)  # Rango de notas a procesar
    
    # Configuración de datos
    parse_notes: bool = True
    parse_controllers: bool = True
    parse_sysex: bool = False
    parse_timing: bool = True
    velocity_threshold: int = 0  # Umbral mínimo de velocidad
    
    def __post_init__(self):
        if self.channel_filter is None:
            self.channel_filter = list(range(1, 17))  # Todos los canales
        if self.message_types is None:
            self.message_types = ["note_on", "note_off", "control_change", "program_change"]


class MIDIConnector(BaseConnector):
    """
    Conector MIDI que recibe datos desde dispositivos musicales
    
    Este conector se conecta a dispositivos MIDI y procesa mensajes
    como notas, controladores, y cambios de programa.
    """
    
    def __init__(self, config: MIDIConnectorConfig, data_callback=None):
        super().__init__(config, data_callback)
        
        # Configuración específica de MIDI
        self.midi_config = MIDIConnectorConfig(**config.__dict__) if isinstance(config, ConnectorConfig) else config
        
        # Puerto MIDI
        self.midi_port = None
        self.midi_input = None
        
        # Estado de dispositivos MIDI
        self.connected_devices: Dict[str, Dict[str, Any]] = {}
        self.active_notes: Dict[int, Dict[str, Any]] = {}  # channel -> note info
        
        # Logging específico
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
    
    def connect(self) -> bool:
        """Conecta al dispositivo MIDI"""
        try:
            self.logger.info(f"🎵 Conectando a dispositivo MIDI")
            
            # Intentar importar biblioteca MIDI
            try:
                import mido
                self.logger.info("✅ Biblioteca mido disponible")
            except ImportError:
                self.logger.error("❌ Biblioteca mido no disponible. Instala con: pip install mido")
                return False
            
            # Obtener puertos MIDI disponibles
            available_ports = mido.get_input_names()
            self.logger.info(f"Puertos MIDI disponibles: {available_ports}")
            
            # Seleccionar puerto
            selected_port = self._select_midi_port(available_ports)
            if not selected_port:
                self.logger.error("❌ No se pudo seleccionar puerto MIDI")
                return False
            
            # Abrir puerto MIDI
            try:
                self.midi_input = mido.open_input(selected_port, callback=self._on_midi_message)
                self.midi_port = selected_port
                
                self.status = ConnectorStatus.CONNECTED
                self.connected = True
                self.last_connection_time = datetime.now(timezone.utc)
                
                self.logger.info(f"✅ Conectado al puerto MIDI: {selected_port}")
                return True
                
            except Exception as e:
                self.logger.error(f"❌ Error abriendo puerto MIDI {selected_port}: {e}")
                return False
                
        except Exception as e:
            self.logger.error(f"❌ Error conectando a MIDI: {e}")
            self.status = ConnectorStatus.ERROR
            self._handle_connection_error(e)
            return False
    
    def disconnect(self) -> bool:
        """Desconecta del dispositivo MIDI"""
        try:
            if self.midi_input:
                self.midi_input.close()
                self.midi_input = None
            
            self.status = ConnectorStatus.DISCONNECTED
            self.connected = False
            self.connected_devices.clear()
            self.active_notes.clear()
            
            self.logger.info("✅ Desconectado del dispositivo MIDI")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Error desconectando de MIDI: {e}")
            return False
    
    def is_connected(self) -> bool:
        """Verifica si está conectado al dispositivo MIDI"""
        return self.connected and self.midi_input is not None
    
    def _receive_data(self) -> Optional[Any]:
        """
        Recibe datos del dispositivo MIDI
        
        Los datos se reciben de forma asíncrona a través del callback.
        No necesitamos implementar polling aquí.
        """
        return None
    
    def _parse_raw_data(self, raw_data: Any) -> Optional[UnifiedDataFormat]:
        """
        Parsea datos MIDI al formato unificado
        
        Args:
            raw_data: Mensaje MIDI
            
        Returns:
            Datos en formato unificado
        """
        try:
            if not hasattr(raw_data, 'type'):
                self.logger.warning(f"Formato de datos MIDI no reconocido: {type(raw_data)}")
                return None
            
            # Extraer información básica del mensaje MIDI
            message_type = raw_data.type
            channel = getattr(raw_data, 'channel', 0) + 1  # MIDI usa 0-15, convertimos a 1-16
            
            # Verificar filtros
            if channel not in self.midi_config.channel_filter:
                return None
            
            if message_type not in self.midi_config.message_types:
                return None
            
            # Parsear datos según el tipo de mensaje
            measurements = self._parse_midi_message(raw_data, message_type, channel)
            
            # Crear datos unificados
            unified_data = UnifiedDataFormat(
                device_id=f"midi_ch{channel:02d}",
                project_id="midi_music",
                timestamp=datetime.now(timezone.utc),
                measurements=measurements,
                metadata={
                    'message_type': message_type,
                    'channel': channel,
                    'port': self.midi_port,
                    'midi_message': str(raw_data),
                    'timestamp_midi': time.time()
                },
                quality=DataQuality.VALID,
                source_protocol='midi',
                source_address=f"{self.midi_port}:ch{channel}",
                raw_data=raw_data
            )
            
            return unified_data
            
        except Exception as e:
            self.logger.error(f"Error parseando datos MIDI: {e}")
            return None
    
    def _parse_midi_message(self, message, message_type: str, channel: int) -> Dict[str, Any]:
        """Parsea un mensaje MIDI específico"""
        try:
            measurements = {
                'message_type': message_type,
                'channel': channel
            }
            
            if message_type == "note_on":
                measurements.update(self._parse_note_on(message, channel))
            elif message_type == "note_off":
                measurements.update(self._parse_note_off(message, channel))
            elif message_type == "control_change":
                measurements.update(self._parse_control_change(message, channel))
            elif message_type == "program_change":
                measurements.update(self._parse_program_change(message, channel))
            elif message_type == "pitch_bend":
                measurements.update(self._parse_pitch_bend(message, channel))
            elif message_type == "aftertouch":
                measurements.update(self._parse_aftertouch(message, channel))
            else:
                measurements['raw_data'] = str(message)
            
            return measurements
            
        except Exception as e:
            self.logger.error(f"Error parseando mensaje MIDI {message_type}: {e}")
            return {'error': str(e)}
    
    def _parse_note_on(self, message, channel: int) -> Dict[str, Any]:
        """Parsea mensaje note_on"""
        try:
            note = message.note
            velocity = message.velocity
            
            # Verificar filtros
            if not (self.midi_config.note_range[0] <= note <= self.midi_config.note_range[1]):
                return {}
            
            if velocity < self.midi_config.velocity_threshold:
                return {}
            
            # Convertir nota a nombre musical
            note_name = self._note_number_to_name(note)
            
            # Actualizar notas activas
            self.active_notes[channel] = {
                'note': note,
                'note_name': note_name,
                'velocity': velocity,
                'timestamp': time.time()
            }
            
            return {
                'note': note,
                'note_name': note_name,
                'velocity': velocity,
                'note_frequency': self._note_to_frequency(note),
                'event': 'note_on'
            }
            
        except Exception as e:
            self.logger.error(f"Error parseando note_on: {e}")
            return {'error': str(e)}
    
    def _parse_note_off(self, message, channel: int) -> Dict[str, Any]:
        """Parsea mensaje note_off"""
        try:
            note = message.note
            velocity = message.velocity
            
            # Convertir nota a nombre musical
            note_name = self._note_number_to_name(note)
            
            # Remover de notas activas
            if channel in self.active_notes and self.active_notes[channel].get('note') == note:
                del self.active_notes[channel]
            
            return {
                'note': note,
                'note_name': note_name,
                'velocity': velocity,
                'note_frequency': self._note_to_frequency(note),
                'event': 'note_off'
            }
            
        except Exception as e:
            self.logger.error(f"Error parseando note_off: {e}")
            return {'error': str(e)}
    
    def _parse_control_change(self, message, channel: int) -> Dict[str, Any]:
        """Parsea mensaje control_change"""
        try:
            control = message.control
            value = message.value
            
            # Nombres de controles comunes
            control_names = {
                1: "modulation_wheel",
                7: "volume",
                10: "pan",
                11: "expression",
                64: "sustain_pedal",
                65: "portamento",
                71: "resonance",
                72: "release_time",
                73: "attack_time",
                74: "brightness",
                91: "reverb",
                93: "chorus"
            }
            
            control_name = control_names.get(control, f"control_{control}")
            
            return {
                'control': control,
                'control_name': control_name,
                'value': value,
                'value_normalized': value / 127.0,  # Normalizar a 0-1
                'event': 'control_change'
            }
            
        except Exception as e:
            self.logger.error(f"Error parseando control_change: {e}")
            return {'error': str(e)}
    
    def _parse_program_change(self, message, channel: int) -> Dict[str, Any]:
        """Parsea mensaje program_change"""
        try:
            program = message.program
            
            return {
                'program': program,
                'program_name': f"Program {program}",
                'event': 'program_change'
            }
            
        except Exception as e:
            self.logger.error(f"Error parseando program_change: {e}")
            return {'error': str(e)}
    
    def _parse_pitch_bend(self, message, channel: int) -> Dict[str, Any]:
        """Parsea mensaje pitch_bend"""
        try:
            value = message.pitch
            
            return {
                'pitch_bend': value,
                'pitch_bend_normalized': (value + 8192) / 16384.0,  # Normalizar a 0-1
                'event': 'pitch_bend'
            }
            
        except Exception as e:
            self.logger.error(f"Error parseando pitch_bend: {e}")
            return {'error': str(e)}
    
    def _parse_aftertouch(self, message, channel: int) -> Dict[str, Any]:
        """Parsea mensaje aftertouch"""
        try:
            value = message.value
            
            return {
                'aftertouch': value,
                'aftertouch_normalized': value / 127.0,  # Normalizar a 0-1
                'event': 'aftertouch'
            }
            
        except Exception as e:
            self.logger.error(f"Error parseando aftertouch: {e}")
            return {'error': str(e)}
    
    def _select_midi_port(self, available_ports: List[str]) -> Optional[str]:
        """Selecciona el puerto MIDI apropiado"""
        try:
            # Si se especificó un puerto específico
            if self.midi_config.port_name:
                if self.midi_config.port_name in available_ports:
                    return self.midi_config.port_name
                else:
                    self.logger.warning(f"Puerto especificado '{self.midi_config.port_name}' no está disponible")
            
            # Si se especificó un número de puerto
            if self.midi_config.port_number is not None:
                if 0 <= self.midi_config.port_number < len(available_ports):
                    return available_ports[self.midi_config.port_number]
                else:
                    self.logger.warning(f"Número de puerto {self.midi_config.port_number} fuera de rango")
            
            # Seleccionar el primer puerto disponible
            if available_ports:
                return available_ports[0]
            
            return None
            
        except Exception as e:
            self.logger.error(f"Error seleccionando puerto MIDI: {e}")
            return None
    
    def _note_number_to_name(self, note: int) -> str:
        """Convierte número de nota MIDI a nombre musical"""
        try:
            note_names = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
            octave = (note // 12) - 1
            note_in_octave = note % 12
            
            return f"{note_names[note_in_octave]}{octave}"
            
        except Exception:
            return f"Note_{note}"
    
    def _note_to_frequency(self, note: int) -> float:
        """Convierte número de nota MIDI a frecuencia en Hz"""
        try:
            return 440.0 * (2 ** ((note - 69) / 12.0))
        except Exception:
            return 0.0
    
    def _on_midi_message(self, message):
        """Callback para mensajes MIDI recibidos"""
        try:
            # Crear datos unificados
            unified_data = self._parse_raw_data(message)
            
            if unified_data:
                # Enviar al callback del conector base
                if self.data_callback:
                    self.data_callback(unified_data)
                
                self.logger.debug(f"🎵 Mensaje MIDI procesado: {message.type} ch{message.channel + 1}")
            else:
                self.logger.debug(f"Mensaje MIDI filtrado: {message.type} ch{message.channel + 1}")
                
        except Exception as e:
            self.logger.error(f"Error procesando mensaje MIDI: {e}")
    
    def get_active_notes(self) -> Dict[int, Dict[str, Any]]:
        """Obtiene las notas MIDI actualmente activas"""
        return self.active_notes.copy()
    
    def get_connected_devices(self) -> Dict[str, Dict[str, Any]]:
        """Obtiene la lista de dispositivos MIDI conectados"""
        return self.connected_devices.copy()
    
    def get_status(self) -> Dict[str, Any]:
        """Obtiene el estado del conector MIDI"""
        status = super().get_status()
        status.update({
            'port_name': self.midi_port,
            'active_notes': len(self.active_notes),
            'channel_filter': self.midi_config.channel_filter.copy(),
            'message_types': self.midi_config.message_types.copy(),
            'note_range': self.midi_config.note_range,
            'velocity_threshold': self.midi_config.velocity_threshold
        })
        return status
