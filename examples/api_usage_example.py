#!/usr/bin/env python3
"""
Ejemplo de Uso de la API REST - IoT Middleware
===============================================

Este script demuestra cómo usar la API REST para consultar datos de sensores
con diferentes filtros y parámetros.
"""

import sys
import json
import requests
import time
from pathlib import Path
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

# Agregar el directorio src al path para importar el módulo
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

try:
    from iot_middleware.api.api import initialize_api
    print("✅ Módulos importados exitosamente")
except ImportError as e:
    print(f"❌ Error al importar módulos: {e}")
    sys.exit(1)


class APIClient:
    """Cliente para interactuar con la API REST"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'IoT-Middleware-API-Client/1.0',
            'Accept': 'application/json'
        })
    
    def health_check(self) -> Dict[str, Any]:
        """Verifica el estado de salud de la API"""
        try:
            response = self.session.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error en health check: {e}")
            return {"error": str(e)}
    
    def get_sensor_data(self, 
                        topic: Optional[str] = None,
                        fecha_desde: Optional[str] = None,
                        fecha_hasta: Optional[str] = None,
                        limit: int = 100,
                        offset: int = 0,
                        calidad: Optional[str] = None,
                        procesado: Optional[bool] = None,
                        validado: Optional[bool] = None) -> Dict[str, Any]:
        """
        Obtiene datos de sensores con filtros
        
        Args:
            topic: Filtro de tópico
            fecha_desde: Fecha desde (ISO 8601)
            fecha_hasta: Fecha hasta (ISO 8601)
            limit: Número máximo de registros
            offset: Número de registros a omitir
            calidad: Filtro por calidad
            procesado: Filtro por estado de procesamiento
            validado: Filtro por estado de validación
        
        Returns:
            Respuesta de la API
        """
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            if topic:
                params['topic'] = topic
            if fecha_desde:
                params['fecha_desde'] = fecha_desde
            if fecha_hasta:
                params['fecha_hasta'] = fecha_hasta
            if calidad:
                params['calidad'] = calidad
            if procesado is not None:
                params['procesado'] = procesado
            if validado is not None:
                params['validado'] = validado
            
            response = self.session.get(f"{self.base_url}/data", params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo datos: {e}")
            return {"error": str(e)}
    
    def get_sensor_data_by_canal(self, 
                                 canal_id: str,
                                 fecha_desde: Optional[str] = None,
                                 fecha_hasta: Optional[str] = None,
                                 limit: int = 100,
                                 offset: int = 0) -> Dict[str, Any]:
        """
        Obtiene datos de un canal específico
        
        Args:
            canal_id: ID del canal
            fecha_desde: Fecha desde
            fecha_hasta: Fecha hasta
            limit: Número máximo de registros
            offset: Número de registros a omitir
        
        Returns:
            Respuesta de la API
        """
        try:
            params = {
                'limit': limit,
                'offset': offset
            }
            
            if fecha_desde:
                params['fecha_desde'] = fecha_desde
            if fecha_hasta:
                params['fecha_hasta'] = fecha_hasta
            
            response = self.session.get(f"{self.base_url}/data/{canal_id}", params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo datos del canal {canal_id}: {e}")
            return {"error": str(e)}
    
    def get_available_topics(self) -> Dict[str, Any]:
        """Obtiene la lista de tópicos disponibles"""
        try:
            response = self.session.get(f"{self.base_url}/topics")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo tópicos: {e}")
            return {"error": str(e)}
    
    def get_stats(self, 
                  topic: Optional[str] = None,
                  fecha_desde: Optional[str] = None,
                  fecha_hasta: Optional[str] = None) -> Dict[str, Any]:
        """
        Obtiene estadísticas de los datos
        
        Args:
            topic: Filtro de tópico
            fecha_desde: Fecha desde
            fecha_hasta: Fecha hasta
        
        Returns:
            Estadísticas de los datos
        """
        try:
            params = {}
            
            if topic:
                params['topic'] = topic
            if fecha_desde:
                params['fecha_desde'] = fecha_desde
            if fecha_hasta:
                params['fecha_hasta'] = fecha_hasta
            
            response = self.session.get(f"{self.base_url}/stats", params=params)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Error obteniendo estadísticas: {e}")
            return {"error": str(e)}


def example_health_check():
    """Ejemplo de verificación de salud"""
    print("\n🔧 EJEMPLO 1: Health Check")
    print("=" * 50)
    
    client = APIClient()
    
    # Verificar estado de la API
    health = client.health_check()
    
    if "error" not in health:
        print("✅ API está funcionando")
        print(f"   Status: {health.get('status')}")
        print(f"   Versión: {health.get('version')}")
        print(f"   Base de datos: {health.get('database_status')}")
        print(f"   Timestamp: {health.get('timestamp')}")
        return True
    else:
        print("❌ API no está disponible")
        print(f"   Error: {health['error']}")
        return False


def example_get_topics():
    """Ejemplo de obtención de tópicos disponibles"""
    print("\n🔧 EJEMPLO 2: Tópicos Disponibles")
    print("=" * 50)
    
    client = APIClient()
    
    # Obtener tópicos disponibles
    topics_response = client.get_available_topics()
    
    if "error" not in topics_response:
        topics = topics_response.get('topics', [])
        total_topics = topics_response.get('total_topics', 0)
        
        print(f"✅ Se encontraron {total_topics} tópicos disponibles")
        
        if topics:
            print("\n📋 Primeros 5 tópicos:")
            for i, topic_info in enumerate(topics[:5], 1):
                print(f"   {i}. {topic_info['topic']}")
                print(f"      Canal ID: {topic_info['canal_id']}")
                print(f"      Proyecto: {topic_info['proyecto']}")
                print(f"      Unidad: {topic_info['unidad']}")
                print(f"      Dispositivo: {topic_info['dispositivo']}")
                print(f"      Canal: {topic_info['canal']}")
                print()
        
        return topics
    else:
        print("❌ Error obteniendo tópicos")
        print(f"   Error: {topics_response['error']}")
        return []


def example_basic_query():
    """Ejemplo de consulta básica"""
    print("\n🔧 EJEMPLO 3: Consulta Básica")
    print("=" * 50)
    
    client = APIClient()
    
    # Consulta básica sin filtros
    response = client.get_sensor_data(limit=10)
    
    if "error" not in response:
        data = response.get('data', [])
        metadata = response.get('metadata', {})
        pagination = response.get('pagination', {})
        
        print("✅ Consulta exitosa")
        print(f"   Total de registros: {metadata.get('total_registros', 0)}")
        print(f"   Registros retornados: {len(data)}")
        print(f"   Página actual: {pagination.get('pagina_actual', 1)}")
        print(f"   Total de páginas: {pagination.get('total_paginas', 1)}")
        
        if data:
            print("\n📝 Primer registro:")
            primer_registro = data[0]
            print(f"   ID: {primer_registro.get('id')}")
            print(f"   Tópico: {primer_registro.get('topic')}")
            print(f"   Timestamp: {primer_registro.get('timestamp')}")
            print(f"   Valor: {primer_registro.get('valor')}")
            print(f"   Tipo: {primer_registro.get('tipo_valor')}")
            print(f"   Calidad: {primer_registro.get('calidad')}")
        
        return True
    else:
        print("❌ Error en consulta básica")
        print(f"   Error: {response['error']}")
        return False


def example_topic_filter():
    """Ejemplo de filtro por tópico"""
    print("\n🔧 EJEMPLO 4: Filtro por Tópico")
    print("=" * 50)
    
    client = APIClient()
    
    # Filtro por tópico específico
    topic_filter = "iot/proyecto_001/+/+/+/canal_temperatura"
    
    print(f"🔍 Consultando datos con filtro: {topic_filter}")
    
    response = client.get_sensor_data(
        topic=topic_filter,
        limit=20
    )
    
    if "error" not in response:
        data = response.get('data', [])
        metadata = response.get('metadata', {})
        
        print("✅ Filtro por tópico exitoso")
        print(f"   Total de registros encontrados: {metadata.get('total_registros', 0)}")
        print(f"   Registros retornados: {len(data)}")
        
        if data:
            print("\n📊 Resumen de datos:")
            valores = [registro.get('valor') for registro in data if registro.get('valor') is not None]
            if valores:
                print(f"   Valor mínimo: {min(valores)}")
                print(f"   Valor máximo: {max(valores)}")
                print(f"   Valor promedio: {sum(valores) / len(valores):.2f}")
        
        return True
    else:
        print("❌ Error en filtro por tópico")
        print(f"   Error: {response['error']}")
        return False


def example_date_range_filter():
    """Ejemplo de filtro por rango de fechas"""
    print("\n🔧 EJEMPLO 5: Filtro por Rango de Fechas")
    print("=" * 50)
    
    client = APIClient()
    
    # Calcular fechas para el último día
    fecha_hasta = datetime.now(timezone.utc)
    fecha_desde = fecha_hasta - timedelta(days=1)
    
    fecha_desde_str = fecha_desde.isoformat()
    fecha_hasta_str = fecha_hasta.isoformat()
    
    print(f"📅 Consultando datos del período:")
    print(f"   Desde: {fecha_desde_str}")
    print(f"   Hasta: {fecha_hasta_str}")
    
    response = client.get_sensor_data(
        fecha_desde=fecha_desde_str,
        fecha_hasta=fecha_hasta_str,
        limit=50
    )
    
    if "error" not in response:
        data = response.get('data', [])
        metadata = response.get('metadata', {})
        
        print("✅ Filtro por fecha exitoso")
        print(f"   Total de registros en el período: {metadata.get('total_registros', 0)}")
        print(f"   Registros retornados: {len(data)}")
        
        if data:
            # Agrupar por hora para mostrar distribución temporal
            horas = {}
            for registro in data:
                timestamp = registro.get('timestamp')
                if timestamp:
                    try:
                        dt = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        hora = dt.hour
                        horas[hora] = horas.get(hora, 0) + 1
                    except:
                        pass
            
            if horas:
                print("\n⏰ Distribución por hora:")
                for hora in sorted(horas.keys()):
                    print(f"   {hora:02d}:00 - {horas[hora]} registros")
        
        return True
    else:
        print("❌ Error en filtro por fecha")
        print(f"   Error: {response['error']}")
        return False


def example_quality_filter():
    """Ejemplo de filtro por calidad de datos"""
    print("\n🔧 EJEMPLO 6: Filtro por Calidad")
    print("=" * 50)
    
    client = APIClient()
    
    # Filtrar solo datos con calidad OK
    print("🔍 Consultando datos con calidad OK")
    
    response = client.get_sensor_data(
        calidad="OK",
        limit=30
    )
    
    if "error" not in response:
        data = response.get('data', [])
        metadata = response.get('metadata', {})
        
        print("✅ Filtro por calidad exitoso")
        print(f"   Total de registros con calidad OK: {metadata.get('total_registros', 0)}")
        print(f"   Registros retornados: {len(data)}")
        
        # Mostrar distribución por tópico
        topics_count = {}
        for registro in data:
            topic = registro.get('topic', 'unknown')
            topics_count[topic] = topics_count.get(topic, 0) + 1
        
        if topics_count:
            print("\n📡 Distribución por tópico:")
            for topic, count in sorted(topics_count.items(), key=lambda x: x[1], reverse=True):
                print(f"   {topic}: {count} registros")
        
        return True
    else:
        print("❌ Error en filtro por calidad")
        print(f"   Error: {response['error']}")
        return False


def example_pagination():
    """Ejemplo de paginación"""
    print("\n🔧 EJEMPLO 7: Paginación")
    print("=" * 50)
    
    client = APIClient()
    
    # Consultar con paginación
    registros_por_pagina = 10
    total_paginas = 3
    
    print(f"📄 Consultando {total_paginas} páginas con {registros_por_pagina} registros por página")
    
    todas_las_paginas = []
    
    for pagina in range(1, total_paginas + 1):
        offset = (pagina - 1) * registros_por_pagina
        
        print(f"\n   Página {pagina} (offset: {offset})")
        
        response = client.get_sensor_data(
            limit=registros_por_pagina,
            offset=offset
        )
        
        if "error" not in response:
            data = response.get('data', [])
            pagination = response.get('pagination', {})
            
            print(f"     ✅ Registros obtenidos: {len(data)}")
            print(f"     📊 Página actual: {pagination.get('pagina_actual')}")
            print(f"     📊 Total de páginas: {pagination.get('total_paginas')}")
            
            todas_las_paginas.extend(data)
        else:
            print(f"     ❌ Error: {response['error']}")
            break
    
    print(f"\n📋 Total de registros obtenidos: {len(todas_las_paginas)}")
    
    return len(todas_las_paginas) > 0


def example_stats():
    """Ejemplo de obtención de estadísticas"""
    print("\n🔧 EJEMPLO 8: Estadísticas")
    print("=" * 50)
    
    client = APIClient()
    
    # Obtener estadísticas generales
    print("📊 Obteniendo estadísticas generales")
    
    response = client.get_stats()
    
    if "error" not in response:
        stats = response.get('stats', {})
        
        print("✅ Estadísticas obtenidas exitosamente")
        print(f"   Total de registros: {stats.get('total_registros', 0)}")
        
        # Estadísticas por calidad
        por_calidad = stats.get('por_calidad', {})
        if por_calidad:
            print("\n   📈 Distribución por calidad:")
            for calidad, count in por_calidad.items():
                print(f"     {calidad}: {count} registros")
        
        # Estadísticas por tipo
        por_tipo = stats.get('por_tipo', {})
        if por_tipo:
            print("\n   📊 Distribución por tipo:")
            for tipo, count in por_tipo.items():
                print(f"     {tipo}: {count} registros")
        
        # Estadísticas de procesamiento
        procesamiento = stats.get('procesamiento', {})
        if procesamiento:
            print("\n   ⚙️  Estado de procesamiento:")
            print(f"     Total: {procesamiento.get('total', 0)}")
            print(f"     Procesados: {procesamiento.get('procesados', 0)}")
            print(f"     Validados: {procesamiento.get('validados', 0)}")
            print(f"     % Procesados: {procesamiento.get('porcentaje_procesados', 0):.1f}%")
            print(f"     % Validados: {procesamiento.get('porcentaje_validados', 0):.1f}%")
        
        return True
    else:
        print("❌ Error obteniendo estadísticas")
        print(f"   Error: {response['error']}")
        return False


def example_canal_specific():
    """Ejemplo de consulta por canal específico"""
    print("\n🔧 EJEMPLO 9: Consulta por Canal Específico")
    print("=" * 50)
    
    client = APIClient()
    
    # Primero obtener algunos tópicos para encontrar un canal_id
    topics_response = client.get_available_topics()
    
    if "error" not in topics_response and topics_response.get('topics'):
        # Usar el primer tópico disponible
        primer_topic = topics_response['topics'][0]
        canal_id = primer_topic['canal_id']
        
        print(f"🔍 Consultando datos del canal: {canal_id}")
        print(f"   Tópico: {primer_topic['topic']}")
        
        # Consultar datos del canal específico
        response = client.get_sensor_data_by_canal(
            canal_id=canal_id,
            limit=15
        )
        
        if "error" not in response:
            data = response.get('data', [])
            metadata = response.get('metadata', {})
            
            print("✅ Consulta por canal exitosa")
            print(f"   Total de registros del canal: {metadata.get('total_registros', 0)}")
            print(f"   Registros retornados: {len(data)}")
            
            if data:
                print("\n📝 Últimos registros:")
                for i, registro in enumerate(data[:5], 1):
                    print(f"   {i}. {registro.get('timestamp')} - Valor: {registro.get('valor')} ({registro.get('tipo_valor')})")
            
            return True
        else:
            print("❌ Error consultando canal específico")
            print(f"   Error: {response['error']}")
            return False
    else:
        print("❌ No se pudieron obtener tópicos para el ejemplo")
        return False


def example_error_handling():
    """Ejemplo de manejo de errores"""
    print("\n🔧 EJEMPLO 10: Manejo de Errores")
    print("=" * 50)
    
    client = APIClient()
    
    # Probar parámetros inválidos
    print("🧪 Probando manejo de errores...")
    
    # 1. Fecha inválida
    print("\n   1. Fecha inválida:")
    response = client.get_sensor_data(fecha_desde="fecha-invalida")
    if "error" in response:
        print("   ✅ Error manejado correctamente")
        print(f"      Error: {response.get('error', 'N/A')}")
    else:
        print("   ❌ Error no manejado")
    
    # 2. Límite inválido
    print("\n   2. Límite inválido:")
    response = client.get_sensor_data(limit=9999)  # Debería estar limitado a 1000
    if "error" in response:
        print("   ✅ Error manejado correctamente")
        print(f"      Error: {response.get('error', 'N/A')}")
    else:
        print("   ❌ Error no manejado")
    
    # 3. Tópico inexistente
    print("\n   3. Tópico inexistente:")
    response = client.get_sensor_data(topic="iot/proyecto_inexistente/+/+/+/canal_inexistente")
    if "error" in response:
        print("   ✅ Error manejado correctamente")
        print(f"      Error: {response.get('error', 'N/A')}")
    else:
        print("   ❌ Error no manejado")
    
    return True


def main():
    """Función principal"""
    print("🚀 Ejemplos de Uso de la API REST - IoT Middleware")
    print("=" * 60)
    
    # Verificar que la API esté funcionando
    print("🔍 Verificando estado de la API...")
    
    if not example_health_check():
        print("\n❌ La API no está disponible")
        print("💡 Asegúrate de que la API esté ejecutándose en http://localhost:8000")
        print("💡 Puedes iniciarla con: python src/iot_middleware/api/api.py")
        return False
    
    # Ejecutar ejemplos
    examples = [
        ("Health Check", example_health_check),
        ("Tópicos Disponibles", example_get_topics),
        ("Consulta Básica", example_basic_query),
        ("Filtro por Tópico", example_topic_filter),
        ("Filtro por Rango de Fechas", example_date_range_filter),
        ("Filtro por Calidad", example_quality_filter),
        ("Paginación", example_pagination),
        ("Estadísticas", example_stats),
        ("Consulta por Canal Específico", example_canal_specific),
        ("Manejo de Errores", example_error_handling),
    ]
    
    results = []
    
    for example_name, example_func in examples:
        print(f"\n{'='*20} {example_name} {'='*20}")
        try:
            success = example_func()
            results.append((example_name, success))
        except Exception as e:
            print(f"❌ Error inesperado en {example_name}: {e}")
            results.append((example_name, False))
    
    # Resumen de resultados
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE EJEMPLOS")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for example_name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{example_name}: {status}")
        if success:
            passed += 1
    
    print(f"\n🎯 Resultado: {passed}/{total} ejemplos funcionaron")
    
    if passed == total:
        print("🎉 ¡Todos los ejemplos funcionaron exitosamente!")
        print("\n💡 La API REST está funcionando correctamente")
        print("\n🔧 Funcionalidades disponibles:")
        print("   ✅ Endpoint GET /data con filtros por tópico y fechas")
        print("   ✅ Filtros por calidad, procesamiento y validación")
        print("   ✅ Paginación completa")
        print("   ✅ Consulta por canal específico")
        print("   ✅ Lista de tópicos disponibles")
        print("   ✅ Estadísticas de datos")
        print("   ✅ Manejo de errores robusto")
        print("   ✅ Respuestas JSON estándar")
        print("   ✅ Auditoría automática de consultas")
        return True
    else:
        print("⚠️  Algunos ejemplos fallaron")
        print("\n💡 Revisa los errores y asegúrate de que:")
        print("   - La API esté ejecutándose")
        print("   - La base de datos esté disponible")
        print("   - Existan datos de sensores para consultar")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
