"""Scenario Injection Engine — Drives demo crisis sequences through CDIL."""
import asyncio
import logging
import time
from typing import Callable, Optional

from data.scenarios import SCENARIOS

logger = logging.getLogger("nexus.scenario")


class ScenarioEngine:
    """Orchestrates scenario injection via CDIL updates and event bus."""

    def __init__(self, cdil, event_bus, audit_chain, ws_broadcast: Callable):
        self.cdil = cdil
        self.event_bus = event_bus
        self.audit = audit_chain
        self.ws_broadcast = ws_broadcast
        self._active_scenario: Optional[str] = None
        self._tasks: list = []

    @property
    def active_scenario(self) -> Optional[str]:
        return self._active_scenario

    async def inject_scenario(self, scenario_name: str) -> dict:
        """Inject a crisis scenario. Returns scenario metadata."""
        if scenario_name not in SCENARIOS:
            return {"error": f"Unknown scenario: {scenario_name}"}

        if self._active_scenario:
            return {"error": f"Scenario already active: {self._active_scenario}"}

        scenario = SCENARIOS[scenario_name]
        self._active_scenario = scenario_name

        await self.cdil.update("system:active_scenario", scenario_name, source="scenario_engine")
        logger.info(f"[Scenario] Injecting: {scenario['name']}")

        # Broadcast scenario start
        await self.ws_broadcast("threat_level_update", {
            "scenario": scenario_name,
            "name": scenario["name"],
            "description": scenario["description"],
            "status": "STARTED",
        })

        await self.event_bus.publish_timeline_event(
            event_type="SCENARIO_START",
            label=f"Scenario: {scenario['name']}",
            agent="scenario_engine",
        )

        # Schedule timeline steps
        task = asyncio.create_task(self._run_timeline(scenario_name, scenario["timeline"]))
        self._tasks.append(task)

        return {
            "scenario": scenario_name,
            "name": scenario["name"],
            "steps": len(scenario["timeline"]),
            "status": "injected",
        }

    async def _run_timeline(self, scenario_name: str, timeline: list):
        """Execute scenario timeline with delays."""
        start_time = time.time()

        for step in timeline:
            delay = step["delay_sec"]
            elapsed = time.time() - start_time
            wait = max(0, delay - elapsed)
            if wait > 0:
                await asyncio.sleep(wait)

            if self._active_scenario != scenario_name:
                break  # Scenario was reset

            # Apply CDIL updates
            updates = step.get("updates", {})
            if updates:
                changes = await self.cdil.batch_update(updates, source="scenario_engine")

                # Broadcast each change
                for change in changes:
                    await self.ws_broadcast("cdil_update", change)

            # Update threat level if specified
            if "threat_level" in step:
                await self.cdil.update(
                    "system:threat_level", str(step["threat_level"]),
                    source="scenario_engine"
                )
                await self.ws_broadcast("threat_level_update", {
                    "level": step["threat_level"],
                    "reason": step.get("log", ""),
                })

            # Publish reasoning log
            if "log" in step:
                await self.ws_broadcast("reasoning_log", {
                    "agent": "scenario_engine",
                    "event": step.get("event", "update"),
                    "message": step["log"],
                    "timestamp": time.time(),
                    "severity": "critical" if step.get("threat_level", 0) >= 4 else "info",
                })

            # Publish timeline event
            await self.event_bus.publish_timeline_event(
                event_type=step.get("event", "UPDATE"),
                label=step.get("log", "")[:80],
                agent="scenario_engine",
            )
            await self.ws_broadcast("crisis_timeline_update", {
                "event": step.get("event"),
                "label": step.get("log", "")[:80],
                "timestamp": time.time(),
            })

            # Log to audit chain if specified
            if "audit" in step:
                audit_data = step["audit"]
                cdil_snap = await self.cdil.get_snapshot()
                self.audit.log_decision(
                    agent=audit_data["agent"],
                    action=audit_data["action"],
                    reasoning=audit_data["reasoning"],
                    cdil_state=cdil_snap,
                )
                entry = self.audit.get_recent(1)
                if entry:
                    await self.ws_broadcast("audit_entry", entry[0])

            # Broadcast if flagged
            if step.get("broadcast"):
                await self.event_bus.publish_message(
                    from_agent="scenario_engine",
                    to_agent="ALL",
                    msg_type="ALERT",
                    payload={"event": step.get("event"), "updates": updates},
                    priority="CRITICAL",
                    reasoning=step.get("log", ""),
                )

            logger.info(f"[Scenario] Step: {step.get('event')} @ +{delay}s")

        logger.info(f"[Scenario] {scenario_name} timeline complete")

    async def reset(self):
        """Reset scenario state."""
        self._active_scenario = None

        # Cancel running tasks
        for task in self._tasks:
            task.cancel()
        self._tasks.clear()

        await self.cdil.update("system:active_scenario", "none", source="system")
        await self.cdil.update("system:threat_level", "1", source="system")

        await self.ws_broadcast("threat_level_update", {"level": 1, "reason": "System reset"})
        logger.info("[Scenario] Reset complete")

    async def get_status(self) -> dict:
        return {
            "active_scenario": self._active_scenario,
            "available": list(SCENARIOS.keys()),
        }
