"""Flood Agent — Rainfall monitoring, flood risk prediction, evacuation alerts."""
import asyncio
import time
import logging
from typing import List

from agents.base_agent import BaseAgent
from config import settings

logger = logging.getLogger("nexus.agent.flood")


class FloodAgent(BaseAgent):
    AGENT_ID = "flood_agent"
    AGENT_NAME = "Flood Agent"
    DOMAIN = "HYDROLOGY"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._last_weather_fetch = 0
        self._weather_task = None

    async def start(self):
        """Start agent + background weather polling."""
        self._weather_task = asyncio.create_task(self._weather_poll_loop())
        await super().start()

    async def stop(self):
        """Stop agent + cancel weather polling."""
        if self._weather_task:
            self._weather_task.cancel()
        await super().stop()

    # ── Live Weather API ──

    async def _weather_poll_loop(self):
        """Background loop: fetch live weather data from OpenWeatherMap."""
        while True:
            try:
                await self._fetch_live_weather()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"[FloodAgent] Weather poll error: {e}")
            await asyncio.sleep(settings.WEATHER_POLL_INTERVAL)

    async def _fetch_live_weather(self):
        """Fetch weather from OpenWeatherMap and inject into CDIL."""
        api_key = settings.OPENWEATHERMAP_API_KEY
        if not api_key:
            return  # No API key configured

        import httpx
        url = (
            f"https://api.openweathermap.org/data/2.5/weather"
            f"?id={settings.OPENWEATHERMAP_CITY_ID}"
            f"&appid={api_key}&units=metric"
        )

        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(url)
            if resp.status_code != 200:
                logger.warning(f"[FloodAgent] Weather API returned {resp.status_code}")
                return
            data = resp.json()

        # Extract weather data
        rain_1h = data.get("rain", {}).get("1h", 0)  # mm in last hour
        rain_3h = data.get("rain", {}).get("3h", 0)
        temp = data.get("main", {}).get("temp", 30)
        humidity = data.get("main", {}).get("humidity", 60)
        wind_speed = data.get("wind", {}).get("speed", 0) * 3.6  # m/s → km/h
        weather_desc = data.get("weather", [{}])[0].get("description", "clear")

        # Inject into CDIL
        await self.cdil.update("weather:rainfall_1h_mm", str(rain_1h), source="openweathermap")
        await self.cdil.update("weather:rainfall_3h_mm", str(rain_3h), source="openweathermap")
        await self.cdil.update("weather:temperature_c", str(temp), source="openweathermap")
        await self.cdil.update("weather:humidity", str(humidity), source="openweathermap")
        await self.cdil.update("weather:wind_speed_kmh", str(round(wind_speed, 1)), source="openweathermap")
        await self.cdil.update("weather:description", weather_desc, source="openweathermap")

        # Map rain to zone sensors (propagate to all zones)
        rainfall_rate = rain_1h if rain_1h > 0 else rain_3h / 3.0
        for zone in ["zone_c1", "zone_c2", "zone_c3", "zone_c4"]:
            await self.cdil.update(
                f"sensor:{zone}:rainfall_mm_hr", str(round(rainfall_rate, 1)),
                source="openweathermap"
            )

        if rainfall_rate > 0:
            await self._broadcast_reasoning(
                f"🌦 Live Weather: {weather_desc}. Rain: {rainfall_rate:.1f}mm/hr, "
                f"Temp: {temp}°C, Humidity: {humidity}%, Wind: {wind_speed:.1f}km/h",
                severity="warning" if rainfall_rate > 30 else "info"
            )

        self._last_weather_fetch = time.time()
        logger.info(f"[FloodAgent] Weather updated: rain={rainfall_rate}mm/hr, desc={weather_desc}")

    # ── Core Agent Logic ──

    def _should_act(self, cdil_state: dict, messages: list) -> bool:
        """Act on rainfall data or cross-domain messages."""
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
            rainfall = float(cdil_state.get(f"sensor:{zone_id}:rainfall_mm_hr", 0))
            predicted = round(rainfall / 120 * args.get("hours_ahead", 2), 2)

            await self._broadcast_reasoning(
                f"Predicted water level for {zone_id} in {args.get('hours_ahead', 2)}hrs: {predicted}m",
                severity="info"
            )

    def _get_system_prompt(self) -> str:
        return """You are the Flood Agent in NEXUS-GOV for Hyderabad, India.
YOUR RESPONSIBILITIES:
- Monitor rainfall sensors across 12 city zones (including LIVE OpenWeatherMap data)
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

