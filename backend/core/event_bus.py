"""Event Bus — Redis Streams based inter-agent messaging."""
import json
import time
import uuid
import logging
from typing import Any, Dict, List, Optional
import redis.asyncio as aioredis

logger = logging.getLogger("nexus.eventbus")


class EventBus:
    """Redis Streams event bus for agent-to-agent communication."""

    BROADCAST_STREAM = "nexus:broadcast"
    CONFLICT_STREAM = "nexus:conflicts"
    TIMELINE_STREAM = "nexus:timeline"

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    def _agent_stream(self, agent_id: str) -> str:
        return f"nexus:agent:{agent_id}"

    async def initialize(self):
        """Create consumer groups for all streams."""
        streams = [self.BROADCAST_STREAM, self.CONFLICT_STREAM, self.TIMELINE_STREAM]
        for stream in streams:
            try:
                await self.redis.xgroup_create(stream, "nexus-group", id="0", mkstream=True)
            except Exception:
                pass  # Group already exists

    async def publish_message(
        self,
        from_agent: str,
        to_agent: str,  # agent_id or "ALL"
        msg_type: str,  # ALERT | REQUEST | RESPONSE | OVERRIDE | CONFLICT | STATUS
        payload: dict,
        priority: str = "MEDIUM",
        reasoning: str = "",
    ) -> str:
        """Publish a message to the event bus."""
        msg_id = str(uuid.uuid4())[:8]
        message = {
            "id": msg_id,
            "timestamp": time.time(),
            "from": from_agent,
            "to": to_agent,
            "type": msg_type,
            "priority": priority,
            "payload": json.dumps(payload),
            "reasoning": reasoning,
        }

        # Route to target stream
        if to_agent == "ALL":
            await self.redis.xadd(self.BROADCAST_STREAM, message)
        elif msg_type == "CONFLICT":
            await self.redis.xadd(self.CONFLICT_STREAM, message)
        else:
            target_stream = self._agent_stream(to_agent)
            await self.redis.xadd(target_stream, message)

        logger.info(f"[EventBus] {from_agent} → {to_agent}: {msg_type} ({priority})")
        return msg_id

    async def consume_messages(self, agent_id: str, count: int = 10) -> List[dict]:
        """Consume pending messages for an agent."""
        messages = []

        # Read from agent-specific stream
        agent_stream = self._agent_stream(agent_id)
        try:
            raw = await self.redis.xread({agent_stream: "0"}, count=count)
            for stream_name, stream_msgs in raw:
                for msg_id, msg_data in stream_msgs:
                    parsed = self._parse_message(msg_data)
                    parsed["_stream_id"] = msg_id
                    messages.append(parsed)
                    # Acknowledge
                    await self.redis.xdel(agent_stream, msg_id)
        except Exception:
            pass

        # Read from broadcast stream
        try:
            raw = await self.redis.xread({self.BROADCAST_STREAM: "0"}, count=count)
            for stream_name, stream_msgs in raw:
                for msg_id, msg_data in stream_msgs:
                    parsed = self._parse_message(msg_data)
                    if parsed.get("from") != agent_id:  # Don't read own broadcasts
                        messages.append(parsed)
        except Exception:
            pass

        return messages

    async def publish_timeline_event(
        self, event_type: str, label: str, agent: str = "system", data: dict = None
    ) -> str:
        """Publish an event to the crisis timeline."""
        event = {
            "id": str(uuid.uuid4())[:8],
            "timestamp": time.time(),
            "event_type": event_type,
            "label": label,
            "agent": agent,
            "data": json.dumps(data or {}),
        }
        await self.redis.xadd(self.TIMELINE_STREAM, event)
        return event["id"]

    async def get_timeline(self, count: int = 50) -> List[dict]:
        """Get timeline events."""
        try:
            raw = await self.redis.xrange(self.TIMELINE_STREAM, count=count)
            return [self._parse_message(data) for _, data in raw]
        except Exception:
            return []

    async def get_messages(self, stream: str, count: int = 50) -> List[dict]:
        """Get messages from any stream."""
        try:
            raw = await self.redis.xrange(stream, count=count)
            return [self._parse_message(data) for _, data in raw]
        except Exception:
            return []

    def _parse_message(self, data: dict) -> dict:
        """Parse Redis stream message bytes to strings."""
        parsed = {}
        for k, v in data.items():
            key = k.decode() if isinstance(k, bytes) else k
            val = v.decode() if isinstance(v, bytes) else v
            if key == "payload" or key == "data":
                try:
                    val = json.loads(val)
                except (json.JSONDecodeError, TypeError):
                    pass
            parsed[key] = val
        return parsed
