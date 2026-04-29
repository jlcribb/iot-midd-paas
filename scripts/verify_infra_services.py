#!/usr/bin/env python3
"""
Verifica conectividad y operación básica de InfluxDB y RabbitMQ.
"""

from __future__ import annotations

import argparse
import json
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

import pika
from influxdb_client import InfluxDBClient, Point
from influxdb_client.client.write_api import SYNCHRONOUS

from iot_middleware.config import load_config


@dataclass
class CheckResult:
    service: str
    ok: bool
    detail: str
    latency_ms: Optional[int] = None


def check_influx(config) -> CheckResult:
    started = time.time()
    try:
        client = InfluxDBClient(
            url=config.influxdb.url,
            token=config.influxdb.token,
            org=config.influxdb.org,
            timeout=8000,
        )

        health = client.health()
        if health.status != "pass":
            return CheckResult(
                service="influxdb",
                ok=False,
                detail=f"health={health.status} message={health.message}",
                latency_ms=int((time.time() - started) * 1000),
            )

        test_value = int(time.time())
        point = (
            Point("infra_verification")
            .tag("source", "verify_infra_services")
            .field("value", test_value)
            .time(datetime.now(timezone.utc))
        )
        client.write_api(write_options=SYNCHRONOUS).write(
            bucket=config.influxdb.bucket,
            org=config.influxdb.org,
            record=point,
        )

        query = f"""
from(bucket: "{config.influxdb.bucket}")
  |> range(start: -5m)
  |> filter(fn: (r) => r._measurement == "infra_verification")
  |> filter(fn: (r) => r.source == "verify_infra_services")
  |> last()
"""
        tables = client.query_api().query(query=query, org=config.influxdb.org)
        has_rows = any(table.records for table in tables)
        if not has_rows:
            return CheckResult(
                service="influxdb",
                ok=False,
                detail="escritura OK pero query sin resultados",
                latency_ms=int((time.time() - started) * 1000),
            )

        return CheckResult(
            service="influxdb",
            ok=True,
            detail="health OK + write/read OK",
            latency_ms=int((time.time() - started) * 1000),
        )
    except Exception as exc:  # pragma: no cover - diagnóstico operativo
        return CheckResult(
            service="influxdb",
            ok=False,
            detail=str(exc),
            latency_ms=int((time.time() - started) * 1000),
        )


def check_rabbitmq(config) -> CheckResult:
    started = time.time()
    connection = None
    channel = None
    try:
        credentials = pika.PlainCredentials(
            username=config.rabbitmq.username,
            password=config.rabbitmq.password,
        )
        parameters = pika.ConnectionParameters(
            host=config.rabbitmq.host,
            port=config.rabbitmq.port,
            virtual_host=config.rabbitmq.virtual_host,
            credentials=credentials,
            heartbeat=config.rabbitmq.heartbeat,
            connection_attempts=config.rabbitmq.connection_attempts,
            retry_delay=config.rabbitmq.retry_delay,
        )
        connection = pika.BlockingConnection(parameters)
        channel = connection.channel()

        exchange = config.rabbitmq.exchange
        queue_name = f"{config.rabbitmq.queue_prefix}.infra.verify.{int(time.time())}"
        routing_key = f"{config.rabbitmq.queue_prefix}.infra.verify"
        payload = {"ts": datetime.now(timezone.utc).isoformat(), "probe": "rabbitmq"}

        channel.exchange_declare(exchange=exchange, exchange_type="topic", durable=True)
        channel.queue_declare(queue=queue_name, durable=False, auto_delete=True)
        channel.queue_bind(queue=queue_name, exchange=exchange, routing_key=routing_key)
        channel.basic_publish(
            exchange=exchange,
            routing_key=routing_key,
            body=json.dumps(payload),
            properties=pika.BasicProperties(content_type="application/json"),
        )

        method_frame, _, body = channel.basic_get(queue=queue_name, auto_ack=True)
        if method_frame is None:
            return CheckResult(
                service="rabbitmq",
                ok=False,
                detail="publish OK pero consumo inmediato vacío",
                latency_ms=int((time.time() - started) * 1000),
            )

        decoded = json.loads(body.decode("utf-8"))
        if decoded.get("probe") != "rabbitmq":
            return CheckResult(
                service="rabbitmq",
                ok=False,
                detail=f"mensaje inválido: {decoded}",
                latency_ms=int((time.time() - started) * 1000),
            )

        return CheckResult(
            service="rabbitmq",
            ok=True,
            detail="connect + publish + consume OK",
            latency_ms=int((time.time() - started) * 1000),
        )
    except Exception as exc:  # pragma: no cover - diagnóstico operativo
        return CheckResult(
            service="rabbitmq",
            ok=False,
            detail=str(exc),
            latency_ms=int((time.time() - started) * 1000),
        )
    finally:
        try:
            if channel and channel.is_open:
                channel.close()
        except Exception:
            pass
        try:
            if connection and connection.is_open:
                connection.close()
        except Exception:
            pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Verificación operativa InfluxDB/RabbitMQ")
    parser.add_argument("--config", default="config.yaml", help="Ruta config YAML")
    args = parser.parse_args()

    config = load_config(args.config)
    influx = check_influx(config)
    rabbit = check_rabbitmq(config)

    report = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_path": args.config,
        "influxdb": asdict(influx),
        "rabbitmq": asdict(rabbit),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if influx.ok and rabbit.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
