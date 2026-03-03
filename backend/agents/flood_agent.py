"""Flood Agent — Rainfall monitoring, flood risk prediction, evacuation alerts."""
import time
import logging
from typing import List

from agents.base_agent import BaseAgent

logger = logging.getLogger("nexus.agent.flood")


class FloodAgent(BaseAgent):
    AGENT_ID = "flood_agent"
    AGENT_NAME = "Flood Agent"
    DOMAIN = "HYDROLOGY"

    def _should_act(self, cdil_state: dict, messages: list) -> bool:
        """Act on rainfall data or cross-domain messages."""
        # Check for rainfall sensors above threshold
        for key, val in cdil_state.items():
            if "rainfall_mm_hr" in key:
                try:
                    if float(val) > 65:
                        return True
                except ValueError:
                    pass
            if "flood_risk" in key and val in ("HIGH", "CRITICAL"):
                return True
        return len(messages) > 0

    async def reason_and_act(self, cdil_state: dict, messages: list) -> List[dict]:
        actions = []

        # Check rainfall sensors
        for key, val in cdil_state.items():
            if "rainfall_mm_hr" not in key:
                continue
            try:
                rainfall = float(val)
            except ValueError:
                continue

            zone_id = key.split(":")[1]  # sensor:zone_c2:rainfall_mm_hr → zone_c2

            if rainfall > 100:
                actions.append({
                    "tool": "assess_flood_risk",
                    "args": {"zone_id": zone_id, "current_rainfall_mm_hr": rainfall, "severity": "CRITICAL"},
                })
                actions.append({
                    "tool": "trigger_evacuation_alert",
                    "args": {"zone_id": zone_id, "severity": "CRITICAL", "estimated_water_level_m": 0.8},
                })
                actions.append({
                    "tool": "broadcast_to_all_agents",
                    "args": {
                        "event_type": "flash_flood",
                        "affected_zones": [zone_id],
                        "message": f"CRITICAL FLOOD ALERT: {zone_id}. Rainfall {rainfall}mm/hr.",
                    },
                })
            elif rainfall > 65:
                actions.append({
                    "tool": "assess_flood_risk",
                    "args": {"zone_id": zone_id, "current_rainfall_mm_hr": rainfall, "severity": "HIGH"},
                })

        # Process incoming messages
        for msg in messages:
            payload = msg.get("payload", {})
            if isinstance(payload, str):
                import json
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}

        return actions

    async def execute_tool(self, action: dict, cdil_state: dict):
        tool = action["tool"]
        args = action["args"]

        if tool == "assess_flood_risk":
            zone_id = args["zone_id"]
            severity = args.get("severity", "HIGH")
            rainfall = args.get("current_rainfall_mm_hr", 0)

            await self.cdil.update(f"zone:{zone_id}:flood_risk", severity, source=self.AGENT_ID)
            self.confidence = 0.94 if severity == "CRITICAL" else 0.85

            water_level = round(rainfall / 150, 2)
            await self.cdil.update(f"zone:{zone_id}:water_level", str(water_level), source=self.AGENT_ID)

            msg = (f"FLOOD RISK: {severity} for {zone_id}. "
                   f"Rainfall: {rainfall}mm/hr. Est. water level: {water_level}m.")
            self.last_action = f"Flood risk: {severity} for {zone_id}"
            await self._broadcast_reasoning(msg, severity="critical" if severity == "CRITICAL" else "warning")
            await self._log_to_audit("assess_flood_risk", msg, args)
            self._add_to_memory("assess_flood_risk", {"zone": zone_id, "severity": severity})

            # Trigger causal effects
            await self.causal.propagate_effects(f"zone:{zone_id}:flood_risk", severity)

        elif tool == "trigger_evacuation_alert":
            zone_id = args["zone_id"]
            severity = args["severity"]

            await self.cdil.update(f"zone:{zone_id}:evacuation_status",
                                   "EVACUATING" if severity == "CRITICAL" else "ADVISORY",
                                   source=self.AGENT_ID)

            msg = f"⚠ EVACUATION {severity}: Zone {zone_id}. Est. water: {args.get('estimated_water_level_m', 0)}m."
            await self._broadcast_reasoning(msg, severity="critical")
            await self._log_to_audit("trigger_evacuation_alert", msg, args)

            await self.event_bus.publish_timeline_event(
                "EVACUATION_ALERT", f"Evacuation alert: {zone_id}", agent=self.AGENT_ID
            )

        elif tool == "broadcast_to_all_agents":
            affected = args.get("affected_zones", [])
            msg = args.get("message", "")

            await self.event_bus.publish_message(
                from_agent=self.AGENT_ID,
                to_agent="ALL",
                msg_type="ALERT",
                payload=args,
                priority="CRITICAL",
                reasoning=msg,
            )

            await self._broadcast_reasoning(
                f"→ [BROADCAST TO ALL AGENTS] {msg}",
                severity="critical",
                target="ALL",
            )

        elif tool == "predict_water_level":
            zone_id = args["zone_id"]
            # Simple prediction based on rainfall
            rainfall = float(cdil_state.get(f"sensor:{zone_id}:rainfall_mm_hr", 0))
            predicted = round(rainfall / 120 * args.get("hours_ahead", 2), 2)

            await self._broadcast_reasoning(
                f"Predicted water level for {zone_id} in {args.get('hours_ahead', 2)}hrs: {predicted}m",
                severity="info"
            )

    def _get_system_prompt(self) -> str:
        return """You are the Flood Agent in NEXUS-GOV for Hyderabad, India.
YOUR RESPONSIBILITIES:
- Monitor rainfall sensors across 12 city zones
- Predict flood risk based on rainfall intensity, terrain, drainage capacity
- Issue evacuation alerts when water levels threaten safety
- Broadcast critical alerts to ALL other agents for cross-domain cascading

TRIGGER THRESHOLDS:
- Rainfall > 65mm/hr sustained 1+ hours → flood_risk = HIGH
- Rainfall > 100mm/hr OR water level > 0.5m → flood_risk = CRITICAL
- On CRITICAL → auto-broadcast to ALL agents

PRIORITY: HUMAN LIFE > PROPERTY > EFFICIENCY > COST
If confidence < 0.6, request human override."""

    async def _broadcast_status(self):
        await super()._broadcast_status()
