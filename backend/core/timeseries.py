"""InfluxDB Time-Series Client — Stores sensor data for historical analysis."""
import logging
import time
from typing import Dict, List, Optional
from datetime import datetime

logger = logging.getLogger("nexus.timeseries")


class TimeSeriesDB:
    """
    InfluxDB wrapper for storing and querying time-series sensor data.
    Provides dual-write capability alongside Redis CDIL.
    """

    def __init__(self, url: str, token: str, org: str, bucket: str):
        self.url = url
        self.token = token
        self.org = org
        self.bucket = bucket
        self._client = None
        self._write_api = None
        self._query_api = None
        self._enabled = False

    async def initialize(self):
        """Initialize InfluxDB client and create bucket if needed."""
        try:
            from influxdb_client import InfluxDBClient, Point
            from influxdb_client.client.write_api import ASYNCHRONOUS

            self._client = InfluxDBClient(
                url=self.url, token=self.token, org=self.org
            )
            self._write_api = self._client.write_api(write_options=ASYNCHRONOUS)
            self._query_api = self._client.query_api()

            # Verify connection
            health = self._client.health()
            if health.status == "pass":
                self._enabled = True
                logger.info(f"[TimeSeries] InfluxDB connected: {self.url}")
            else:
                logger.warning(f"[TimeSeries] InfluxDB health check failed: {health.message}")
        except ImportError:
            logger.warning("[TimeSeries] influxdb-client not installed — time-series disabled")
        except Exception as e:
            logger.warning(f"[TimeSeries] InfluxDB connection failed: {e} — continuing without time-series")

    async def close(self):
        """Close the InfluxDB client."""
        if self._client:
            self._client.close()
            logger.info("[TimeSeries] InfluxDB connection closed")

    def write_sensor_data(
        self,
        measurement: str,
        tags: Dict[str, str],
        fields: Dict[str, float],
        timestamp: Optional[datetime] = None,
    ):
        """Write a sensor data point to InfluxDB."""
        if not self._enabled or not self._write_api:
            return

        try:
            from influxdb_client import Point

            point = Point(measurement)
            for key, val in tags.items():
                point = point.tag(key, val)
            for key, val in fields.items():
                point = point.field(key, float(val) if isinstance(val, (int, float, str)) else val)
            if timestamp:
                point = point.time(timestamp)

            self._write_api.write(bucket=self.bucket, record=point)
        except Exception as e:
            logger.error(f"[TimeSeries] Write error: {e}")

    def write_cdil_update(self, key: str, value: str, source: str):
        """
        Dual-write hook: called from CDIL.update() to persist every state change.
        Parses the CDIL key format (e.g., 'zone:zone_c1:flood_risk') into
        InfluxDB measurement/tags/fields.
        """
        if not self._enabled:
            return

        parts = key.split(":")
        if len(parts) >= 3:
            measurement = parts[0]  # zone, sensor, weather, substation
            entity = parts[1]       # zone_c1, sub_1, etc.
            field_name = parts[2]   # flood_risk, water_level, etc.
        elif len(parts) == 2:
            measurement = parts[0]
            entity = "global"
            field_name = parts[1]
        else:
            measurement = "misc"
            entity = "unknown"
            field_name = key

        # Try to parse value as float, otherwise store as string field
        try:
            numeric_val = float(value)
            fields = {field_name: numeric_val}
        except (ValueError, TypeError):
            fields = {f"{field_name}_str": 1.0}  # InfluxDB requires numeric fields

        self.write_sensor_data(
            measurement=measurement,
            tags={"entity": entity, "source": source},
            fields=fields,
        )

    def write_agent_decision(self, agent: str, action: str, confidence: float):
        """Log agent decision metrics for analysis."""
        if not self._enabled:
            return

        self.write_sensor_data(
            measurement="agent_decisions",
            tags={"agent": agent, "action": action},
            fields={"confidence": confidence, "count": 1.0},
        )

    async def query_range(
        self, measurement: str, entity: str, field: str, hours: int = 24
    ) -> List[dict]:
        """Query time-series data for a given range."""
        if not self._enabled or not self._query_api:
            return []

        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r._measurement == "{measurement}")
                |> filter(fn: (r) => r.entity == "{entity}")
                |> filter(fn: (r) => r._field == "{field}")
                |> sort(columns: ["_time"], desc: false)
            '''
            tables = self._query_api.query(query, org=self.org)
            results = []
            for table in tables:
                for record in table.records:
                    results.append({
                        "time": record.get_time().isoformat(),
                        "value": record.get_value(),
                        "field": record.get_field(),
                    })
            return results
        except Exception as e:
            logger.error(f"[TimeSeries] Query error: {e}")
            return []

    async def get_stats(self, measurement: str, entity: str, field: str, hours: int = 1) -> dict:
        """Get aggregated statistics (mean, min, max) for a field."""
        if not self._enabled or not self._query_api:
            return {"mean": 0, "min": 0, "max": 0, "count": 0}

        try:
            query = f'''
                from(bucket: "{self.bucket}")
                |> range(start: -{hours}h)
                |> filter(fn: (r) => r._measurement == "{measurement}")
                |> filter(fn: (r) => r.entity == "{entity}")
                |> filter(fn: (r) => r._field == "{field}")
            '''
            tables = self._query_api.query(query, org=self.org)
            values = [record.get_value() for table in tables for record in table.records]

            if not values:
                return {"mean": 0, "min": 0, "max": 0, "count": 0}

            return {
                "mean": round(sum(values) / len(values), 2),
                "min": round(min(values), 2),
                "max": round(max(values), 2),
                "count": len(values),
            }
        except Exception as e:
            logger.error(f"[TimeSeries] Stats query error: {e}")
            return {"mean": 0, "min": 0, "max": 0, "count": 0}
