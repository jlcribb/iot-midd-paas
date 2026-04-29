"""
Repositorio para Registros de Datos con Validación de Tipos
==========================================================

Este módulo maneja la inserción de registros de datos con validación
automática de tipos según el canal y validación de rangos.
"""

from typing import Dict, Any, Optional, List, Union
from datetime import datetime
import json
import logging
from sqlalchemy import select, and_
from sqlalchemy.exc import SQLAlchemyError

from .base_repository import BaseRepository
from ...models.entities import RegistroDatos, Canal, DispositivoProyecto, Proyecto, UnidadProyecto
from ...models.enums import TipoDato, CalidadDato

# Configurar logging
logger = logging.getLogger(__name__)


class RegistroDatosRepository(BaseRepository[RegistroDatos]):
    """
    Repositorio para registros de datos con validación automática
    """
    
    def __init__(self, db_handler):
        super().__init__(db_handler, RegistroDatos)
    
    def insert_record(self, 
                     canal_id: str,
                     valor: Any,
                     ts: Optional[datetime] = None,
                     calidad: CalidadDato = CalidadDato.OK,
                     calidad_porcentaje: int = 100,
                     metadata: Optional[Dict[str, Any]] = None,
                     **kwargs) -> Optional[RegistroDatos]:
        """
        Insertar un registro de datos con validación automática
        
        Args:
            canal_id: ID del canal
            valor: Valor a insertar (se validará según el tipo del canal)
            ts: Timestamp (por defecto ahora)
            calidad: Calidad del dato
            calidad_porcentaje: Porcentaje de calidad (0-100)
            metadata: Metadatos adicionales
            **kwargs: Otros campos opcionales
            
        Returns:
            Registro creado o None si hay error de validación
        """
        try:
            # Obtener información del canal
            canal_info = self._get_canal_info(canal_id)
            if not canal_info:
                logger.error(f"Canal no encontrado: {canal_id}")
                return None
            
            # Validar y preparar el valor según el tipo del canal
            validated_data = self._validate_and_prepare_value(
                valor, canal_info, metadata, **kwargs
            )
            if not validated_data:
                return None
            
            # Crear el registro
            record_data = {
                'canal_id': canal_id,
                'ts': ts or datetime.utcnow(),
                'calidad': calidad,
                'calidad_porcentaje': max(0, min(100, calidad_porcentaje)),
                **validated_data,
                **kwargs
            }
            
            # Insertar usando el método base
            return self.create(record_data)
            
        except Exception as e:
            logger.error(f"Error al insertar registro en canal {canal_id}: {e}")
            return None
    
    def _get_canal_info(self, canal_id: str) -> Optional[Dict[str, Any]]:
        """
        Obtener información del canal incluyendo dispositivo y proyecto
        
        Args:
            canal_id: ID del canal
            
        Returns:
            Diccionario con información del canal
        """
        try:
            with self.db.get_session() as session:
                # Query compleja para obtener toda la información necesaria
                query = select(
                    Canal,
                    DispositivoProyecto,
                    Proyecto,
                    UnidadProyecto
                ).join(
                    DispositivoProyecto, 
                    Canal.dispositivo_id == DispositivoProyecto.dispositivo_id
                ).join(
                    Proyecto, 
                    DispositivoProyecto.proyecto_id == Proyecto.id
                ).outerjoin(
                    UnidadProyecto, 
                    DispositivoProyecto.unidad_id == UnidadProyecto.id
                ).where(
                    Canal.id == canal_id
                )
                
                result = session.execute(query).first()
                if not result:
                    return None
                
                canal, disp_proj, proyecto, unidad = result
                
                return {
                    'tipo_dato': canal.tipo,
                    'rango_min': canal.rango_min,
                    'rango_max': canal.rango_max,
                    'unidad_medida': canal.unidad_medida,
                    'proyecto_id': str(proyecto.id) if proyecto else None,
                    'unidad_id': str(unidad.id) if unidad else None,
                    'dispositivo_id': str(disp_proj.dispositivo_id) if disp_proj else None,
                    'canal_nombre': canal.nombre,
                    'proyecto_nombre': proyecto.nombre if proyecto else None,
                    'unidad_nombre': unidad.nombre if unidad else None
                }
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener información del canal {canal_id}: {e}")
            return None
    
    def _validate_and_prepare_value(self, 
                                  valor: Any, 
                                  canal_info: Dict[str, Any],
                                  metadata: Optional[Dict[str, Any]] = None,
                                  **kwargs) -> Optional[Dict[str, Any]]:
        """
        Validar y preparar el valor según el tipo del canal
        
        Args:
            valor: Valor a validar
            canal_info: Información del canal
            metadata: Metadatos adicionales
            **kwargs: Otros campos
            
        Returns:
            Diccionario con los campos validados o None si hay error
        """
        try:
            tipo_dato = canal_info['tipo_dato']
            rango_min = canal_info.get('rango_min')
            rango_max = canal_info.get('rango_max')
            
            # Preparar campos de valor según el tipo
            valor_fields = {}
            
            if tipo_dato == TipoDato.INT:
                try:
                    valor_int = int(valor)
                    # Validar rango si está definido
                    if rango_min is not None and valor_int < rango_min:
                        logger.warning(f"Valor {valor_int} está por debajo del rango mínimo {rango_min}")
                        return None
                    if rango_max is not None and valor_int > rango_max:
                        logger.warning(f"Valor {valor_int} está por encima del rango máximo {rango_max}")
                        return None
                    
                    valor_fields['valor_int'] = valor_int
                except (ValueError, TypeError):
                    logger.error(f"No se puede convertir {valor} a entero para canal tipo {tipo_dato}")
                    return None
                    
            elif tipo_dato == TipoDato.FLOAT:
                try:
                    valor_num = float(valor)
                    # Validar rango si está definido
                    if rango_min is not None and valor_num < rango_min:
                        logger.warning(f"Valor {valor_num} está por debajo del rango mínimo {rango_min}")
                        return None
                    if rango_max is not None and valor_num > rango_max:
                        logger.warning(f"Valor {valor_num} está por encima del rango máximo {rango_max}")
                        return None
                    
                    valor_fields['valor_num'] = valor_num
                except (ValueError, TypeError):
                    logger.error(f"No se puede convertir {valor} a float para canal tipo {tipo_dato}")
                    return None
                    
            elif tipo_dato == TipoDato.BOOL:
                if isinstance(valor, bool):
                    valor_fields['valor_bool'] = valor
                elif isinstance(valor, str):
                    if valor.lower() in ('true', '1', 'yes', 'on'):
                        valor_fields['valor_bool'] = True
                    elif valor.lower() in ('false', '0', 'no', 'off'):
                        valor_fields['valor_bool'] = False
                    else:
                        logger.error(f"No se puede convertir {valor} a boolean para canal tipo {tipo_dato}")
                        return None
                elif isinstance(valor, (int, float)):
                    valor_fields['valor_bool'] = bool(valor)
                else:
                    logger.error(f"Tipo de valor no válido para boolean: {type(valor)}")
                    return None
                    
            elif tipo_dato == TipoDato.STRING:
                if isinstance(valor, str):
                    valor_fields['valor_text'] = valor
                else:
                    valor_fields['valor_text'] = str(valor)
                    
            elif tipo_dato == TipoDato.JSON:
                if isinstance(valor, dict):
                    valor_fields['valor_json'] = valor
                elif isinstance(valor, str):
                    try:
                        valor_fields['valor_json'] = json.loads(valor)
                    except json.JSONDecodeError:
                        logger.error(f"String no válido como JSON: {valor}")
                        return None
                else:
                    logger.error(f"Tipo de valor no válido para JSON: {type(valor)}")
                    return None
                    
            elif tipo_dato == TipoDato.BINARY:
                # Para datos binarios, almacenar como texto por ahora
                valor_fields['valor_text'] = str(valor)
                
            elif tipo_dato == TipoDato.TIMESTAMP:
                if isinstance(valor, datetime):
                    valor_fields['valor_text'] = valor.isoformat()
                elif isinstance(valor, str):
                    valor_fields['valor_text'] = valor
                else:
                    logger.error(f"Tipo de valor no válido para timestamp: {type(valor)}")
                    return None
            else:
                logger.error(f"Tipo de dato no soportado: {tipo_dato}")
                return None
            
            # Preparar metadatos enriquecidos
            enriched_metadata = self._prepare_metadata(canal_info, metadata, **kwargs)
            
            return {
                **valor_fields,
                'metadatos': enriched_metadata
            }
            
        except Exception as e:
            logger.error(f"Error al validar y preparar valor: {e}")
            return None
    
    def _prepare_metadata(self, 
                          canal_info: Dict[str, Any],
                          metadata: Optional[Dict[str, Any]] = None,
                          **kwargs) -> Dict[str, Any]:
        """
        Preparar metadatos enriquecidos con información del contexto
        
        Args:
            canal_info: Información del canal
            metadata: Metadatos proporcionados por el usuario
            **kwargs: Otros campos que pueden ser metadatos
            
        Returns:
            Diccionario con metadatos enriquecidos
        """
        base_metadata = {
            'canal_nombre': canal_info.get('canal_nombre'),
            'tipo_dato': canal_info.get('tipo_dato'),
            'unidad_medida': canal_info.get('unidad_medida'),
            'proyecto_id': canal_info.get('proyecto_id'),
            'unidad_id': canal_info.get('unidad_id'),
            'dispositivo_id': canal_info.get('dispositivo_id'),
            'proyecto_nombre': canal_info.get('proyecto_nombre'),
            'unidad_nombre': canal_info.get('unidad_nombre'),
            'timestamp_insertion': datetime.utcnow().isoformat(),
            'validated': True
        }
        
        # Agregar metadatos del usuario
        if metadata:
            base_metadata.update(metadata)
        
        # Agregar campos adicionales que pueden ser metadatos
        metadata_fields = ['qos', 'ip', 'source', 'device_info', 'location']
        for field in metadata_fields:
            if field in kwargs:
                base_metadata[field] = kwargs[field]
        
        return base_metadata
    
    def get_records_by_canal(self, 
                           canal_id: str, 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None,
                           limit: Optional[int] = None) -> List[RegistroDatos]:
        """
        Obtener registros de un canal específico con filtros de tiempo
        
        Args:
            canal_id: ID del canal
            start_time: Tiempo de inicio para filtrar
            end_time: Tiempo de fin para filtrar
            limit: Límite de resultados
            
        Returns:
            Lista de registros
        """
        try:
            with self.db.get_session() as session:
                query = select(self.model_class).where(
                    self.model_class.canal_id == canal_id
                )
                
                if start_time:
                    query = query.where(self.model_class.ts >= start_time)
                if end_time:
                    query = query.where(self.model_class.ts <= end_time)
                
                query = query.order_by(self.model_class.ts.desc())
                
                if limit:
                    query = query.limit(limit)
                
                result = session.execute(query)
                records = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(records)} registros del canal {canal_id}")
                return records
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener registros del canal {canal_id}: {e}")
            return []
    
    def get_records_by_project(self, 
                             proyecto_id: str,
                             start_time: Optional[datetime] = None,
                             end_time: Optional[datetime] = None,
                             limit: Optional[int] = None) -> List[RegistroDatos]:
        """
        Obtener registros de un proyecto específico
        
        Args:
            proyecto_id: ID del proyecto
            start_time: Tiempo de inicio para filtrar
            end_time: Tiempo de fin para filtrar
            limit: Límite de resultados
            
        Returns:
            Lista de registros
        """
        try:
            with self.db.get_session() as session:
                # Query compleja para obtener registros por proyecto
                query = select(self.model_class).join(
                    Canal, self.model_class.canal_id == Canal.id
                ).join(
                    DispositivoProyecto, Canal.dispositivo_id == DispositivoProyecto.dispositivo_id
                ).where(
                    DispositivoProyecto.proyecto_id == proyecto_id
                )
                
                if start_time:
                    query = query.where(self.model_class.ts >= start_time)
                if end_time:
                    query = query.where(self.model_class.ts <= end_time)
                
                query = query.order_by(self.model_class.ts.desc())
                
                if limit:
                    query = query.limit(limit)
                
                result = session.execute(query)
                records = result.scalars().all()
                
                logger.debug(f"Obtenidos {len(records)} registros del proyecto {proyecto_id}")
                return records
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener registros del proyecto {proyecto_id}: {e}")
            return []
    
    def get_statistics_by_canal(self, canal_id: str) -> Dict[str, Any]:
        """
        Obtener estadísticas de un canal específico
        
        Args:
            canal_id: ID del canal
            
        Returns:
            Diccionario con estadísticas
        """
        try:
            with self.db.get_session() as session:
                # Contar total de registros
                total_query = select(self.model_class).where(
                    self.model_class.canal_id == canal_id
                )
                total_result = session.execute(total_query)
                total_records = len(total_result.scalars().all())
                
                # Obtener último registro
                last_query = select(self.model_class).where(
                    self.model_class.canal_id == canal_id
                ).order_by(self.model_class.ts.desc()).limit(1)
                last_result = session.execute(last_query)
                last_record = last_result.scalar_one_or_none()
                
                # Obtener primer registro
                first_query = select(self.model_class).where(
                    self.model_class.canal_id == canal_id
                ).order_by(self.model_class.ts.asc()).limit(1)
                first_result = session.execute(first_query)
                first_record = first_result.scalar_one_or_none()
                
                stats = {
                    'canal_id': canal_id,
                    'total_registros': total_records,
                    'primer_registro': first_record.ts if first_record else None,
                    'ultimo_registro': last_record.ts if last_record else None,
                    'rango_tiempo_dias': None
                }
                
                if first_record and last_record:
                    time_diff = last_record.ts - first_record.ts
                    stats['rango_tiempo_dias'] = time_diff.days
                
                return stats
                
        except SQLAlchemyError as e:
            logger.error(f"Error al obtener estadísticas del canal {canal_id}: {e}")
            return {}
