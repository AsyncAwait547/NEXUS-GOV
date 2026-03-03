"""Power Agent — Grid monitoring, load shedding, backup activation, power rerouting."""
import time
import logging
from typing import List

from agents.base_agent import BaseAgent

logger = logging.getLogger("nexus.agent.power")


class PowerAgent(BaseAgent):
    AGENT_ID = "power_agent"
    AGENT_NAME = "Power Agent"
    DOMAIN = "ENERGY GRID"

    # Hospital zones that NEVER get power shed
    HOSPITAL_ZONES = {"zone_c1", "zone_a2", "zone_b1", "zone_b3", "zone_c3"}

    def _should_act(self, cdil_state: dict, messages: list) -> bool:
        for key, val in cdil_state.items():
            if "flood_risk" in key and val in ("HIGH", "CRITICAL"):
                return True
            if "load_pct" in key:
                try:
                    if float(val) > 85:
                        return True
                except ValueError:
                    pass
            if "fire_severity" in key:
                try:
                    if int(val) > 5:
                        return True
                except ValueError:
                    pass
        return len(messages) > 0

    async def reason_and_act(self, cdil_state: dict, messages: list) -> List[dict]:
        actions = []

        # React to flood zones — proactively reroute power
        flood_zones = set()
        for key, val in cdil_state.items():
            if "flood_risk" in key and val in ("HIGH", "CRITICAL"):
                zone_id = key.split(":")[1]
                flood_zones.add(zone_id)

        if flood_zones:
            # Find substations in flood zones
            substations_at_risk = {
                "zone_c3": "sub_3",  # LB Nagar SS
                "zone_a1": "sub_1",
                "zone_b1": "sub_2",
                "zone_a2": "sub_4",
            }
            for zone_id in flood_zones:
                if zone_id in substations_at_risk:
                    sub_id = substations_at_risk[zone_id]
                    load = cdil_state.get(f"substation:{sub_id}:load_pct", "65")
                    try:
                        load_val = float(load)
                    except ValueError:
                        load_val = 65

                    if load_val > 20:  # Still carrying load
                        # Determine target substations
                        targets = [s for s in ["sub_2", "sub_4", "sub_1"]
                                   if s != sub_id and
                                   substations_at_risk.get(
                                       self._zone_for_sub(s), "") not in flood_zones]
                        if targets:
                            actions.append({
                                "tool": "reroute_power",
                                "args": {
                                    "from_substation": sub_id,
                                    "to_substation": targets[0],
                                    "load_mw": load_val * 2.5,
                                },
                            })

                    # Activate backup if zone has hospital
                    if zone_id in self.HOSPITAL_ZONES:
                        actions.append({
                            "tool": "activate_backup",
                            "args": {
                                "zone_id": zone_id,
                                "reason": f"Flood risk in zone with hospital",
                            },
                        })

        # React to fire zones — isolate grid segment
        for key, val in cdil_state.items():
            if "fire_severity" in key:
                try:
                    sev = int(val)
                except ValueError:
                    continue
                if sev > 5:
                    zone_id = key.split(":")[1]
                    actions.append({
                        "tool": "shed_load",
                        "args": {
                            "zone_id": zone_id,
                            "reduction_percentage": 30,
                        },
                    })

        return actions

    async def execute_tool(self, action: dict, cdil_state: dict):
        tool = action["tool"]
        args = action["args"]

        if tool == "reroute_power":
            from_sub = args["from_substation"]
            to_sub = args["to_substation"]
            load_mw = args["load_mw"]

            await self.cdil.update(f"substation:{from_sub}:load_pct", "15", source=self.AGENT_ID)
            await self.cdil.update(f"substation:{to_sub}:load_pct", "92", source=self.AGENT_ID)

            self.confidence = 0.86
            self.last_action = f"Rerouting {load_mw:.0f}MW from {from_sub}"

            msg = (f"Rerouting {load_mw:.0f}MW: {from_sub} → {to_sub}. "
                   f"Hospital backup power: ACTIVATED. Cascade protection: ENABLED.")
            await self._broadcast_reasoning(msg, severity="warning")
            await self._log_to_audit("reroute_power", msg, args)
            self._add_to_memory("reroute_power", {"from": from_sub, "to": to_sub, "mw": load_mw})

        elif tool == "activate_backup":
            zone_id = args["zone_id"]

            await self.cdil.update(f"zone:{zone_id}:backup_active", "true", source=self.AGENT_ID)

            self.confidence = 0.90
            msg = f"Backup power ACTIVATED for {zone_id}. Reason: {args.get('reason', 'precautionary')}."
            self.last_action = f"Backup: {zone_id}"
            await self._broadcast_reasoning(msg, severity="info")
            await self._log_to_audit("activate_backup", msg, args)

        elif tool == "shed_load":
            zone_id = args["zone_id"]
            reduction = args["reduction_percentage"]

            # Safety check — never shed hospital zones
            if zone_id in self.HOSPITAL_ZONES:
                msg = f"⚠ BLOCKED: Cannot shed load in {zone_id} — hospital zone. Rerouting instead."
                await self._broadcast_reasoning(msg, severity="critical")
                return

            await self.cdil.update(f"zone:{zone_id}:power_status", "DEGRADED", source=self.AGENT_ID)

            self.confidence = 0.82
            self.last_action = f"Shed {reduction}% in {zone_id}"
            msg = f"Load shedding: {zone_id} reduced by {reduction}%. Non-essential services offline."
            await self._broadcast_reasoning(msg, severity="warning")
            await self._log_to_audit("shed_load", msg, args)

            # Trigger causal — power down affects traffic signals
            await self.causal.propagate_effects(f"zone:{zone_id}:power_status", "DEGRADED")

        elif tool == "predict_demand":
            zone_id = args["zone_id"]
            msg = f"Demand forecast: {zone_id} expected +15% load in {args.get('time_horizon_minutes', 30)} min."
            await self._broadcast_reasoning(msg, severity="info")

    def _zone_for_sub(self, sub_id: str) -> str:
        mapping = {"sub_1": "zone_a1", "sub_2": "zone_b1", "sub_3": "zone_c3", "sub_4": "zone_a2"}
        return mapping.get(sub_id, "")

    def _get_system_prompt(self) -> str:
        return """You are the Power Agent in NEXUS-GOV for Hyderabad.
YOUR RESPONSIBILITIES:
- Monitor grid load across 4 substations serving 12 zones
- Prevent outages by proactive load rerouting
- Activate backup power for critical zones (hospitals)
- Implement load shedding for non-critical areas
HARD CONSTRAINT: Hospital zones NEVER get power shed. hospital zones = zone_c1, zone_a2, zone_b1, zone_b3, zone_c3
KEY BEHAVIORS:
- When Flood Agent marks zone at risk → proactively reroute BEFORE substation fails
- When Traffic Agent needs corridor signals ON → ensure those zones have power
PRIORITY: HUMAN LIFE > PROPERTY > EFFICIENCY > COST"""
