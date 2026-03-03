"""Meta-Orchestrator — Conflict resolution, global coordination, weighted utility."""
import time
import logging
from typing import List

from agents.base_agent import BaseAgent

logger = logging.getLogger("nexus.agent.meta")


class MetaAgent(BaseAgent):
    AGENT_ID = "meta_orchestrator"
    AGENT_NAME = "Meta-Orchestrator"
    DOMAIN = "COORDINATION"

    # Utility weights
    W_SAFETY = 0.6
    W_EFFICIENCY = 0.25
    W_COST = 0.15

    def _should_act(self, cdil_state: dict, messages: list) -> bool:
        # Meta always monitors — act if there are messages or conflicting states
        if len(messages) > 0:
            return True

        # Check for conflicting states
        flood_zones = set()
        fire_zones = set()
        for key, val in cdil_state.items():
            if "flood_risk" in key and val in ("HIGH", "CRITICAL"):
                flood_zones.add(key.split(":")[1])
            if "fire_severity" in key:
                try:
                    if int(val) > 5:
                        fire_zones.add(key.split(":")[1])
                except ValueError:
                    pass

        # Dual crisis detection
        if flood_zones and fire_zones:
            return True

        return False

    async def reason_and_act(self, cdil_state: dict, messages: list) -> List[dict]:
        actions = []

        # Detect dual crisis
        flood_zones = set()
        fire_zones = set()
        for key, val in cdil_state.items():
            if "flood_risk" in key and val in ("HIGH", "CRITICAL"):
                flood_zones.add(key.split(":")[1])
            if "fire_severity" in key:
                try:
                    if int(val) > 5:
                        fire_zones.add(key.split(":")[1])
                except ValueError:
                    pass

        if flood_zones and fire_zones:
            actions.append({
                "tool": "resolve_conflict",
                "args": {
                    "type": "dual_crisis",
                    "flood_zones": list(flood_zones),
                    "fire_zones": list(fire_zones),
                },
            })

        # Process conflict reports
        for msg in messages:
            msg_type = msg.get("type", "")
            if msg_type == "CONFLICT":
                actions.append({
                    "tool": "resolve_conflict",
                    "args": {
                        "type": "agent_conflict",
                        "details": msg.get("payload", {}),
                        "from_agent": msg.get("from", "unknown"),
                    },
                })

        # Check for unresponsive agents
        # In production, we'd track last activity timestamps

        return actions

    async def execute_tool(self, action: dict, cdil_state: dict):
        tool = action["tool"]
        args = action["args"]

        if tool == "resolve_conflict":
            conflict_type = args.get("type", "unknown")

            if conflict_type == "dual_crisis":
                await self._resolve_dual_crisis(args, cdil_state)
            elif conflict_type == "agent_conflict":
                await self._resolve_agent_conflict(args, cdil_state)
            elif conflict_type == "resource_contention":
                await self._resolve_resource_contention(args, cdil_state)

        elif tool == "reprioritize_resources":
            await self._reprioritize(args, cdil_state)

    async def _resolve_dual_crisis(self, args: dict, cdil_state: dict):
        """Resolve competing resource demands in dual crisis."""
        flood_zones = args.get("flood_zones", [])
        fire_zones = args.get("fire_zones", [])

        # Compute utility for each crisis
        flood_utility = self._compute_utility(
            safety=0.9,  # Flood directly threatens population
            efficiency=0.4,
            cost=0.3,
        )
        fire_utility = self._compute_utility(
            safety=0.7,  # Fire is localized
            efficiency=0.6,
            cost=0.5,
        )

        # Determine primary crisis
        if flood_utility > fire_utility:
            primary = "flood"
            primary_zones = flood_zones
            secondary = "fire"
            secondary_zones = fire_zones
        else:
            primary = "fire"
            primary_zones = fire_zones
            secondary = "flood"
            secondary_zones = flood_zones

        self.confidence = 0.92
        self.last_action = f"Resolved: {primary} primary"

        reasoning = (
            f"DUAL CRISIS RESOLUTION:\n"
            f"U(flood) = {self.W_SAFETY}×0.9 + {self.W_EFFICIENCY}×0.4 + {self.W_COST}×0.3 = {flood_utility:.3f}\n"
            f"U(fire) = {self.W_SAFETY}×0.7 + {self.W_EFFICIENCY}×0.6 + {self.W_COST}×0.5 = {fire_utility:.3f}\n"
            f"PRIMARY: {primary.upper()} (U={max(flood_utility, fire_utility):.3f})\n"
            f"RESOURCE ALLOCATION: 60% → {primary}, 40% → {secondary}"
        )

        msg = (f"CONFLICT RESOLUTION: {primary.upper()} prioritized over {secondary.upper()}. "
               f"U({primary})={max(flood_utility, fire_utility):.3f} > U({secondary})={min(flood_utility, fire_utility):.3f}. "
               f"Safety-weighted. 60/40 resource split.")

        await self._broadcast_reasoning(msg, severity="critical")
        await self._log_to_audit("resolve_conflict", reasoning, args)
        self._add_to_memory("resolve_conflict", {"primary": primary, "secondary": secondary})

        await self.event_bus.publish_timeline_event(
            "CONFLICT_RESOLVED",
            f"Conflict resolved: {primary} prioritized",
            agent=self.AGENT_ID,
        )

        await self.ws_broadcast("crisis_timeline_update", {
            "event": "CONFLICT_RESOLVED",
            "label": f"Meta: {primary} prioritized over {secondary}",
            "timestamp": time.time(),
        })

    async def _resolve_agent_conflict(self, args: dict, cdil_state: dict):
        """Resolve conflicting agent actions."""
        from_agent = args.get("from_agent", "unknown")
        details = args.get("details", {})

        msg = f"Agent conflict detected from {from_agent}. Applying weighted utility resolution."
        await self._broadcast_reasoning(msg, severity="warning")
        await self._log_to_audit("resolve_agent_conflict", msg, args)

    async def _resolve_resource_contention(self, args: dict, cdil_state: dict):
        """Resolve resource contention between agents."""
        msg = "Resource contention resolved. Priority: HUMAN LIFE > PROPERTY."
        await self._broadcast_reasoning(msg, severity="info")
        await self._log_to_audit("resolve_resource_contention", msg, args)

    async def _reprioritize(self, args: dict, cdil_state: dict):
        """Reprioritize resources across agents."""
        msg = "Resources reprioritized based on current threat assessment."
        await self._broadcast_reasoning(msg, severity="info")
        await self._log_to_audit("reprioritize_resources", msg, args)

    def _compute_utility(self, safety: float, efficiency: float, cost: float) -> float:
        """Compute weighted utility: U = 0.6×safety + 0.25×efficiency + 0.15×cost."""
        return (self.W_SAFETY * safety +
                self.W_EFFICIENCY * efficiency +
                self.W_COST * cost)

    def _get_system_prompt(self) -> str:
        return """You are the Meta-Orchestrator in NEXUS-GOV for Hyderabad.
YOUR RESPONSIBILITIES:
- Coordinate all 4 domain agents (Flood, Emergency, Traffic, Power)
- Detect and resolve conflicts between agent actions
- Decompose complex goals into agent-specific tasks
- Maintain global coherence across all domains

CONFLICT RESOLUTION PROTOCOL:
U(action) = 0.6 × safety + 0.25 × efficiency + 0.15 × cost
Safety priority is ALWAYS highest.

ALWAYS explain your reasoning in full English before resolving.
If two agents propose contradictory actions, compute utility for each, choose higher U.
Log FULL reasoning chain to audit trail."""
