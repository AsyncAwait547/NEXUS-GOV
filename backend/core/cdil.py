"""Cross-Domain Inference Layer (CDIL) — Redis Hash backed shared state."""
import json
import time
import logging
from typing import Any, Dict, Optional
import redis.asyncio as aioredis

logger = logging.getLogger("nexus.cdil")


class CDIL:
    """Shared city state backed by Redis Hash. All agents read/write here."""

    HASH_KEY = "nexus:cdil"
    CHANGE_CHANNEL = "nexus:cdil:changes"

    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client
        self._subscribers = []

    async def initialize(self, city_model: dict):
        """Seed CDIL with initial city state from city_model.json."""
        pipe = self.redis.pipeline()

        for zone in city_model.get("zones", []):
            zid = zone["id"]
            pipe.hset(self.HASH_KEY, f"zone:{zid}:flood_risk", "LOW")
            pipe.hset(self.HASH_KEY, f"zone:{zid}:traffic_congestion", "0.1")
            pipe.hset(self.HASH_KEY, f"zone:{zid}:power_status", "ACTIVE")
            pipe.hset(self.HASH_KEY, f"zone:{zid}:evacuation_status", "NORMAL")
            pipe.hset(self.HASH_KEY, f"zone:{zid}:backup_active", "false")
            pipe.hset(self.HASH_KEY, f"zone:{zid}:population", str(zone["population"]))
            pipe.hset(self.HASH_KEY, f"zone:{zid}:elevation_m", str(zone["elevation_m"]))

        for road in city_model.get("roads", []):
            rid = road["id"]
            pipe.hset(self.HASH_KEY, f"road:{rid}:status", "OPEN")
            pipe.hset(self.HASH_KEY, f"road:{rid}:travel_time_min", "10")

        for sub in city_model.get("substations", []):
            sid = sub["id"]
            pipe.hset(self.HASH_KEY, f"substation:{sid}:load_pct", "65")
            pipe.hset(self.HASH_KEY, f"substation:{sid}:is_flooded", "false")
            pipe.hset(self.HASH_KEY, f"substation:{sid}:capacity_mw", str(sub["capacity_mw"]))

        for hosp in city_model.get("hospitals", []):
            hid = hosp["id"]
            pipe.hset(self.HASH_KEY, f"hospital:{hid}:beds_available", str(hosp["beds"]))
            pipe.hset(self.HASH_KEY, f"hospital:{hid}:icu_available", str(hosp["icu"]))

        for amb in city_model.get("ambulances", []):
            aid = amb["id"]
            pipe.hset(self.HASH_KEY, f"ambulance:{aid}:zone", amb["home"])
            pipe.hset(self.HASH_KEY, f"ambulance:{aid}:status", "IDLE")
            pipe.hset(self.HASH_KEY, f"ambulance:{aid}:lat", str(amb["lat"]))
            pipe.hset(self.HASH_KEY, f"ambulance:{aid}:lng", str(amb["lng"]))

        # System state
        pipe.hset(self.HASH_KEY, "system:threat_level", "1")
        pipe.hset(self.HASH_KEY, "system:active_scenario", "none")
        pipe.hset(self.HASH_KEY, "system:decision_count", "0")

        await pipe.execute()
        logger.info("CDIL initialized with city model data")

    async def get_snapshot(self) -> Dict[str, str]:
        """Get full CDIL state as a dict."""
        raw = await self.redis.hgetall(self.HASH_KEY)
        return {k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in raw.items()}

    async def get(self, key: str) -> Optional[str]:
        """Get a single CDIL key."""
        val = await self.redis.hget(self.HASH_KEY, key)
        return val.decode() if isinstance(val, bytes) else val

    async def update(self, key: str, value: Any, source: str = "system",
                     confidence: float = 1.0) -> dict:
        """Update a single CDIL key and broadcast change."""
        str_value = str(value) if not isinstance(value, str) else value
        await self.redis.hset(self.HASH_KEY, key, str_value)

        change = {
            "key": key,
            "value": str_value,
            "source": source,
            "confidence": confidence,
            "timestamp": time.time(),
        }

        # Publish change notification
        await self.redis.publish(self.CHANGE_CHANNEL, json.dumps(change))

        logger.debug(f"CDIL update: {key} = {str_value} (by {source})")
        return change

    async def batch_update(self, updates: Dict[str, Any], source: str = "system") -> list:
        """Update multiple CDIL keys atomically."""
        changes = []
        pipe = self.redis.pipeline()

        for key, value in updates.items():
            str_value = str(value) if not isinstance(value, str) else value
            pipe.hset(self.HASH_KEY, key, str_value)
            changes.append({
                "key": key,
                "value": str_value,
                "source": source,
                "timestamp": time.time(),
            })

        await pipe.execute()

        # Broadcast all changes
        for change in changes:
            await self.redis.publish(self.CHANGE_CHANNEL, json.dumps(change))

        return changes

    async def get_zone_state(self, zone_id: str) -> dict:
        """Get all state for a specific zone."""
        snapshot = await self.get_snapshot()
        prefix = f"zone:{zone_id}:"
        return {k.replace(prefix, ""): v for k, v in snapshot.items() if k.startswith(prefix)}

    async def increment(self, key: str, amount: int = 1) -> int:
        """Atomically increment a counter."""
        return await self.redis.hincrby(self.HASH_KEY, key, amount)
