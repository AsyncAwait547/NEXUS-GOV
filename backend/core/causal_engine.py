"""Causal Inference Engine — Rule-based cross-domain effect propagation."""
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("nexus.causal")


CAUSAL_RULES = [
    {
        "id": "flood_blocks_roads",
        "condition": {"key_pattern": "zone:*:flood_risk", "value": "HIGH"},
        "effects": [
            {"key_pattern": "road:{road_id}:status", "value": "FLOODED", "confidence": 0.85},
        ],
        "description": "Flooding blocks roads in affected zones",
        "resolver": "roads_in_zone",
    },
    {
        "id": "flood_critical_blocks_roads",
        "condition": {"key_pattern": "zone:*:flood_risk", "value": "CRITICAL"},
        "effects": [
            {"key_pattern": "road:{road_id}:status", "value": "FLOODED", "confidence": 0.95},
        ],
        "description": "Critical flooding blocks all roads in zone",
        "resolver": "roads_in_zone",
    },
    {
        "id": "flood_increases_traffic",
        "condition": {"key_pattern": "zone:*:flood_risk", "value": "HIGH"},
        "effects": [
            {"key_pattern": "zone:{adj_zone}:traffic_congestion", "delta": 0.3, "confidence": 0.75},
        ],
        "description": "Flooding blocks roads causing traffic congestion in adjacent zones",
        "resolver": "adjacent_zones",
    },
    {
        "id": "power_down_darkens_signals",
        "condition": {"key_pattern": "zone:*:power_status", "value": "DOWN"},
        "effects": [
            {"key_pattern": "zone:{zone_id}:traffic_congestion", "delta": 0.2, "confidence": 0.70},
        ],
        "description": "Power outage darkens signals, increasing congestion",
        "resolver": "same_zone",
    },
    {
        "id": "congestion_delays_ambulance",
        "condition": {"key_pattern": "zone:*:traffic_congestion", "threshold": 0.8},
        "effects": [
            {"key_pattern": "ambulance:{amb_id}:travel_time_multiplier", "value": "2.5", "confidence": 0.80},
        ],
        "description": "High congestion increases ambulance response time by 2.5x",
        "resolver": "ambulances_in_zone",
    },
    {
        "id": "substation_flooded_power_outage",
        "condition": {"key_pattern": "substation:*:is_flooded", "value": "true"},
        "effects": [
            {"key_pattern": "zone:{zone_id}:power_status", "value": "DOWN", "confidence": 0.90},
        ],
        "description": "Flooded substation causes power outage in served zones",
        "resolver": "zones_served_by_substation",
    },
]


class CausalEngine:
    """Propagates causal effects when CDIL state changes."""

    def __init__(self, cdil, city_model: dict):
        self.cdil = cdil
        self.city_model = city_model
        self.rules = CAUSAL_RULES
        self._adjacency = city_model.get("adjacency", {})
        self._roads = city_model.get("roads", [])
        self._substations = city_model.get("substations", [])
        self._ambulances = city_model.get("ambulances", [])

    async def propagate_effects(self, trigger_key: str, trigger_value: str) -> List[dict]:
        """When a CDIL value changes, compute and apply causal effects."""
        effects_applied = []

        for rule in self.rules:
            if not self._matches_condition(rule["condition"], trigger_key, trigger_value):
                continue

            zone_id = self._extract_zone_from_key(trigger_key)
            if not zone_id:
                continue

            resolved_effects = self._resolve_effects(rule, zone_id)

            for eff_key, eff_value, confidence in resolved_effects:
                current = await self.cdil.get(eff_key)

                # Handle delta updates
                if isinstance(eff_value, dict) and "delta" in eff_value:
                    try:
                        current_val = float(current or 0)
                        new_val = min(1.0, max(0.0, current_val + eff_value["delta"]))
                        eff_value = str(round(new_val, 2))
                    except ValueError:
                        continue

                await self.cdil.update(
                    eff_key, eff_value,
                    source="causal_engine",
                    confidence=confidence
                )
                effects_applied.append({
                    "rule": rule["description"],
                    "trigger": trigger_key,
                    "affected_key": eff_key,
                    "value": eff_value,
                    "confidence": confidence,
                })

        if effects_applied:
            logger.info(f"[Causal] {len(effects_applied)} effects from {trigger_key}")
        return effects_applied

    def _matches_condition(self, condition: dict, key: str, value: str) -> bool:
        """Check if the trigger matches a rule condition."""
        pattern = condition["key_pattern"]
        parts_pattern = pattern.split(":")
        parts_key = key.split(":")

        if len(parts_pattern) != len(parts_key):
            return False

        for pp, pk in zip(parts_pattern, parts_key):
            if pp != "*" and pp != pk:
                return False

        # Check value match
        if "value" in condition:
            return value == str(condition["value"])
        elif "threshold" in condition:
            try:
                return float(value) >= condition["threshold"]
            except ValueError:
                return False
        return True

    def _extract_zone_from_key(self, key: str) -> str:
        """Extract zone_id from a CDIL key like 'zone:zone_c2:flood_risk'."""
        parts = key.split(":")
        if len(parts) >= 2:
            entity = parts[1]
            if entity.startswith("zone_") or entity.startswith("sub_"):
                return entity
        return ""

    def _resolve_effects(self, rule: dict, source_id: str):
        """Resolve effect targets based on resolver type."""
        resolver = rule.get("resolver", "same_zone")
        results = []

        for effect in rule["effects"]:
            confidence = effect.get("confidence", 0.5)

            if resolver == "roads_in_zone":
                zone_id = source_id if source_id.startswith("zone_") else source_id
                for road in self._roads:
                    if road["from"] == zone_id or road["to"] == zone_id:
                        if road.get("flood_prone", False):
                            eff_key = f"road:{road['id']}:status"
                            results.append((eff_key, effect["value"], confidence))

            elif resolver == "adjacent_zones":
                adj_zones = self._adjacency.get(source_id, [])
                for az in adj_zones:
                    eff_key = effect["key_pattern"].replace("{adj_zone}", az)
                    results.append((eff_key, {"delta": effect.get("delta", 0)}, confidence))

            elif resolver == "same_zone":
                eff_key = effect["key_pattern"].replace("{zone_id}", source_id)
                if "delta" in effect:
                    results.append((eff_key, {"delta": effect["delta"]}, confidence))
                else:
                    results.append((eff_key, effect["value"], confidence))

            elif resolver == "ambulances_in_zone":
                for amb in self._ambulances:
                    if amb.get("home") == source_id:
                        eff_key = f"ambulance:{amb['id']}:travel_time_multiplier"
                        results.append((eff_key, effect["value"], confidence))

            elif resolver == "zones_served_by_substation":
                for sub in self._substations:
                    if sub["id"] == source_id:
                        zone = sub["zone"]
                        eff_key = effect["key_pattern"].replace("{zone_id}", zone)
                        results.append((eff_key, effect["value"], confidence))

        return results
