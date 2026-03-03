"""Base Agent — Shared pattern for all domain agents."""
import asyncio
import json
import time
import logging
from abc import abstractmethod
from typing import Any, Callable, Dict, List, Optional

from config import settings

logger = logging.getLogger("nexus.agent")


class BaseAgent:
    """
    Abstract base agent implementing Perceive → Reason → Act cycle.
    All domain agents inherit from this.
    """

    AGENT_ID: str = "base"
    AGENT_NAME: str = "Base Agent"
    DOMAIN: str = "base"

    def __init__(self, cdil, event_bus, audit_chain, causal_engine, ws_broadcast: Callable):
        self.cdil = cdil
        self.event_bus = event_bus
        self.audit = audit_chain
        self.causal = causal_engine
        self.ws_broadcast = ws_broadcast

        self.status = "ACTIVE"
        self.confidence = 0.5
        self.last_action = "Initializing"
        self.episodic_memory: List[dict] = []
        self.action_count = 0
        self._paused = False
        self._running = False

        # LLM model (loaded on first use)
        self._model = None
        self._chat = None

    # ── Agent Lifecycle ──

    async def start(self):
        """Start the agent's perception-reasoning-action loop."""
        self._running = True
        logger.info(f"[{self.AGENT_ID}] Agent started")

        while self._running:
            try:
                if not self._paused:
                    await self.run_cycle()
                await asyncio.sleep(settings.AGENT_CYCLE_INTERVAL)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[{self.AGENT_ID}] Cycle error: {e}")
                self.status = "ERROR"
                await self._broadcast_status()
                await asyncio.sleep(5)  # Back off on error

    async def stop(self):
        """Gracefully stop the agent."""
        self._running = False
        logger.info(f"[{self.AGENT_ID}] Agent stopped")

    def pause(self):
        """Pause the agent (human override)."""
        self._paused = True
        self.status = "PAUSED"
        logger.info(f"[{self.AGENT_ID}] Agent paused")

    def resume(self):
        """Resume the agent."""
        self._paused = False
        self.status = "ACTIVE"
        logger.info(f"[{self.AGENT_ID}] Agent resumed")

    # ── Core Loop ──

    async def run_cycle(self):
        """One perception → reasoning → action cycle."""
        # 1. Perceive
        cdil_state, messages = await self.perceive()

        # 2. Check if action is needed
        if not self._should_act(cdil_state, messages):
            return

        # 3. Reason and act
        self.status = "REASONING"
        await self._broadcast_status()

        try:
            actions = await self.reason_and_act(cdil_state, messages)
            if actions:
                for action in actions:
                    await self.execute_tool(action, cdil_state)
                    self.action_count += 1

                self.status = "ALERT" if self.confidence > 0.7 else "ACTIVE"
            else:
                self.status = "ACTIVE"
        except Exception as e:
            logger.error(f"[{self.AGENT_ID}] Reasoning error: {e}")
            self.status = "ERROR"

        await self._broadcast_status()

    async def perceive(self):
        """Read CDIL state + pending messages."""
        cdil_state = await self.cdil.get_snapshot()
        messages = await self.event_bus.consume_messages(self.AGENT_ID)
        return cdil_state, messages

    @abstractmethod
    def _should_act(self, cdil_state: dict, messages: list) -> bool:
        """Determine if the agent should reason on this cycle."""
        return len(messages) > 0

    @abstractmethod
    async def reason_and_act(self, cdil_state: dict, messages: list) -> List[dict]:
        """
        Core reasoning method. Returns list of tool call dicts:
        [{"tool": "tool_name", "args": {...}}]
        """
        pass

    @abstractmethod
    async def execute_tool(self, action: dict, cdil_state: dict):
        """Execute a single tool action."""
        pass

    # ── LLM Integration ──

    async def _call_llm(self, prompt: str) -> Optional[dict]:
        """Call Gemini 2.0 Flash for reasoning. Falls back to mock in demo mode."""
        if settings.MOCK_LLM:
            return self._mock_llm_response(prompt)

        try:
            return await self._call_gemini(prompt)
        except Exception as e:
            logger.warning(f"[{self.AGENT_ID}] Gemini failed: {e}, trying Groq fallback")
            try:
                return await self._call_groq(prompt)
            except Exception as e2:
                logger.error(f"[{self.AGENT_ID}] All LLM calls failed: {e2}")
                self.status = "ERROR"
                await self._request_human_override(
                    reason=f"LLM reasoning failed: {e2}"
                )
                return None

    async def _call_gemini(self, prompt: str) -> dict:
        """Call Gemini 2.0 Flash API."""
        import google.generativeai as genai

        if not self._model:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel(
                model_name="gemini-2.0-flash-exp",
                system_instruction=self._get_system_prompt(),
            )

        response = await asyncio.wait_for(
            asyncio.to_thread(self._model.generate_content, prompt),
            timeout=settings.LLM_TIMEOUT,
        )

        # Parse JSON from response
        text = response.text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            if "```json" in text:
                json_str = text.split("```json")[1].split("```")[0].strip()
                return json.loads(json_str)
            elif "```" in text:
                json_str = text.split("```")[1].split("```")[0].strip()
                return json.loads(json_str)
            return {"reasoning": text, "actions": []}

    async def _call_groq(self, prompt: str) -> dict:
        """Fallback to Groq (Llama 3.3)."""
        from groq import AsyncGroq

        client = AsyncGroq(api_key=settings.GROQ_API_KEY)
        response = await asyncio.wait_for(
            client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            ),
            timeout=settings.LLM_TIMEOUT,
        )
        return json.loads(response.choices[0].message.content)

    def _mock_llm_response(self, prompt: str) -> dict:
        """Deterministic mock response for demo mode."""
        return {"reasoning": "Mock LLM — demo mode active", "actions": []}

    @abstractmethod
    def _get_system_prompt(self) -> str:
        """Agent-specific system prompt."""
        pass

    # ── Helpers ──

    async def _broadcast_status(self):
        """Broadcast agent status via WebSocket."""
        await self.ws_broadcast("agent_status_update", {
            "agent": self.AGENT_ID,
            "name": self.AGENT_NAME,
            "domain": self.DOMAIN,
            "status": self.status,
            "confidence": self.confidence,
            "last_action": self.last_action,
            "action_count": self.action_count,
            "timestamp": time.time(),
        })

    async def _broadcast_reasoning(self, message: str, severity: str = "info",
                                    target: str = None):
        """Broadcast reasoning log entry."""
        await self.ws_broadcast("reasoning_log", {
            "agent": self.AGENT_ID,
            "badge": self._get_badge(),
            "message": message,
            "severity": severity,
            "target": target,
            "timestamp": time.time(),
        })

    async def _log_to_audit(self, action: str, reasoning: str,
                             parameters: dict = None):
        """Log decision to audit chain + broadcast."""
        cdil_state = await self.cdil.get_snapshot()
        entry = self.audit.log_decision(
            agent=self.AGENT_ID,
            action=action,
            reasoning=reasoning,
            cdil_state=cdil_state,
            parameters=parameters,
        )
        await self.ws_broadcast("audit_entry", entry)
        await self.cdil.increment("system:decision_count")

    async def _request_human_override(self, reason: str):
        """Request human override when confidence is low or LLM failed."""
        await self.ws_broadcast("reasoning_log", {
            "agent": self.AGENT_ID,
            "badge": self._get_badge(),
            "message": f"⚠ REQUESTING HUMAN OVERRIDE: {reason}",
            "severity": "critical",
            "timestamp": time.time(),
        })

    def _add_to_memory(self, action: str, result: Any):
        """Add event to episodic memory (last 10)."""
        self.episodic_memory.append({
            "action": action,
            "result": result,
            "timestamp": time.time(),
        })
        if len(self.episodic_memory) > 10:
            self.episodic_memory.pop(0)

    def _get_badge(self) -> str:
        """Get agent badge for UI display."""
        badges = {
            "flood_agent": "FLD",
            "emergency_agent": "EMG",
            "traffic_agent": "TRF",
            "power_agent": "PWR",
            "meta_orchestrator": "META",
        }
        return badges.get(self.AGENT_ID, "SYS")

    def get_status(self) -> dict:
        """Get agent status for API."""
        return {
            "agent_id": self.AGENT_ID,
            "name": self.AGENT_NAME,
            "domain": self.DOMAIN,
            "status": self.status,
            "confidence": self.confidence,
            "last_action": self.last_action,
            "action_count": self.action_count,
            "paused": self._paused,
            "memory_size": len(self.episodic_memory),
        }
