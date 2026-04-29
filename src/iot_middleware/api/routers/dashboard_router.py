"""
Router del Dashboard - IoT Middleware
=====================================

Este router proporciona endpoints WebSocket para el dashboard de monitoreo
en tiempo real, consumiendo eventos de RabbitMQ.
"""

import json
import logging
import asyncio
import threading
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from fastapi.responses import HTMLResponse

from ...messaging import RabbitMQClient, MonitoringEvent, EventType, create_rabbitmq_client
from ...config import RabbitMQConfig, load_config

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/dashboard", tags=["dashboard"])

# Almacenar conexiones WebSocket activas
active_connections: List[WebSocket] = []

# Cliente RabbitMQ compartido
rabbitmq_client: Optional[RabbitMQClient] = None
rabbitmq_thread: Optional[threading.Thread] = None


def get_rabbitmq_client() -> Optional[RabbitMQClient]:
    """Obtiene el cliente RabbitMQ configurado"""
    global rabbitmq_client
    
    if rabbitmq_client is None:
        try:
            config = load_config()
            if config and hasattr(config, 'rabbitmq') and config.rabbitmq.enable_monitoring:
                rabbitmq_client = create_rabbitmq_client(config.rabbitmq)
                if not rabbitmq_client.connect():
                    logger.error("❌ No se pudo conectar a RabbitMQ para dashboard")
                    return None
                
                # Suscribirse a todos los tipos de eventos
                rabbitmq_client.subscribe_to_events(
                    event_types=list(EventType),
                    callback=_on_rabbitmq_event
                )
                
                # Iniciar consumo en thread separado
                _start_rabbitmq_consumer()
                
                logger.info("✅ Cliente RabbitMQ configurado para dashboard")
            else:
                logger.warning("⚠️  RabbitMQ no está habilitado en la configuración")
        except Exception as e:
            logger.error(f"❌ Error configurando RabbitMQ: {e}")
    
    return rabbitmq_client


def _on_rabbitmq_event(event: MonitoringEvent):
    """Callback cuando llega un evento de RabbitMQ"""
    try:
        # Enviar evento a todas las conexiones WebSocket activas
        message = json.dumps(event.to_dict())
        _broadcast_message(message)
    except Exception as e:
        logger.error(f"❌ Error procesando evento RabbitMQ: {e}")


def _broadcast_message(message: str):
    """Envía un mensaje a todas las conexiones WebSocket activas"""
    disconnected = []
    
    for connection in active_connections:
        try:
            # Verificar que la conexión esté activa
            if connection.client_state.name == "CONNECTED":
                asyncio.run(connection.send_text(message))
            else:
                disconnected.append(connection)
        except Exception as e:
            logger.debug(f"Error enviando mensaje a conexión: {e}")
            disconnected.append(connection)
    
    # Remover conexiones desconectadas
    for conn in disconnected:
        if conn in active_connections:
            active_connections.remove(conn)


def _start_rabbitmq_consumer():
    """Inicia el consumidor de RabbitMQ en un thread separado"""
    global rabbitmq_thread
    
    if rabbitmq_thread and rabbitmq_thread.is_alive():
        return
    
    def consumer_worker():
        try:
            if rabbitmq_client:
                rabbitmq_client.start_consuming()
        except Exception as e:
            logger.error(f"❌ Error en consumidor RabbitMQ: {e}")
    
    rabbitmq_thread = threading.Thread(
        target=consumer_worker,
        name="RabbitMQConsumer",
        daemon=True
    )
    rabbitmq_thread.start()
    logger.info("🔄 Consumidor RabbitMQ iniciado")


@router.get("/", response_class=HTMLResponse)
async def dashboard_page():
    """Página HTML del dashboard"""
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>IoT Middleware - Dashboard de Monitoreo</title>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: #333;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
            }
            
            .header {
                background: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            }
            
            .header h1 {
                color: #667eea;
                margin-bottom: 10px;
            }
            
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
                margin-left: 10px;
            }
            
            .status.connected {
                background: #4caf50;
                color: white;
            }
            
            .status.disconnected {
                background: #f44336;
                color: white;
            }
            
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                transition: transform 0.2s;
            }
            
            .metric-card:hover {
                transform: translateY(-5px);
            }
            
            .metric-card h3 {
                color: #666;
                font-size: 14px;
                margin-bottom: 10px;
                text-transform: uppercase;
            }
            
            .metric-value {
                font-size: 32px;
                font-weight: bold;
                color: #667eea;
            }
            
            .events-panel {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                max-height: 500px;
                overflow-y: auto;
            }
            
            .events-panel h2 {
                margin-bottom: 15px;
                color: #667eea;
            }
            
            .event-item {
                padding: 10px;
                border-left: 4px solid #667eea;
                margin-bottom: 10px;
                background: #f5f5f5;
                border-radius: 4px;
            }
            
            .event-header {
                display: flex;
                justify-content: space-between;
                margin-bottom: 5px;
            }
            
            .event-type {
                font-weight: bold;
                color: #667eea;
            }
            
            .event-time {
                color: #999;
                font-size: 12px;
            }
            
            .event-service {
                color: #666;
                font-size: 14px;
            }
            
            .event-data {
                margin-top: 5px;
                font-size: 12px;
                color: #555;
            }
            
            .severity-info { border-left-color: #2196F3; }
            .severity-warning { border-left-color: #FF9800; }
            .severity-error { border-left-color: #F44336; }
            .severity-critical { border-left-color: #9C27B0; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📊 IoT Middleware - Dashboard de Monitoreo</h1>
                <span id="connectionStatus" class="status disconnected">Desconectado</span>
            </div>
            
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>Mensajes Procesados</h3>
                    <div class="metric-value" id="messagesProcessed">0</div>
                </div>
                <div class="metric-card">
                    <h3>Mensajes Fallidos</h3>
                    <div class="metric-value" id="messagesFailed">0</div>
                </div>
                <div class="metric-card">
                    <h3>Operaciones BD</h3>
                    <div class="metric-value" id="databaseOps">0</div>
                </div>
                <div class="metric-card">
                    <h3>Protocolos Activos</h3>
                    <div class="metric-value" id="activeProtocols">0</div>
                </div>
                <div class="metric-card">
                    <h3>Dispositivos Activos</h3>
                    <div class="metric-value" id="activeDevices">0</div>
                </div>
                <div class="metric-card">
                    <h3>Uptime (segundos)</h3>
                    <div class="metric-value" id="uptime">0</div>
                </div>
            </div>
            
            <div class="events-panel">
                <h2>📡 Eventos en Tiempo Real</h2>
                <div id="eventsContainer"></div>
            </div>
        </div>
        
        <script>
            const ws = new WebSocket(`ws://${window.location.host}/dashboard/ws`);
            const eventsContainer = document.getElementById('eventsContainer');
            const statusEl = document.getElementById('connectionStatus');
            
            // Métricas
            const metrics = {
                messagesProcessed: 0,
                messagesFailed: 0,
                databaseOps: 0,
                activeProtocols: 0,
                activeDevices: 0,
                uptime: 0
            };
            
            ws.onopen = () => {
                console.log('✅ Conectado al WebSocket');
                statusEl.textContent = 'Conectado';
                statusEl.className = 'status connected';
            };
            
            ws.onmessage = (event) => {
                const data = JSON.parse(event.data);
                handleEvent(data);
            };
            
            ws.onerror = (error) => {
                console.error('❌ Error en WebSocket:', error);
                statusEl.textContent = 'Error';
                statusEl.className = 'status disconnected';
            };
            
            ws.onclose = () => {
                console.log('🔌 Desconectado del WebSocket');
                statusEl.textContent = 'Desconectado';
                statusEl.className = 'status disconnected';
            };
            
            function handleEvent(event) {
                // Actualizar métricas según el tipo de evento
                if (event.event_type === 'metric') {
                    const metric = event.data.metric;
                    const value = event.data.value;
                    
                    if (metric === 'system.messages_processed') {
                        metrics.messagesProcessed = value;
                        document.getElementById('messagesProcessed').textContent = value.toLocaleString();
                    } else if (metric === 'system.messages_failed') {
                        metrics.messagesFailed = value;
                        document.getElementById('messagesFailed').textContent = value.toLocaleString();
                    } else if (metric === 'system.database_operations') {
                        metrics.databaseOps = value;
                        document.getElementById('databaseOps').textContent = value.toLocaleString();
                    } else if (metric === 'system.active_protocols') {
                        metrics.activeProtocols = value;
                        document.getElementById('activeProtocols').textContent = value;
                    } else if (metric === 'system.active_devices') {
                        metrics.activeDevices = value;
                        document.getElementById('activeDevices').textContent = value;
                    } else if (metric === 'system.uptime_seconds') {
                        metrics.uptime = value;
                        document.getElementById('uptime').textContent = value.toLocaleString();
                    }
                }
                
                // Agregar evento a la lista
                addEventToPanel(event);
            }
            
            function addEventToPanel(event) {
                const eventDiv = document.createElement('div');
                eventDiv.className = `event-item severity-${event.severity}`;
                
                const time = new Date(event.timestamp).toLocaleTimeString();
                
                eventDiv.innerHTML = `
                    <div class="event-header">
                        <span class="event-type">${event.event_type.toUpperCase()}</span>
                        <span class="event-time">${time}</span>
                    </div>
                    <div class="event-service">Servicio: ${event.service}</div>
                    <div class="event-data">${JSON.stringify(event.data, null, 2)}</div>
                `;
                
                eventsContainer.insertBefore(eventDiv, eventsContainer.firstChild);
                
                // Limitar a 50 eventos
                while (eventsContainer.children.length > 50) {
                    eventsContainer.removeChild(eventsContainer.lastChild);
                }
            }
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    Endpoint WebSocket para el dashboard de monitoreo
    
    Recibe eventos de RabbitMQ y los envía al cliente en tiempo real
    """
    await websocket.accept()
    active_connections.append(websocket)
    
    logger.info(f"✅ Cliente WebSocket conectado. Total: {len(active_connections)}")
    
    try:
        # Enviar mensaje de bienvenida
        await websocket.send_json({
            "type": "welcome",
            "message": "Conectado al dashboard de monitoreo",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        
        # Mantener conexión activa
        while True:
            # Esperar mensajes del cliente (ping/pong)
            try:
                data = await websocket.receive_text()
                # Responder a pings
                if data == "ping":
                    await websocket.send_text("pong")
            except WebSocketDisconnect:
                break
                
    except WebSocketDisconnect:
        logger.info("🔌 Cliente WebSocket desconectado")
    except Exception as e:
        logger.error(f"❌ Error en WebSocket: {e}")
    finally:
        if websocket in active_connections:
            active_connections.remove(websocket)
        logger.info(f"📊 Conexiones WebSocket activas: {len(active_connections)}")


@router.get("/health")
async def dashboard_health():
    """Verifica el estado del dashboard"""
    client = get_rabbitmq_client()
    
    if client:
        health = client.health_check()
        return {
            "status": "healthy" if health.get("connected") else "unhealthy",
            "rabbitmq": health,
            "active_connections": len(active_connections)
        }
    else:
        return {
            "status": "unhealthy",
            "message": "RabbitMQ no configurado o no conectado",
            "active_connections": len(active_connections)
        }
