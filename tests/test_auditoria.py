"""
Pruebas Unitarias del Sistema de Auditoría
IoT Middleware
==========================================

Este módulo contiene pruebas unitarias para verificar el correcto
funcionamiento del sistema de auditoría.
"""

import unittest
import json
import tempfile
import os
from datetime import datetime, timezone, timedelta
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, Optional

# Importar módulos a probar
try:
    from iot_middleware.utils.auditoria import (
        AuditoriaService,
        ContextoAuditoria,
        AccionAuditoria,
        EntidadAuditable,
        auditar_cambios,
        contexto_auditoria,
        create_auditoria_service
    )
    from iot_middleware.models.entities import Auditoria
except ImportError:
    # Fallback para importación directa
    from src.iot_middleware.utils.auditoria import (
        AuditoriaService,
        ContextoAuditoria,
        AccionAuditoria,
        EntidadAuditable,
        auditar_cambios,
        contexto_auditoria,
        create_auditoria_service
    )
    from src.iot_middleware.models.entities import Auditoria


class TestContextoAuditoria(unittest.TestCase):
    """Pruebas para la clase ContextoAuditoria"""
    
    def test_creacion_basica(self):
        """Prueba la creación básica de un contexto de auditoría"""
        contexto = ContextoAuditoria(
            usuario_id="user_001",
            ip_origen="192.168.1.100"
        )
        
        self.assertEqual(contexto.usuario_id, "user_001")
        self.assertEqual(contexto.ip_origen, "192.168.1.100")
        self.assertIsInstance(contexto.timestamp, datetime)
    
    def test_creacion_completa(self):
        """Prueba la creación completa de un contexto de auditoría"""
        timestamp = datetime.now(timezone.utc)
        contexto = ContextoAuditoria(
            usuario_id="user_001",
            ip_origen="192.168.1.100",
            user_agent="TestAgent/1.0",
            sesion_id="session_123",
            request_id="req_456",
            endpoint="/api/test",
            metodo_http="POST",
            headers={"content-type": "application/json"},
            parametros={"id": "123"},
            timestamp=timestamp
        )
        
        self.assertEqual(contexto.usuario_id, "user_001")
        self.assertEqual(contexto.ip_origen, "192.168.1.100")
        self.assertEqual(contexto.user_agent, "TestAgent/1.0")
        self.assertEqual(contexto.sesion_id, "session_123")
        self.assertEqual(contexto.request_id, "req_456")
        self.assertEqual(contexto.endpoint, "/api/test")
        self.assertEqual(contexto.metodo_http, "POST")
        self.assertEqual(contexto.headers, {"content-type": "application/json"})
        self.assertEqual(contexto.parametros, {"id": "123"})
        self.assertEqual(contexto.timestamp, timestamp)
    
    def test_timestamp_por_defecto(self):
        """Prueba que el timestamp se genera por defecto"""
        contexto = ContextoAuditoria()
        
        self.assertIsInstance(contexto.timestamp, datetime)
        self.assertLess(
            abs((datetime.now(timezone.utc) - contexto.timestamp).total_seconds()),
            1.0  # Debe ser menor a 1 segundo
        )


class TestAccionAuditoria(unittest.TestCase):
    """Pruebas para el enum AccionAuditoria"""
    
    def test_valores_enum(self):
        """Prueba que todos los valores del enum están definidos"""
        acciones_esperadas = {
            'CREAR', 'ACTUALIZAR', 'ELIMINAR', 'ACTIVAR', 'DESACTIVAR',
            'CONFIGURAR', 'VALIDAR', 'PROCESAR', 'RECONOCER', 'RESOLVER'
        }
        
        acciones_actuales = {accion.value for accion in AccionAuditoria}
        self.assertEqual(acciones_actuales, acciones_esperadas)
    
    def test_valor_crear(self):
        """Prueba el valor CREAR"""
        self.assertEqual(AccionAuditoria.CREAR.value, "CREAR")
    
    def test_valor_actualizar(self):
        """Prueba el valor ACTUALIZAR"""
        self.assertEqual(AccionAuditoria.ACTUALIZAR.value, "ACTUALIZAR")


class TestEntidadAuditable(unittest.TestCase):
    """Pruebas para el enum EntidadAuditable"""
    
    def test_valores_enum(self):
        """Prueba que todos los valores del enum están definidos"""
        entidades_esperadas = {
            'config_middleware', 'canal', 'evento_alarma', 'dispositivo',
            'proyecto', 'usuario', 'cliente'
        }
        
        entidades_actuales = {entidad.value for entidad in EntidadAuditable}
        self.assertEqual(entidades_actuales, entidades_esperadas)
    
    def test_valor_config_middleware(self):
        """Prueba el valor CONFIG_MIDDLEWARE"""
        self.assertEqual(EntidadAuditable.CONFIG_MIDDLEWARE.value, "config_middleware")
    
    def test_valor_canal(self):
        """Prueba el valor CANAL"""
        self.assertEqual(EntidadAuditable.CANAL.value, "canal")


class TestAuditoriaService(unittest.TestCase):
    """Pruebas para la clase AuditoriaService"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        # Mock del manejador de base de datos
        self.mock_db_handler = MagicMock()
        self.mock_session = Mock()
        self.mock_db_handler.get_session.return_value.__enter__.return_value = self.mock_session
        self.mock_db_handler.get_session.return_value.__exit__.return_value = None
        
        # Crear servicio de auditoría
        self.auditoria_service = AuditoriaService(self.mock_db_handler)
    
    def test_creacion_servicio(self):
        """Prueba la creación del servicio de auditoría"""
        self.assertIsInstance(self.auditoria_service, AuditoriaService)
        self.assertEqual(self.auditoria_service.auditoria_habilitada, True)
        self.assertEqual(self.auditoria_service.auditoria_sensible, True)
        self.assertEqual(self.auditoria_service.max_tamano_cambios, 10000)
    
    def test_set_get_contexto(self):
        """Prueba el establecimiento y obtención del contexto"""
        contexto = ContextoAuditoria(
            usuario_id="user_001",
            ip_origen="192.168.1.100"
        )
        
        self.auditoria_service.set_contexto(contexto)
        contexto_obtenido = self.auditoria_service.get_contexto()
        
        self.assertEqual(contexto_obtenido.usuario_id, "user_001")
        self.assertEqual(contexto_obtenido.ip_origen, "192.168.1.100")
    
    def test_clear_contexto(self):
        """Prueba la limpieza del contexto"""
        contexto = ContextoAuditoria(usuario_id="user_001")
        self.auditoria_service.set_contexto(contexto)
        
        self.auditoria_service.clear_contexto()
        contexto_obtenido = self.auditoria_service.get_contexto()
        
        self.assertIsNone(contexto_obtenido)
    
    def test_registrar_cambio_sin_contexto(self):
        """Prueba el registro de cambios sin contexto"""
        cambios = {'antes': {}, 'despues': {'valor': 'test'}}
        
        resultado = self.auditoria_service.registrar_cambio(
            entidad="test_entity",
            entidad_id="123",
            accion="TEST",
            cambios=cambios
        )
        
        self.assertFalse(resultado)
    
    def test_registrar_cambio_con_contexto(self):
        """Prueba el registro de cambios con contexto"""
        contexto = ContextoAuditoria(
            usuario_id="user_001",
            ip_origen="192.168.1.100"
        )
        self.auditoria_service.set_contexto(contexto)
        
        cambios = {'antes': {}, 'despues': {'valor': 'test'}}
        
        resultado = self.auditoria_service.registrar_cambio(
            entidad="test_entity",
            entidad_id="123",
            accion="TEST",
            cambios=cambios
        )
        
        self.assertTrue(resultado)
        
        # Verificar que se llamó a la inserción
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()
    
    def test_auditoria_deshabilitada(self):
        """Prueba que la auditoría no se ejecuta cuando está deshabilitada"""
        self.auditoria_service.auditoria_habilitada = False
        
        contexto = ContextoAuditoria(usuario_id="user_001")
        self.auditoria_service.set_contexto(contexto)
        
        cambios = {'antes': {}, 'despues': {'valor': 'test'}}
        
        resultado = self.auditoria_service.registrar_cambio(
            entidad="test_entity",
            entidad_id="123",
            accion="TEST",
            cambios=cambios
        )
        
        self.assertTrue(resultado)
        # No se debe haber llamado a la inserción
        self.mock_session.add.assert_not_called()
    
    def test_sanitizacion_datos_sensibles(self):
        """Prueba la sanitización de datos sensibles"""
        contexto = ContextoAuditoria(usuario_id="user_001")
        self.auditoria_service.set_contexto(contexto)
        
        cambios = {
            'antes': {},
            'despues': {
                'username': 'admin',
                'password': 'secret123',
                'api_key': 'sk-123456',
                'datos_normales': 'valor'
            }
        }
        
        resultado = self.auditoria_service.registrar_cambio(
            entidad="test_entity",
            entidad_id="123",
            accion="TEST",
            cambios=cambios
        )
        
        self.assertTrue(resultado)
        
        # Verificar que se llamó a add con datos sanitizados
        call_args = self.mock_session.add.call_args[0][0]
        cambios_guardados = call_args.cambios
        
        self.assertEqual(cambios_guardados['despues']['password'], '***SENSIBLE***')
        self.assertEqual(cambios_guardados['despues']['api_key'], '***SENSIBLE***')
        self.assertEqual(cambios_guardados['despues']['datos_normales'], 'valor')
    
    def test_truncado_cambios_grandes(self):
        """Prueba el truncado de cambios muy grandes"""
        contexto = ContextoAuditoria(usuario_id="user_001")
        self.auditoria_service.set_contexto(contexto)
        
        # Crear cambios muy grandes
        cambios_grandes = {
            'antes': {},
            'despues': {'datos': 'x' * 15000}  # Más de 10KB
        }
        
        resultado = self.auditoria_service.registrar_cambio(
            entidad="test_entity",
            entidad_id="123",
            accion="TEST",
            cambios=cambios_grandes
        )
        
        self.assertTrue(resultado)
        
        # Verificar que se truncaron los cambios
        call_args = self.mock_session.add.call_args[0][0]
        cambios_guardados = call_args.cambios
        
        self.assertTrue(cambios_guardados['antes']['_truncado'])
        self.assertTrue(cambios_guardados['despues']['_truncado'])
        self.assertIn('mensaje', cambios_guardados)
    
    def test_auditar_config_middleware(self):
        """Prueba la auditoría específica de config_middleware"""
        contexto = ContextoAuditoria(usuario_id="user_001")
        self.auditoria_service.set_contexto(contexto)
        
        antes = {'valor': 'antiguo'}
        despues = {'valor': 'nuevo'}
        
        resultado = self.auditoria_service.auditar_config_middleware(
            config_id="config_001",
            accion=AccionAuditoria.CREAR,
            antes=antes,
            despues=despues
        )
        
        self.assertTrue(resultado)
        
        # Verificar que se llamó con los parámetros correctos
        call_args = self.mock_session.add.call_args[0][0]
        self.assertEqual(call_args.entidad, 'config_middleware')
        self.assertEqual(call_args.entidad_id, 'config_001')
        self.assertEqual(call_args.accion, 'CREAR')
    
    def test_auditar_canal(self):
        """Prueba la auditoría específica de canales"""
        contexto = ContextoAuditoria(usuario_id="user_001")
        self.auditoria_service.set_contexto(contexto)
        
        resultado = self.auditoria_service.auditar_canal(
            canal_id="canal_001",
            accion=AccionAuditoria.CONFIGURAR,
            antes={'umbral': 80},
            despues={'umbral': 85}
        )
        
        self.assertTrue(resultado)
        
        call_args = self.mock_session.add.call_args[0][0]
        self.assertEqual(call_args.entidad, 'canal')
        self.assertEqual(call_args.entidad_id, 'canal_001')
        self.assertEqual(call_args.accion, 'CONFIGURAR')
    
    def test_auditar_evento_alarma(self):
        """Prueba la auditoría específica de eventos de alarma"""
        contexto = ContextoAuditoria(usuario_id="user_001")
        self.auditoria_service.set_contexto(contexto)
        
        resultado = self.auditoria_service.auditar_evento_alarma(
            evento_id="alarma_001",
            accion=AccionAuditoria.RECONOCER,
            antes={'estado': 'activa'},
            despues={'estado': 'reconocida'}
        )
        
        self.assertTrue(resultado)
        
        call_args = self.mock_session.add.call_args[0][0]
        self.assertEqual(call_args.entidad, 'evento_alarma')
        self.assertEqual(call_args.entidad_id, 'alarma_001')
        self.assertEqual(call_args.accion, 'RECONOCER')


class TestDecoradoresAuditoria(unittest.TestCase):
    """Pruebas para los decoradores de auditoría"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.mock_db_handler = MagicMock()
        self.mock_session = Mock()
        self.mock_db_handler.get_session.return_value.__enter__.return_value = self.mock_session
        self.mock_db_handler.get_session.return_value.__exit__.return_value = None
        
        self.auditoria_service = AuditoriaService(self.mock_db_handler)
    
    def test_decorador_auditar_cambios(self):
        """Prueba el decorador auditar_cambios"""
        
        class ServicioTest:
            def __init__(self, auditoria_service):
                self.auditoria_service = auditoria_service
            
            @auditar_cambios(EntidadAuditable.CONFIG_MIDDLEWARE, AccionAuditoria.CREAR)
            def crear_config(self, id: str, data: dict):
                return True
        
        servicio = ServicioTest(self.auditoria_service)
        
        # Establecer contexto
        contexto = ContextoAuditoria(usuario_id="user_001")
        self.auditoria_service.set_contexto(contexto)
        
        # Ejecutar método decorado
        resultado = servicio.crear_config("config_001", {"valor": "test"})
        
        self.assertTrue(resultado)
        
        # Verificar que se registró la auditoría
        self.mock_session.add.assert_called_once()
        self.mock_session.commit.assert_called_once()


class TestContextManagerAuditoria(unittest.TestCase):
    """Pruebas para el context manager de auditoría"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.mock_db_handler = MagicMock()
        self.mock_session = Mock()
        self.mock_db_handler.get_session.return_value.__enter__.return_value = self.mock_session
        self.mock_db_handler.get_session.return_value.__exit__.return_value = None
        
        self.auditoria_service = AuditoriaService(self.mock_db_handler)
    
    def test_context_manager_basico(self):
        """Prueba el uso básico del context manager"""
        with contexto_auditoria(
            self.auditoria_service,
            usuario_id="user_001",
            ip_origen="192.168.1.100"
        ) as audit_service:
            
            # Verificar que el contexto se estableció
            contexto = audit_service.get_contexto()
            self.assertIsNotNone(contexto)
            self.assertEqual(contexto.usuario_id, "user_001")
            self.assertEqual(contexto.ip_origen, "192.168.1.100")
            
            # Registrar un cambio
            resultado = audit_service.auditar_config_middleware(
                config_id="config_001",
                accion=AccionAuditoria.CREAR,
                antes={},
                despues={'valor': 'test'}
            )
            
            self.assertTrue(resultado)
        
        # Verificar que el contexto se limpió
        contexto = self.auditoria_service.get_contexto()
        self.assertIsNone(contexto)


class TestFuncionesConveniencia(unittest.TestCase):
    """Pruebas para las funciones de conveniencia"""
    
    def test_create_auditoria_service(self):
        """Prueba la función create_auditoria_service"""
        mock_db_handler = Mock()
        
        auditoria_service = create_auditoria_service(mock_db_handler)
        
        self.assertIsInstance(auditoria_service, AuditoriaService)
        self.assertEqual(auditoria_service.db_handler, mock_db_handler)


class TestGeneracionReportes(unittest.TestCase):
    """Pruebas para la generación de reportes"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.mock_db_handler = MagicMock()
        self.mock_session = Mock()
        self.mock_db_handler.get_session.return_value.__enter__.return_value = self.mock_session
        self.mock_db_handler.get_session.return_value.__exit__.return_value = None
        
        self.auditoria_service = AuditoriaService(self.mock_db_handler)
    
    def test_generar_reporte_json(self):
        """Prueba la generación de reportes en formato JSON"""
        # Mock de registros de auditoría
        mock_registros = [
            {
                'id': 1,
                'usuario_id': 'user_001',
                'entidad': 'config_middleware',
                'entidad_id': 'config_001',
                'accion': 'CREAR',
                'cambios': {},
                'ip_origen': None,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        with patch.object(self.auditoria_service, 'obtener_auditoria', return_value=mock_registros):
            reporte = self.auditoria_service.generar_reporte_auditoria(
                fecha_desde=datetime.now(timezone.utc) - timedelta(days=1),
                fecha_hasta=datetime.now(timezone.utc),
                formato='json'
            )
            
            self.assertIsInstance(reporte, dict)
            self.assertIn('estadisticas', reporte)
            self.assertIn('registros', reporte)
            self.assertEqual(reporte['estadisticas']['total_registros'], 1)
    
    def test_generar_reporte_csv(self):
        """Prueba la generación de reportes en formato CSV"""
        mock_registros = [
            {
                'id': 1,
                'usuario_id': 'user_001',
                'entidad': 'config_middleware',
                'entidad_id': 'config_001',
                'accion': 'CREAR',
                'cambios': {},
                'ip_origen': None,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        with patch.object(self.auditoria_service, 'obtener_auditoria', return_value=mock_registros):
            reporte = self.auditoria_service.generar_reporte_auditoria(
                fecha_desde=datetime.now(timezone.utc) - timedelta(days=1),
                fecha_hasta=datetime.now(timezone.utc),
                formato='csv'
            )
            
            self.assertIsInstance(reporte, str)
            self.assertTrue(reporte.startswith('ID,Usuario'))
            self.assertIn('config_middleware', reporte)
    
    def test_generar_reporte_html(self):
        """Prueba la generación de reportes en formato HTML"""
        mock_registros = [
            {
                'id': 1,
                'usuario_id': 'user_001',
                'entidad': 'config_middleware',
                'entidad_id': 'config_001',
                'accion': 'CREAR',
                'cambios': {},
                'ip_origen': None,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
        ]
        
        with patch.object(self.auditoria_service, 'obtener_auditoria', return_value=mock_registros):
            reporte = self.auditoria_service.generar_reporte_auditoria(
                fecha_desde=datetime.now(timezone.utc) - timedelta(days=1),
                fecha_hasta=datetime.now(timezone.utc),
                formato='html'
            )
            
            self.assertIsInstance(reporte, str)
            self.assertIn('<html>', reporte)
            self.assertIn('Reporte de Auditoría', reporte)
    
    def test_formato_no_soportado(self):
        """Prueba el manejo de formatos no soportados"""
        with self.assertRaises(ValueError):
            self.auditoria_service.generar_reporte_auditoria(
                fecha_desde=datetime.now(timezone.utc) - timedelta(days=1),
                fecha_hasta=datetime.now(timezone.utc),
                formato='xml'  # Formato no soportado
            )


class TestConsultasAuditoria(unittest.TestCase):
    """Pruebas para las consultas de auditoría"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.mock_db_handler = MagicMock()
        self.mock_session = Mock()
        self.mock_db_handler.get_session.return_value.__enter__.return_value = self.mock_session
        self.mock_db_handler.get_session.return_value.__exit__.return_value = None
        
        self.auditoria_service = AuditoriaService(self.mock_db_handler)
    
    def test_obtener_auditoria_sin_filtros(self):
        """Prueba la obtención de auditoría sin filtros"""
        # Mock de resultados
        mock_resultados = [
            Mock(
                id=1,
                usuario_id='user_001',
                entidad='config_middleware',
                entidad_id='config_001',
                accion='CREAR',
                cambios={},
                ip_origen='192.168.1.100',
                user_agent='TestAgent',
                contexto={},
                ts=datetime.now(timezone.utc)
            )
        ]
        
        # Mock de la consulta
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = mock_resultados
        
        self.mock_session.query.return_value = mock_query
        
        # Ejecutar consulta
        resultados = self.auditoria_service.obtener_auditoria(limite=10)
        
        # Verificar resultados
        self.assertEqual(len(resultados), 1)
        self.assertEqual(resultados[0]['entidad'], 'config_middleware')
        self.assertEqual(resultados[0]['accion'], 'CREAR')
    
    def test_obtener_auditoria_con_filtros(self):
        """Prueba la obtención de auditoría con filtros"""
        mock_query = Mock()
        mock_query.filter.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        
        self.mock_session.query.return_value = mock_query
        
        # Ejecutar consulta con filtros
        resultados = self.auditoria_service.obtener_auditoria(
            entidad='config_middleware',
            accion='CREAR',
            usuario_id='user_001',
            limite=5
        )
        
        # Verificar que se aplicaron los filtros
        self.assertEqual(len(resultados), 0)
        mock_query.filter.assert_called()


if __name__ == '__main__':
    # Configurar logging para las pruebas
    logging.basicConfig(level=logging.WARNING)
    
    # Ejecutar pruebas
    unittest.main(verbosity=2)
