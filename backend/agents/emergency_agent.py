"""Emergency Agent — Ambulance dispatch, hospital alerting, resource positioning."""
import time
import logging
from typing import List

from agents.base_agent import BaseAgent

logger = logging.getLogger("nexus.agent.emergency")


class EmergencyAgent(BaseAgent):
    AGENT_ID = "emergency_agent"
    AGENT_NAME = "Emergency Agent"
    DOMAIN = "EMERGENCY MGMT"

    def _should_act(self, cdil_state: dict, messages: list) -> bool:
        for key, val in cdil_state.items():
            if "flood_risk" in key and val in ("HIGH", "CRITICAL"):
                return True
            if "fire_severity" in key:
                try:
                    if int(val) > 5:
                        return True
                except ValueError:
                    pass
        return len(messages) > 0

    async def reason_and_act(self, cdil_state: dict, messages: list) -> List[dict]:
        actions = []

        # React to flood zones — pre-position ambulances
        flood_zones = []
        for key, val in cdil_state.items():
            if "flood_risk" in key and val in ("HIGH", "CRITICAL"):
                zone_id = key.split(":")[1]
                flood_zones.append(zone_id)

        if flood_zones:
            # Find ambulances in flood zones and reposition
            for key, val in cdil_state.items():
                if "ambulance:" in key and key.endswith(":zone"):
                    amb_id = key.split(":")[1]
                    if val in flood_zones:
                        status_key = f"ambulance:{amb_id}:status"
                        if cdil_state.get(status_key) == "IDLE":
                            actions.append({
                                "tool": "pre_position_ambulance",
                                "args": {
                                    "ambulance_id": amb_id,
                                    "target_zone": "zone_a3",  # Move to safe zone
                                    "reason": f"Pre-positioning outside flood zones {flood_zones}",
                                },
                            })

            # Request corridor clearing
            actions.append({
                "tool": "request_corridor_clearing",
                "args": {
                    "route_road_ids": ["r_a3_c1", "r_a1_a3"],
                    "urgency": "CRITICAL",
                },
            })

            # Alert hospitals
            for zone in flood_zones:
                actions.append({
                    "tool": "alert_hospital",
                    "args": {
                        "hospital_id": "hosp_1",  # NIMS
                        "eta_minutes": 12,
                        "case_type": "trauma",
                        "severity": 7,
                    },
                })

        # React to fire zones
        for key, val in cdil_state.items():
            if "fire_severity" in key:
                try:
                    sev = int(val)
                except ValueError:
                    continue
                if sev > 5:
                    zone_id = key.split(":")[1]
                    actions.append({
                        "tool": "dispatch_ambulance",
                        "args": {
                            "ambulance_id": "amb_6",
                            "destination_zone": zone_id,
                            "case_type": "trauma",
                            "route_preference": "fastest",
                        },
                    })

        return actions

    async def execute_tool(self, action: dict, cdil_state: dict):
        tool = action["tool"]
        args = action["args"]

        if tool == "dispatch_ambulance":
            amb_id = args["ambulance_id"]
            dest = args["destination_zone"]

            await self.cdil.update(f"ambulance:{amb_id}:status", "DISPATCHED", source=self.AGENT_ID)
            await self.cdil.update(f"ambulance:{amb_id}:zone", dest, source=self.AGENT_ID)

            self.confidence = 0.91
            self.last_action = f"Dispatched {amb_id} → {dest}"

            msg = f"Dispatching {amb_id} to {dest}. Case: {args.get('case_type', 'general')}. Route: {args.get('route_preference', 'fastest')}."
            await self._broadcast_reasoning(msg, severity="warning")
            await self._log_to_audit("dispatch_ambulance", msg, args)
            self._add_to_memory("dispatch_ambulance", {"amb": amb_id, "dest": dest})

            await self.ws_broadcast("map_update", {
                "subtype": "ambulance_move",
                "id": amb_id,
                "zone": dest,
                "status": "DISPATCHED",
            })

        elif tool == "pre_position_ambulance":
            amb_id = args["ambulance_id"]
            target = args["target_zone"]

            await self.cdil.update(f"ambulance:{amb_id}:status", "REPOSITIONING", source=self.AGENT_ID)
            await self.cdil.update(f"ambulance:{amb_id}:zone", target, source=self.AGENT_ID)

            self.confidence = 0.88
            self.last_action = f"Pre-positioning {amb_id}"

            msg = f"Repositioning {amb_id} → {target} staging. {args.get('reason', '')}"
            await self._broadcast_reasoning(msg, severity="info")
            await self._log_to_audit("pre_position_ambulance", msg, args)

        elif tool == "alert_hospital":
            hosp_id = args["hospital_id"]
            msg = (f"Alerting {hosp_id}: incoming patient. "
                   f"ETA: {args.get('eta_minutes', 0)} min. "
                   f"Case: {args.get('case_type', 'general')}. Severity: {args.get('severity', 5)}.")
            await self._broadcast_reasoning(msg, severity="warning")
            await self._log_to_audit("alert_hospital", msg, args)

        elif tool == "request_corridor_clearing":
            roads = args.get("route_road_ids", [])
            urgency = args.get("urgency", "HIGH")

            # Send message to Traffic Agent via event bus
            await self.event_bus.publish_message(
                from_agent=self.AGENT_ID,
                to_agent="traffic_agent",
                msg_type="REQUEST",
                payload={"action": "clear_corridor", "roads": roads, "urgency": urgency},
                priority="CRITICAL",
                reasoning=f"Emergency corridor needed: {roads}",
            )

            msg = f"→ [TO TRAFFIC] Requesting corridor clearing: {', '.join(roads)}. Urgency: {urgency}."
            await self._broadcast_reasoning(msg, severity="warning", target="traffic")
            self._add_to_memory("request_corridor", {"roads": roads})

    def _get_system_prompt(self) -> str:
        return """You are the Emergency Agent in NEXUS-GOV for Hyderabad.
YOUR RESPONSIBILITIES:
- Dispatch ambulances based on emergency calls and crisis zones
- Pre-position ambulances OUTSIDE flood zones for rapid response
- Alert hospitals about incoming patients with ETA and severity
- Request corridor clearing from Traffic Agent BEFORE dispatching
CRITICAL PROTOCOL: Always request_corridor_clearing() → wait → then dispatch_ambulance()
PRIORITY: HUMAN LIFE > PROPERTY > EFFICIENCY > COST"""
