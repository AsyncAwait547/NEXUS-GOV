"""NEXUS-GOV Backend — Main Application Entrypoint.

Production-grade async multi-agent orchestration system.
Combines FastAPI + Socket.IO + Redis + MQTT + InfluxDB + Agent Scheduling.
"""
import asyncio
import json
import logging
import os
import signal
import sys
import time

import redis.asyncio as aioredis
import socketio
import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from core.cdil import CDIL
from core.event_bus import EventBus
from core.audit_chain import AuditChain
from core.causal_engine import CausalEngine
from core.scenario_engine import ScenarioEngine
from core.mqtt_client import MQTTClient
from core.timeseries import TimeSeriesDB
from core.kafka_bridge import KafkaBridge
from api.websocket import create_sio, broadcast
from api.routes import router as api_router, init_routes
from api.override import router as override_router, init_override
from agents.flood_agent import FloodAgent
from agents.emergency_agent import EmergencyAgent
from agents.traffic_agent import TrafficAgent
from agents.power_agent import PowerAgent
from agents.meta_agent import MetaAgent

# ── Logging ──
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("nexus.main")

# ── FastAPI ──
app = FastAPI(
    title="NEXUS-GOV Backend",
    description="Autonomous Multi-Agent Orchestration for Urban Civic Infrastructure",
    version="2.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Socket.IO ──
sio = create_sio()
sio_app = socketio.ASGIApp(sio, other_asgi_app=app)

# ── Global State ──
redis_client = None
cdil = None
event_bus = None
audit_chain = None
causal_engine = None
scenario_engine = None
mqtt_client = None
timeseries_db = None
kafka_bridge = None
agents = {}
agent_tasks = []
system_active = True


async def ws_broadcast(event: str, data: dict):
    """Broadcast via Socket.IO to all clients."""
    await broadcast(sio, event, data)


def load_city_model() -> dict:
    """Load city model from JSON."""
    model_path = os.path.join(os.path.dirname(__file__), "data", "city_model.json")
    with open(model_path) as f:
        return json.load(f)


@app.on_event("startup")
async def startup():
    """Initialize all systems on startup."""
    global redis_client, cdil, event_bus, audit_chain, causal_engine
    global scenario_engine, agents, mqtt_client, timeseries_db, kafka_bridge

    logger.info("=" * 60)
    logger.info("NEXUS-GOV BACKEND — SYSTEM STARTUP v2.0")
    logger.info("=" * 60)

    # 1. Connect Redis
    try:
        redis_client = aioredis.from_url(
            settings.REDIS_URL,
            decode_responses=False,
            socket_connect_timeout=3,
        )
        await redis_client.ping()
        logger.info("✓ Redis connected")
    except Exception as e:
        logger.warning(f"⚠ Redis connection failed: {e}. Falling back to Fakeredis (in-memory).")
        try:
            from fakeredis import aioredis as fakeaioredis
            redis_client = fakeaioredis.FakeRedis(decode_responses=False)
            logger.info("✓ Fakeredis initialized successfully for demo mode")
        except ImportError:
            logger.error("Fakeredis is required if a physical Redis broker is unavailable. Please `pip install fakeredis`.")
            return

    # 2. Initialize core
    city_model = load_city_model()

    cdil = CDIL(redis_client)
    await cdil.initialize(city_model)
    logger.info("✓ CDIL initialized")

    event_bus = EventBus(redis_client)
    await event_bus.initialize()
    logger.info("✓ Event Bus initialized")

    os.makedirs("data", exist_ok=True)
    audit_chain = AuditChain(settings.AUDIT_DB_PATH)
    logger.info("✓ Audit Chain initialized (SHA-256 + HMAC + Merkle)")

    causal_engine = CausalEngine(cdil, city_model)
    logger.info("✓ Causal Engine initialized")

    scenario_engine = ScenarioEngine(cdil, event_bus, audit_chain, ws_broadcast)
    logger.info("✓ Scenario Engine initialized")

    # 3. Initialize InfluxDB TimeSeries
    if settings.INFLUXDB_ENABLED:
        timeseries_db = TimeSeriesDB(
            url=settings.INFLUXDB_URL,
            token=settings.INFLUXDB_TOKEN,
            org=settings.INFLUXDB_ORG,
            bucket=settings.INFLUXDB_BUCKET,
        )
        await timeseries_db.initialize()
        if timeseries_db._enabled:
            logger.info("✓ InfluxDB TimeSeries connected")
        else:
            logger.info("⚠ InfluxDB unavailable — continuing without time-series")
    else:
        logger.info("⊘ InfluxDB disabled by config")

    # 4. Initialize Kafka Bridge
    kafka_bridge = KafkaBridge(
        broker_url=settings.KAFKA_BROKER_URL,
        enabled=settings.USE_KAFKA,
    )
    await kafka_bridge.initialize()
    if kafka_bridge.enabled:
        logger.info("✓ Kafka/Redpanda bridge connected")
    else:
        logger.info("⊘ Kafka bridge disabled — using Redis Streams")

    # 5. Initialize MQTT Client
    if settings.MQTT_ENABLED:
        mqtt_client = MQTTClient(
            cdil=cdil,
            event_bus=event_bus,
            ws_broadcast=ws_broadcast,
            host=settings.MQTT_BROKER_HOST,
            port=settings.MQTT_BROKER_PORT,
        )
        await mqtt_client.start()
        logger.info("✓ MQTT Client initialized")
    else:
        logger.info("⊘ MQTT disabled by config")

    # 6. Create agents
    agent_classes = {
        "flood_agent": FloodAgent,
        "emergency_agent": EmergencyAgent,
        "traffic_agent": TrafficAgent,
        "power_agent": PowerAgent,
        "meta_orchestrator": MetaAgent,
    }

    for agent_id, AgentClass in agent_classes.items():
        agent = AgentClass(
            cdil=cdil,
            event_bus=event_bus,
            audit_chain=audit_chain,
            causal_engine=causal_engine,
            ws_broadcast=ws_broadcast,
        )
        agents[agent_id] = agent
        logger.info(f"✓ Agent created: {agent_id}")

    # 7. Wire up API routes (pass timeseries for dual-write)
    init_routes(cdil, event_bus, audit_chain, scenario_engine, agents, timeseries=timeseries_db)
    init_override(agents, cdil, audit_chain, ws_broadcast)

    # 8. Start agent loops
    for agent_id, agent in agents.items():
        task = asyncio.create_task(agent.start())
        agent_tasks.append(task)
        logger.info(f"✓ Agent loop started: {agent_id}")

    # 9. Log genesis
    audit_chain.log_decision(
        agent="system",
        action="system_startup",
        reasoning="NEXUS-GOV v2.0 backend initialized. All agents online.",
        cdil_state=await cdil.get_snapshot(),
    )

    # Broadcast initial state
    await ws_broadcast("agent_status_update", {
        "agents": {aid: a.get_status() for aid, a in agents.items()},
        "timestamp": time.time(),
    })

    logger.info("=" * 60)
    logger.info(f"NEXUS-GOV ONLINE — {len(agents)} agents deployed")
    logger.info(f"Demo mode: {settings.DEMO_MODE} | Mock LLM: {settings.MOCK_LLM}")
    logger.info(f"MQTT: {'ON' if settings.MQTT_ENABLED else 'OFF'} | "
                f"InfluxDB: {'ON' if timeseries_db and timeseries_db._enabled else 'OFF'} | "
                f"Kafka: {'ON' if kafka_bridge.enabled else 'OFF'}")
    logger.info(f"Weather API: {'ON' if settings.OPENWEATHERMAP_API_KEY else 'OFF'}")
    logger.info(f"Auth: JWT ({settings.JWT_ALGORITHM})")
    logger.info(f"API: http://{settings.HOST}:{settings.PORT}/docs")
    logger.info(f"WS:  ws://{settings.HOST}:{settings.PORT}/socket.io/")
    logger.info("=" * 60)


@app.on_event("shutdown")
async def shutdown():
    """Graceful shutdown."""
    global system_active
    system_active = False
    logger.info("NEXUS-GOV shutting down...")

    # Stop all agents
    for agent in agents.values():
        await agent.stop()

    # Cancel agent tasks
    for task in agent_tasks:
        task.cancel()

    # Stop MQTT
    if mqtt_client:
        await mqtt_client.stop()

    # Close InfluxDB
    if timeseries_db:
        await timeseries_db.close()

    # Close Kafka
    if kafka_bridge:
        await kafka_bridge.close()

    # Close Redis
    if redis_client:
        await redis_client.close()

    logger.info("NEXUS-GOV shutdown complete")


# Mount routes
app.include_router(api_router)
app.include_router(override_router)


@app.get("/")
async def root():
    return {
        "system": "NEXUS-GOV",
        "version": "2.0.0",
        "description": "Autonomous Multi-Agent Orchestration for Urban Civic Infrastructure",
        "docs": "/docs",
        "health": "/api/v1/health",
        "auth": "/api/v1/auth/login",
        "architecture": {
            "agents": 5,
            "mqtt": settings.MQTT_ENABLED,
            "influxdb": settings.INFLUXDB_ENABLED,
            "kafka": settings.USE_KAFKA,
            "rbac": "JWT + HMAC-SHA256",
            "audit": "SHA-256 Hash Chain + Merkle Tree",
        },
    }


# ── Entry Point ──
# The `sio_app` wraps FastAPI with Socket.IO
# Uvicorn should run `main:sio_app`

if __name__ == "__main__":
    uvicorn.run(
        "main:sio_app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,
        log_level="info",
    )

