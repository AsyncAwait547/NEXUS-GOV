"""REST API Routes — City state, agents, audit, scenarios, health."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

router = APIRouter(prefix="/api/v1")


# ── Dependencies (set by main.py) ──
_cdil = None
_event_bus = None
_audit_chain = None
_scenario_engine = None
_agents = {}


def init_routes(cdil, event_bus, audit_chain, scenario_engine, agents: dict):
    global _cdil, _event_bus, _audit_chain, _scenario_engine, _agents
    _cdil = cdil
    _event_bus = event_bus
    _audit_chain = audit_chain
    _scenario_engine = scenario_engine
    _agents = agents


# ── Request Models ──

class ScenarioRequest(BaseModel):
    scenario: str


# ── City State ──

@router.get("/city/state")
async def get_city_state():
    """Full CDIL snapshot."""
    return await _cdil.get_snapshot()


@router.get("/city/zones")
async def get_zones():
    """All zone states."""
    snapshot = await _cdil.get_snapshot()
    zones = {}
    for key, val in snapshot.items():
        if key.startswith("zone:"):
            parts = key.split(":")
            if len(parts) >= 3:
                zone_id = parts[1]
                prop = parts[2]
                if zone_id not in zones:
                    zones[zone_id] = {"id": zone_id}
                zones[zone_id][prop] = val
    return list(zones.values())


@router.get("/city/zones/{zone_id}")
async def get_zone(zone_id: str):
    """Specific zone state."""
    state = await _cdil.get_zone_state(zone_id)
    if not state:
        raise HTTPException(404, f"Zone {zone_id} not found")
    return {"id": zone_id, **state}


# ── Agents ──

@router.get("/agents")
async def get_agents():
    """All agent statuses."""
    return {aid: agent.get_status() for aid, agent in _agents.items()}


@router.get("/agents/{agent_id}/status")
async def get_agent_status(agent_id: str):
    """Specific agent status."""
    if agent_id not in _agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return _agents[agent_id].get_status()


@router.get("/agents/{agent_id}/reasoning")
async def get_agent_reasoning(agent_id: str, limit: int = 20):
    """Agent reasoning log (from audit chain)."""
    if agent_id not in _agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    entries = _audit_chain.get_recent(limit)
    return [e for e in entries if e.get("agent") == agent_id]


@router.get("/agents/{agent_id}/memory")
async def get_agent_memory(agent_id: str):
    """Agent episodic memory."""
    if agent_id not in _agents:
        raise HTTPException(404, f"Agent {agent_id} not found")
    return _agents[agent_id].episodic_memory


# ── Events ──

@router.get("/events/timeline")
async def get_timeline():
    """Event timeline."""
    return await _event_bus.get_timeline()


@router.get("/events/messages")
async def get_messages():
    """Inter-agent messages from broadcast stream."""
    return await _event_bus.get_messages(_event_bus.BROADCAST_STREAM)


# ── Audit ──

@router.get("/audit/chain")
async def get_audit_chain(limit: int = 50):
    """Full audit trail."""
    return _audit_chain.get_recent(limit)


@router.get("/audit/verify")
async def verify_audit():
    """Chain integrity verification."""
    valid, message, count = _audit_chain.verify_chain()
    return {"valid": valid, "message": message, "decisions_count": count}


# ── Scenarios ──

@router.post("/scenarios/inject")
async def inject_scenario(req: ScenarioRequest):
    """Trigger a crisis scenario."""
    result = await _scenario_engine.inject_scenario(req.scenario)
    if "error" in result:
        raise HTTPException(400, result["error"])
    return result


@router.get("/scenarios/status")
async def scenario_status():
    """Current scenario status."""
    return await _scenario_engine.get_status()


@router.post("/scenarios/reset")
async def reset_scenario():
    """Reset active scenario."""
    await _scenario_engine.reset()
    return {"status": "reset"}


# ── IoT Sensors (Hackathon) ──

class SensorPayload(BaseModel):
    sensor_id: str
    type: str
    value: float
    unit: str
    lat: float
    lng: float


@router.post("/sensors/ingest")
async def ingest_sensor_data(payload: SensorPayload):
    """Ingest live IoT data from physical sensors (e.g., smart phone)."""
    # Push to CDIL directly
    if payload.type == "water_level":
        zone = "zone_c1" # Force it to C1 for demo
        await _cdil.update_zone(zone, {"flood_risk": payload.value})
        msg = f"🌊 Live River Sensor in {zone}: {payload.value}{payload.unit}"
    elif payload.type == "seismic":
        zone = "zone_c3"
        await _cdil.update_zone(zone, {"structural_integrity": max(0, 100 - payload.value)})
        msg = f"💥 Live Seismic Sensor: Magnitude {payload.value} detected"
    else:
        msg = f"📡 Sensor {payload.sensor_id} reported {payload.value}{payload.unit}"

    # Push to Event Bus to wake agents
    await _event_bus.publish_timeline({
        "event": msg,
        "source": "Physical IoT Sensor",
        "severity": "CRITICAL" if payload.value > 50 else "WARNING"
    })
    
    return {"status": "ingested", "message": msg}


# ── Health ──

@router.get("/health")
async def health_check():
    """System health check."""
    try:
        snapshot = await _cdil.get_snapshot()
        redis_ok = len(snapshot) > 0
    except Exception:
        redis_ok = False

    agent_statuses = {aid: a.get_status()["status"] for aid, a in _agents.items()}
    audit_count = _audit_chain.get_count()
    chain_valid, _, _ = _audit_chain.verify_chain()

    return {
        "status": "healthy" if redis_ok else "degraded",
        "redis": "connected" if redis_ok else "disconnected",
        "agents": agent_statuses,
        "audit_chain": {"count": audit_count, "valid": chain_valid},
        "scenario": await _scenario_engine.get_status(),
    }
