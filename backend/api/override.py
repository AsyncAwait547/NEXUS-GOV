"""Human Override API — Pause, resume, reassign, force actions."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
import time
import logging

logger = logging.getLogger("nexus.override")

router = APIRouter(prefix="/api/v1/override")

# Set by main.py
_agents = {}
_cdil = None
_audit_chain = None
_ws_broadcast = None


def init_override(agents: dict, cdil, audit_chain, ws_broadcast):
    global _agents, _cdil, _audit_chain, _ws_broadcast
    _agents = agents
    _cdil = cdil
    _audit_chain = audit_chain
    _ws_broadcast = ws_broadcast


class OverrideRequest(BaseModel):
    reason: str = ""


class ForceActionRequest(BaseModel):
    action: str
    parameters: dict = {}
    reason: str = ""
    zones: List[str] = []


class ReassignRequest(BaseModel):
    from_agent: str
    to_agent: str
    resource_type: str
    reason: str = ""


@router.post("/pause")
async def pause_all(req: OverrideRequest):
    """Pause all agents."""
    for agent in _agents.values():
        agent.pause()

    entry = _audit_chain.log_decision(
        agent="HUMAN_OPERATOR",
        action="pause_all_agents",
        reasoning=f"Human override: {req.reason or 'Manual pause'}",
        cdil_state=await _cdil.get_snapshot(),
    )

    await _ws_broadcast("reasoning_log", {
        "agent": "system",
        "badge": "HUM",
        "message": f"⚠ HUMAN OVERRIDE: All agents PAUSED. Reason: {req.reason}",
        "severity": "critical",
        "timestamp": time.time(),
    })

    await _ws_broadcast("audit_entry", entry)

    return {"status": "all_paused", "agents_affected": list(_agents.keys())}


@router.post("/resume")
async def resume_all(req: OverrideRequest):
    """Resume all agents."""
    for agent in _agents.values():
        agent.resume()

    entry = _audit_chain.log_decision(
        agent="HUMAN_OPERATOR",
        action="resume_all_agents",
        reasoning=f"Human override: {req.reason or 'Manual resume'}",
        cdil_state=await _cdil.get_snapshot(),
    )

    await _ws_broadcast("reasoning_log", {
        "agent": "system",
        "badge": "HUM",
        "message": f"✓ HUMAN OVERRIDE: All agents RESUMED. Reason: {req.reason}",
        "severity": "info",
        "timestamp": time.time(),
    })

    await _ws_broadcast("audit_entry", entry)

    return {"status": "all_resumed", "agents_affected": list(_agents.keys())}


@router.post("/reassign")
async def reassign_resource(req: ReassignRequest):
    """Reassign a resource from one agent to another."""
    if req.from_agent not in _agents or req.to_agent not in _agents:
        raise HTTPException(404, "Agent not found")

    entry = _audit_chain.log_decision(
        agent="HUMAN_OPERATOR",
        action="reassign_resource",
        reasoning=f"Reassigning {req.resource_type} from {req.from_agent} to {req.to_agent}. {req.reason}",
        cdil_state=await _cdil.get_snapshot(),
        parameters=req.dict(),
    )

    await _ws_broadcast("reasoning_log", {
        "agent": "system",
        "badge": "HUM",
        "message": f"OVERRIDE: Reassigning {req.resource_type}: {req.from_agent} → {req.to_agent}.",
        "severity": "warning",
        "timestamp": time.time(),
    })

    await _ws_broadcast("audit_entry", entry)

    return {"status": "reassigned", "details": req.dict()}


@router.post("/force_action")
async def force_action(req: ForceActionRequest):
    """Force a manual action on the CDIL."""
    # Apply CDIL mutations directly
    cdil_updates = {}
    for key, value in req.parameters.items():
        await _cdil.update(key, value, source="HUMAN_OPERATOR")
        cdil_updates[key] = value

    entry = _audit_chain.log_decision(
        agent="HUMAN_OPERATOR",
        action=f"force_action:{req.action}",
        reasoning=f"Human override forced action: {req.action}. {req.reason}",
        cdil_state=await _cdil.get_snapshot(),
        parameters={"action": req.action, "updates": cdil_updates, "zones": req.zones},
    )

    await _ws_broadcast("reasoning_log", {
        "agent": "system",
        "badge": "HUM",
        "message": f"⚠ HUMAN OVERRIDE EXECUTED: {req.action}. Zones: {', '.join(req.zones) or 'ALL'}. Reason: {req.reason}",
        "severity": "critical",
        "timestamp": time.time(),
    })

    # Broadcast override event
    await _ws_broadcast("audit_entry", entry)
    await _ws_broadcast("crisis_timeline_update", {
        "event": "HUMAN_OVERRIDE",
        "label": f"Override: {req.action}",
        "timestamp": time.time(),
    })

    return {"status": "executed", "action": req.action, "audit_hash": entry["hash"]}


@router.post("/{agent_id}/pause")
async def pause_agent(agent_id: str, req: OverrideRequest):
    """Pause a specific agent."""
    if agent_id not in _agents:
        raise HTTPException(404, f"Agent {agent_id} not found")

    _agents[agent_id].pause()

    entry = _audit_chain.log_decision(
        agent="HUMAN_OPERATOR",
        action=f"pause_agent:{agent_id}",
        reasoning=f"Paused {agent_id}. {req.reason}",
        cdil_state=await _cdil.get_snapshot(),
    )

    await _ws_broadcast("agent_status_update", {
        "agent": agent_id,
        "status": "PAUSED",
        "timestamp": time.time(),
    })
    await _ws_broadcast("audit_entry", entry)

    return {"status": "paused", "agent": agent_id}


@router.post("/{agent_id}/resume")
async def resume_agent(agent_id: str, req: OverrideRequest):
    """Resume a specific agent."""
    if agent_id not in _agents:
        raise HTTPException(404, f"Agent {agent_id} not found")

    _agents[agent_id].resume()

    entry = _audit_chain.log_decision(
        agent="HUMAN_OPERATOR",
        action=f"resume_agent:{agent_id}",
        reasoning=f"Resumed {agent_id}. {req.reason}",
        cdil_state=await _cdil.get_snapshot(),
    )

    await _ws_broadcast("agent_status_update", {
        "agent": agent_id,
        "status": "ACTIVE",
        "timestamp": time.time(),
    })
    await _ws_broadcast("audit_entry", entry)

    return {"status": "resumed", "agent": agent_id}
