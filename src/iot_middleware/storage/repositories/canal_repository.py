"""
Repositorio para Canales
========================

Este módulo maneja las operaciones CRUD específicas para canales,
incluyendo validación de tipos de datos y rangos.
"""

from typing import Dict, Any, Optional, List
from sqlalchemy import select, and_, or_, func
from sqlalchemy.exc import SQLAlchemyError
import logging

from .base_repository import BaseRepository
from ...models.entities import Canal, Dispositivo, DispositivoProyecto, Proyecto
from ...models.enums import TipoDato

# Configurar logging
logger = logging.getLogger(__name__)


class CanalRepository(BaseRepository[Canal]):
    """
    Repositorio para canales con métodos especializados
    """
    
    def __init__(self, db_handler):
        super().__init__(db_handler, Canal)
    
    def get_by_dispositivo(self, dispositivo_id: str) -> List[Canal]:
        """
        Obtener canales por dispositivo
        
        Args:
            dispositivo_id: ID del dispositivo
            
        Returns:
            Lista de canales del dispositivo
        """
        return self.find_by_criteria({'dispositivo_id': dispositivo_id})
    
    def get_by_tipo_dato(self, tipo_dato: TipoDato) -> List[Canal]:
        """
        Obtener canales por tipo de dato
        
        Args:
            tipo_dato: Tipo de dato del canal
            
        Returns:
            Lista de canales del tipo especificado
        """
        return self.find_by_criteria({'tipo': tipo_dato})
    
    def get_active_channels(self) -> List[Canal]:
        """
        Obtener solo canales activos
        
        Returns:
            Lista de canales activos
        """
        return self.find_by_criteria({'activo': True})
    
    def get_channels_by_project(self, proyecto_id: str) -> List[Canal]:
        """
        Obtener canales de un proyecto específico
        
        Args:
            proyecto_id: ID del proyecto
            
        Returns:
            Lista de canales del proyecto
        """
        try:
            with self.db.get_session() as session:
                query = select(Canal).join(
                    DispositivoProyecto, Canal.dispositivo_id == DispositivoProyecto.dispositivo_id
                ).where(
                    DispositivoProyecto.proyecto_id == proyecto_id
                )
                
                result = session.execute(query)
                channels = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(channels)} canales del proyecto {proyecto_id}")
                return channels
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener canales del proyecto {proyecto_id}: {e}")
            return []
    
    def get_channels_by_unit(self, unidad_id: str) -> List[Canal]:
        """
        Obtener canales de una unidad específica
        
        Args:
            unidad_id: ID de la unidad
            
        Returns:
            Lista de canales de la unidad
        """
        try:
            with self.db.get_session() as session:
                query = select(Canal).join(
                    DispositivoProyecto, Canal.dispositivo_id == DispositivoProyecto.dispositivo_id
                ).where(
                    DispositivoProyecto.unidad_id == unidad_id
                )
                
                result = session.execute(query)
                channels = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(channels)} canales de la unidad {unidad_id}")
                return channels
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener canales de la unidad {unidad_id}: {e}")
            return []
    
    def get_channels_with_range_validation(self) -> List[Canal]:
        """
        Obtener canales que tienen validación de rango configurada
        
        Returns:
            Lista de canales con rango_min y rango_max definidos
        """
        try:
            with self.db.get_session() as session:
                query = select(Canal).where(
                    and_(
                        Canal.rango_min.isnot(None),
                        Canal.rango_max.isnot(None)
                    )
                )
                
                result = session.execute(query)
                channels = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(channels)} canales con validación de rango")
                return channels
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener canales con validación de rango: {e}")
            return []
    
    def get_channel_info_for_validation(self, canal_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información completa del canal para validación
        
        Args:
            canal_id: ID del canal
            
        Returns:
            Diccionario con información del canal para validación
        """
        try:
            with self.db.get_session() as session:
                query = select(
                    Canal,
                    Dispositivo,
                    DispositivoProyecto,
                    Proyecto
                ).join(
                    Dispositivo, Canal.dispositivo_id == Dispositivo.id
                ).join(
                    DispositivoProyecto, Canal.dispositivo_id == DispositivoProyecto.dispositivo_id
                ).join(
                    Proyecto, DispositivoProyecto.proyecto_id == Proyecto.id
                ).where(
                    Canal.id == canal_id
                )
                
                result = session.execute(query).first()
                if not result:
                    return None
                
                canal, dispositivo, disp_proj, proyecto = result
                
                return {
                    'id': str(canal.id),
                    'nombre': canal.nombre,
                    'tipo': canal.tipo,
                    'unidad_medida': canal.unidad_medida,
                    'rango_min': canal.rango_min,
                    'rango_max': canal.rango_max,
                    'activo': canal.activo,
                    'dispositivo': {
                        'id': str(dispositivo.id),
                        'tipo': dispositivo.tipo,
                        'fabricante': dispositivo.fabricante,
                        'modelo': dispositivo.modelo,
                        'identificador_unico': dispositivo.identificador_unico
                    },
                    'proyecto': {
                        'id': str(proyecto.id),
                        'nombre': proyecto.nombre,
                        'estado': proyecto.estado
                    },
                    'configuracion': canal.configuracion
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener información del canal {canal_id}: {e}")
            return None
    
    def validate_channel_value(self, canal_id: str, valor: Any) -> Dict[str, Any]:
        """
        Validar un valor para un canal específico
        
        Args:
            canal_id: ID del canal
            valor: Valor a validar
            
        Returns:
            Diccionario con resultado de la validación
        """
        try:
            canal_info = self.get_channel_info_for_validation(canal_id)
            if not canal_info:
                return {
                    'valid': False,
                    'error': 'Canal no encontrado',
                    'canal_id': canal_id
                }
            
            # Validar tipo de dato
            tipo_dato = canal_info['tipo']
            validation_result = self._validate_value_type(valor, tipo_dato)
            
            if not validation_result['valid']:
                return validation_result
            
            # Validar rango si está configurado
            if canal_info.get('rango_min') is not None or canal_info.get('rango_max') is not None:
                range_validation = self._validate_value_range(
                    validation_result['converted_value'],
                    canal_info.get('rango_min'),
                    canal_info.get('rango_max')
                )
                
                if not range_validation['valid']:
                    return range_validation
            
            return {
                'valid': True,
                'canal_id': canal_id,
                'tipo_dato': tipo_dato,
                'valor_original': valor,
                'valor_validado': validation_result['converted_value'],
                'unidad_medida': canal_info.get('unidad_medida'),
                'rango_min': canal_info.get('rango_min'),
                'rango_max': canal_info.get('rango_max')
            }
            
        except Exception as e:
            logger.error(f"Error al validar valor para canal {canal_id}: {e}")
            return {
                'valid': False,
                'error': f'Error de validación: {str(e)}',
                'canal_id': canal_id
            }
    
    def _validate_value_type(self, valor: Any, tipo_dato: TipoDato) -> Dict[str, Any]:
        """
        Validar el tipo de dato de un valor
        
        Args:
            valor: Valor a validar
            tipo_dato: Tipo de dato esperado
            
        Returns:
            Diccionario con resultado de la validación
        """
        try:
            if tipo_dato == TipoDato.INT:
                try:
                    converted_value = int(valor)
                    return {
                        'valid': True,
                        'converted_value': converted_value,
                        'tipo_original': type(valor).__name__,
                        'tipo_convertido': 'int'
                    }
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error': f'No se puede convertir {valor} a entero',
                        'tipo_esperado': 'int',
                        'tipo_recibido': type(valor).__name__
                    }
                    
            elif tipo_dato == TipoDato.FLOAT:
                try:
                    converted_value = float(valor)
                    return {
                        'valid': True,
                        'converted_value': converted_value,
                        'tipo_original': type(valor).__name__,
                        'tipo_convertido': 'float'
                    }
                except (ValueError, TypeError):
                    return {
                        'valid': False,
                        'error': f'No se puede convertir {valor} a float',
                        'tipo_esperado': 'float',
                        'tipo_recibido': type(valor).__name__
                    }
                    
            elif tipo_dato == TipoDato.BOOL:
                if isinstance(valor, bool):
                    return {
                        'valid': True,
                        'converted_value': valor,
                        'tipo_original': 'bool',
                        'tipo_convertido': 'bool'
                    }
                elif isinstance(valor, str):
                    if valor.lower() in ('true', '1', 'yes', 'on'):
                        return {
                            'valid': True,
                            'converted_value': True,
                            'tipo_original': 'str',
                            'tipo_convertido': 'bool'
                        }
                    elif valor.lower() in ('false', '0', 'no', 'off'):
                        return {
                            'valid': True,
                            'converted_value': False,
                            'tipo_original': 'str',
                            'tipo_convertido': 'bool'
                        }
                    else:
                        return {
                            'valid': False,
                            'error': f'String no válido para boolean: {valor}',
                            'tipo_esperado': 'bool',
                            'tipo_recibido': 'str'
                        }
                elif isinstance(valor, (int, float)):
                    return {
                        'valid': True,
                        'converted_value': bool(valor),
                        'tipo_original': type(valor).__name__,
                        'tipo_convertido': 'bool'
                    }
                else:
                    return {
                        'valid': False,
                        'error': f'Tipo no válido para boolean: {type(valor).__name__}',
                        'tipo_esperado': 'bool',
                        'tipo_recibido': type(valor).__name__
                    }
                    
            elif tipo_dato == TipoDato.STRING:
                converted_value = str(valor)
                return {
                    'valid': True,
                    'converted_value': converted_value,
                    'tipo_original': type(valor).__name__,
                    'tipo_convertido': 'str'
                }
                
            elif tipo_dato == TipoDato.JSON:
                if isinstance(valor, dict):
                    return {
                        'valid': True,
                        'converted_value': valor,
                        'tipo_original': 'dict',
                        'tipo_convertido': 'dict'
                    }
                elif isinstance(valor, str):
                    try:
                        import json
                        converted_value = json.loads(valor)
                        return {
                            'valid': True,
                            'converted_value': converted_value,
                            'tipo_original': 'str',
                            'tipo_convertido': 'dict'
                        }
                    except json.JSONDecodeError:
                        return {
                            'valid': False,
                            'error': f'String no válido como JSON: {valor}',
                            'tipo_esperado': 'dict',
                            'tipo_recibido': 'str'
                        }
                else:
                    return {
                        'valid': False,
                        'error': f'Tipo no válido para JSON: {type(valor).__name__}',
                        'tipo_esperado': 'dict',
                        'tipo_recibido': type(valor).__name__
                    }
                    
            else:
                return {
                    'valid': False,
                    'error': f'Tipo de dato no soportado: {tipo_dato}',
                    'tipo_esperado': str(tipo_dato),
                    'tipo_recibido': type(valor).__name__
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error en validación de tipo: {str(e)}',
                'tipo_esperado': str(tipo_dato),
                'tipo_recibido': type(valor).__name__
            }
    
    def _validate_value_range(self, valor: Any, rango_min: Optional[float], rango_max: Optional[float]) -> Dict[str, Any]:
        """
        Validar que un valor esté dentro del rango especificado
        
        Args:
            valor: Valor a validar
            rango_min: Valor mínimo del rango
            rango_max: Valor máximo del rango
            
        Returns:
            Diccionario con resultado de la validación
        """
        try:
            if rango_min is not None and valor < rango_min:
                return {
                    'valid': False,
                    'error': f'Valor {valor} está por debajo del rango mínimo {rango_min}',
                    'valor': valor,
                    'rango_min': rango_min,
                    'rango_max': rango_max
                }
            
            if rango_max is not None and valor > rango_max:
                return {
                    'valid': False,
                    'error': f'Valor {valor} está por encima del rango máximo {rango_max}',
                    'valor': valor,
                    'rango_min': rango_min,
                    'rango_max': rango_max
                }
            
            return {
                'valid': True,
                'valor': valor,
                'rango_min': rango_min,
                'rango_max': rango_max
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Error en validación de rango: {str(e)}',
                'valor': valor,
                'rango_min': rango_min,
                'rango_max': rango_max
            }
    
    def get_channels_summary(self) -> Dict[str, Any]:
        """
        Obtener resumen general de todos los canales
        
        Returns:
            Diccionario con estadísticas de canales
        """
        try:
            with self.db.get_session() as session:
                # Contar total de canales
                total_channels = session.query(Canal).count()
                
                # Contar por tipo de dato
                channels_by_type = session.query(
                    Canal.tipo, func.count(Canal.id)
                ).group_by(Canal.tipo).all()
                
                # Contar canales activos
                active_channels = session.query(Canal).filter(
                    Canal.activo == True
                ).count()
                
                # Contar canales con validación de rango
                channels_with_range = session.query(Canal).filter(
                    and_(
                        Canal.rango_min.isnot(None),
                        Canal.rango_max.isnot(None)
                    )
                ).count()
                
                summary = {
                    'total_canales': total_channels,
                    'canales_activos': active_channels,
                    'canales_inactivos': total_channels - active_channels,
                    'por_tipo': dict(channels_by_type),
                    'con_validacion_rango': channels_with_range
                }
                
                return summary
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener resumen de canales: {e}")
            return {}
