"""MQTT Client — IoT sensor ingestion via Mosquitto broker."""
import asyncio
import json
import logging
import time
from typing import Callable, Optional

logger = logging.getLogger("nexus.mqtt")


class MQTTClient:
    """
    Async MQTT client for ingesting IoT sensor data.
    Subscribes to sensor topics and pipes data into CDIL + EventBus.
    """

    SENSOR_TOPICS = [
        "nexus/sensors/#",
        "nexus/weather/#",
        "nexus/traffic/#",
        "nexus/power/#",
    ]

    def __init__(self, cdil, event_bus, ws_broadcast: Callable,
                 host: str = "localhost", port: int = 1883):
        self.cdil = cdil
        self.event_bus = event_bus
        self.ws_broadcast = ws_broadcast
        self.host = host
        self.port = port
        self._running = False
        self._client = None

    async def start(self):
        """Start the MQTT subscription loop."""
        try:
            import paho.mqtt.client as mqtt
        except ImportError:
            logger.warning("[MQTT] paho-mqtt not installed — MQTT disabled")
            return

        self._running = True
        self._client = mqtt.Client(client_id="nexus-gov-backend", protocol=mqtt.MQTTv311)
        self._client.on_connect = self._on_connect
        self._client.on_message = self._on_message_sync
        self._client.on_disconnect = self._on_disconnect

        try:
            self._client.connect(self.host, self.port, keepalive=60)
            self._client.loop_start()
            logger.info(f"[MQTT] Connected to broker at {self.host}:{self.port}")
        except Exception as e:
            logger.warning(f"[MQTT] Failed to connect to broker: {e} — continuing without MQTT")
            self._running = False

    async def stop(self):
        """Stop MQTT client."""
        self._running = False
        if self._client:
            self._client.loop_stop()
            self._client.disconnect()
            logger.info("[MQTT] Disconnected from broker")

    def _on_connect(self, client, userdata, flags, rc):
        """Subscribe to all sensor topics on connect."""
        if rc == 0:
            logger.info("[MQTT] Connected to broker successfully")
            for topic in self.SENSOR_TOPICS:
                client.subscribe(topic, qos=1)
                logger.info(f"[MQTT] Subscribed to: {topic}")
        else:
            logger.error(f"[MQTT] Connection failed with code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Handle disconnection."""
        if rc != 0:
            logger.warning(f"[MQTT] Unexpected disconnect (rc={rc}), will auto-reconnect")

    def _on_message_sync(self, client, userdata, msg):
        """Synchronous callback — dispatches to async handler."""
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                asyncio.ensure_future(self._on_message(msg))
            else:
                loop.run_until_complete(self._on_message(msg))
        except RuntimeError:
            # No event loop in thread — create a task for later
            asyncio.ensure_future(self._on_message(msg))

    async def _on_message(self, msg):
        """Process incoming MQTT message and pipe into CDIL."""
        topic = msg.topic
        try:
            payload = json.loads(msg.payload.decode())
        except (json.JSONDecodeError, UnicodeDecodeError):
            logger.warning(f"[MQTT] Invalid payload on {topic}: {msg.payload}")
            return

        logger.info(f"[MQTT] {topic} → {payload}")

        # ── Route by topic ──
        if topic.startswith("nexus/sensors/water"):
            await self._handle_water_sensor(payload)
        elif topic.startswith("nexus/sensors/seismic"):
            await self._handle_seismic_sensor(payload)
        elif topic.startswith("nexus/weather"):
            await self._handle_weather(payload)
        elif topic.startswith("nexus/traffic"):
            await self._handle_traffic(payload)
        elif topic.startswith("nexus/power"):
            await self._handle_power(payload)
        else:
            # Generic sensor
            await self._handle_generic(topic, payload)

    async def _handle_water_sensor(self, data: dict):
        """Water level sensor → CDIL zone flood data."""
        zone = data.get("zone", "zone_c1")
        value = float(data.get("value", 0))
        unit = data.get("unit", "cm")

        await self.cdil.update(f"sensor:{zone}:water_level", str(value), source="mqtt_sensor")
        if value > 50:
            await self.cdil.update(f"zone:{zone}:flood_risk", "HIGH", source="mqtt_sensor")
        if value > 80:
            await self.cdil.update(f"zone:{zone}:flood_risk", "CRITICAL", source="mqtt_sensor")

        await self.ws_broadcast("reasoning_log", {
            "agent": "system",
            "badge": "IOT",
            "message": f"🌊 MQTT Water Sensor [{zone}]: {value}{unit}",
            "severity": "critical" if value > 80 else "warning" if value > 50 else "info",
            "timestamp": time.time(),
        })

    async def _handle_seismic_sensor(self, data: dict):
        """Seismic sensor → CDIL structural integrity."""
        zone = data.get("zone", "zone_c3")
        magnitude = float(data.get("value", 0))

        integrity = max(0, 100 - magnitude * 10)
        await self.cdil.update(f"zone:{zone}:structural_integrity", str(integrity), source="mqtt_sensor")

        if magnitude > 4.0:
            await self.cdil.update(f"zone:{zone}:seismic_alert", "ACTIVE", source="mqtt_sensor")

        await self.ws_broadcast("reasoning_log", {
            "agent": "system",
            "badge": "IOT",
            "message": f"💥 MQTT Seismic Sensor [{zone}]: Magnitude {magnitude}",
            "severity": "critical" if magnitude > 5 else "warning",
            "timestamp": time.time(),
        })

    async def _handle_weather(self, data: dict):
        """Weather data → CDIL rainfall/temperature."""
        rainfall = data.get("rainfall_mm_hr", 0)
        temp = data.get("temperature_c", 30)
        humidity = data.get("humidity", 60)
        wind_speed = data.get("wind_speed_kmh", 0)

        # Update all weather-related CDIL keys
        await self.cdil.update("weather:rainfall_mm_hr", str(rainfall), source="mqtt_weather")
        await self.cdil.update("weather:temperature_c", str(temp), source="mqtt_weather")
        await self.cdil.update("weather:humidity", str(humidity), source="mqtt_weather")
        await self.cdil.update("weather:wind_speed_kmh", str(wind_speed), source="mqtt_weather")

        # Map rainfall to sensor zones
        for zone in ["zone_c1", "zone_c2"]:
            await self.cdil.update(f"sensor:{zone}:rainfall_mm_hr", str(rainfall), source="mqtt_weather")

    async def _handle_traffic(self, data: dict):
        """Traffic data → CDIL zone congestion."""
        zone = data.get("zone", "zone_c1")
        congestion = data.get("congestion_index", 0)
        flow_rate = data.get("flow_rate", 0)

        await self.cdil.update(f"zone:{zone}:congestion_index", str(congestion), source="mqtt_traffic")
        await self.cdil.update(f"zone:{zone}:traffic_flow", str(flow_rate), source="mqtt_traffic")

    async def _handle_power(self, data: dict):
        """Power grid data → CDIL substation load."""
        substation = data.get("substation", "sub_1")
        load_mw = data.get("load_mw", 0)

        await self.cdil.update(f"substation:{substation}:load_mw", str(load_mw), source="mqtt_power")

    async def _handle_generic(self, topic: str, data: dict):
        """Generic sensor fallback → log and store."""
        key = topic.replace("/", ":")
        await self.cdil.update(key, json.dumps(data), source="mqtt_generic")
        logger.info(f"[MQTT] Generic sensor: {key}")

    def publish(self, topic: str, payload: dict):
        """Publish a message (e.g., for actuator commands)."""
        if self._client and self._running:
            self._client.publish(topic, json.dumps(payload), qos=1)
