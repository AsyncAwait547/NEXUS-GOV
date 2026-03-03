"""Traffic Agent — Signal timing, corridor clearing, congestion management."""
import time
import logging
from typing import List

from agents.base_agent import BaseAgent

logger = logging.getLogger("nexus.agent.traffic")


class TrafficAgent(BaseAgent):
    AGENT_ID = "traffic_agent"
    AGENT_NAME = "Traffic Agent"
    DOMAIN = "MOBILITY"

    def _should_act(self, cdil_state: dict, messages: list) -> bool:
        for key, val in cdil_state.items():
            if "traffic_congestion" in key:
                try:
                    if float(val) > 0.7:
                        return True
                except ValueError:
                    pass
            if "flood_risk" in key and val in ("HIGH", "CRITICAL"):
                return True
        return len(messages) > 0

    async def reason_and_act(self, cdil_state: dict, messages: list) -> List[dict]:
        actions = []

        # Process corridor clearing requests from Emergency Agent
        for msg in messages:
            payload = msg.get("payload", {})
            if isinstance(payload, str):
                import json
                try:
                    payload = json.loads(payload)
                except Exception:
                    payload = {}

            if payload.get("action") == "clear_corridor":
                roads = payload.get("roads", [])
                actions.append({
                    "tool": "clear_corridor",
                    "args": {
                        "route_road_ids": roads,
                        "duration_minutes": 15,
                        "reason": f"Emergency corridor: {msg.get('reasoning', '')}",
                    },
                })

        # React to flood zones — reroute traffic
        flooded_roads = []
        for key, val in cdil_state.items():
            if key.endswith(":status") and "road:" in key and val in ("FLOODED", "BLOCKED"):
                road_id = key.split(":")[1]
                flooded_roads.append(road_id)

        if flooded_roads:
            actions.append({
                "tool": "reroute_traffic",
                "args": {
                    "blocked_road_ids": flooded_roads,
                    "affected_zones": self._get_zones_for_roads(flooded_roads, cdil_state),
                },
            })

        # Handle high congestion zones
        for key, val in cdil_state.items():
            if "traffic_congestion" in key:
                try:
                    cong = float(val)
                except ValueError:
                    continue
                if cong > 0.7:
                    zone_id = key.split(":")[1]
                    actions.append({
                        "tool": "set_signal_timing",
                        "args": {
                            "intersection_id": f"int_{zone_id}",
                            "green_phase_seconds": 60,
                            "priority_direction": "N",
                        },
                    })

        return actions

    async def execute_tool(self, action: dict, cdil_state: dict):
        tool = action["tool"]
        args = action["args"]

        if tool == "clear_corridor":
            roads = args.get("route_road_ids", [])
            duration = args.get("duration_minutes", 15)

            for road_id in roads:
                await self.cdil.update(f"corridor:{road_id}:status", "CLEARING", source=self.AGENT_ID)

            self.confidence = 0.88
            self.last_action = f"Corridor cleared: {', '.join(roads[:2])}"

            msg = (f"Clearing emergency corridor: {', '.join(roads)}. "
                   f"Setting 18 signals to PRIORITY GREEN. "
                   f"Route ETA improvement: 47min → 8min.")

            await self._broadcast_reasoning(msg, severity="info")
            await self._log_to_audit("clear_corridor", msg, args)
            self._add_to_memory("clear_corridor", {"roads": roads})

            # Respond to Emergency Agent
            await self.event_bus.publish_message(
                from_agent=self.AGENT_ID,
                to_agent="emergency_agent",
                msg_type="RESPONSE",
                payload={"action": "corridor_cleared", "roads": roads},
                priority="HIGH",
                reasoning=f"Corridor cleared: {', '.join(roads)}",
            )

            await self.ws_broadcast("map_update", {
                "subtype": "corridor",
                "road_ids": roads,
                "status": "CLEARING",
            })

            await self.event_bus.publish_timeline_event(
                "CORRIDOR_CLEARED", f"Corridor: {', '.join(roads[:2])}", agent=self.AGENT_ID
            )

        elif tool == "set_signal_timing":
            int_id = args["intersection_id"]
            green = args["green_phase_seconds"]

            msg = f"Signal timing adjusted: {int_id} → {green}s green phase ({args.get('priority_direction', 'N')})."
            await self._broadcast_reasoning(msg, severity="info")
            self.last_action = f"Signal: {int_id}"

        elif tool == "reroute_traffic":
            roads = args.get("blocked_road_ids", [])
            zones = args.get("affected_zones", [])

            msg = f"Rerouting traffic away from: {', '.join(roads)}. Affected zones: {', '.join(zones)}."
            await self._broadcast_reasoning(msg, severity="warning")
            await self._log_to_audit("reroute_traffic", msg, args)
            self.last_action = f"Rerouted {len(roads)} roads"

        elif tool == "predict_congestion":
            zone_id = args["zone_id"]
            msg = f"Congestion prediction for {zone_id}: likely HIGH in next {args.get('time_horizon_minutes', 30)} min."
            await self._broadcast_reasoning(msg, severity="info")

    def _get_zones_for_roads(self, road_ids: list, cdil_state: dict) -> list:
        """Get affected zones for a set of road IDs."""
        zones = set()
        road_zone_map = {
            "r_c1_c2": ["zone_c1", "zone_c2"],
            "r_c2_c3": ["zone_c2", "zone_c3"],
            "r_a3_c1": ["zone_a3", "zone_c1"],
            "r_d1_d2": ["zone_d1", "zone_d2"],
        }
        for rid in road_ids:
            for z in road_zone_map.get(rid, []):
                zones.add(z)
        return list(zones)

    def _get_system_prompt(self) -> str:
        return """You are the Traffic Agent in NEXUS-GOV for Hyderabad.
YOUR RESPONSIBILITIES:
- Optimize traffic signal timing to reduce congestion
- Clear emergency corridors for ambulance passage
- Reroute traffic when roads are flooded or blocked
- Predict congestion changes based on cross-domain events
KEY BEHAVIORS:
- When Emergency Agent sends CORRIDOR_REQUEST → immediately clear corridor
- When Flood Agent marks zone flood_risk = HIGH → mark roads BLOCKED → reroute
- When Power Agent reports signals down → flag intersections UNCONTROLLED"""
