"""NEXUS-GOV Configuration — Pydantic Settings."""
import os
from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # ── LLM Keys ──
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # ── Redis ──
    REDIS_URL: str = "redis://localhost:6379"

    # ── Server ──
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    SECRET_KEY: str = "nexus-gov-secret-2026"

    # ── Demo Mode ──
    DEMO_MODE: bool = True
    MOCK_LLM: bool = True
    VERBOSE_REASONING: bool = True

    # ── Agent Config ──
    AGENT_CYCLE_INTERVAL: float = 2.0
    LLM_TIMEOUT: int = 15
    LLM_RETRY_COUNT: int = 1
    CONFIDENCE_THRESHOLD: float = 0.6

    # ── Audit ──
    AUDIT_DB_PATH: str = "data/audit.db"

    # ── CORS ──
    CORS_ORIGINS: list = ["http://localhost:5173", "http://localhost:3000", "*"]

    # ── MQTT ──
    MQTT_BROKER_HOST: str = "localhost"
    MQTT_BROKER_PORT: int = 1883
    MQTT_ENABLED: bool = True

    # ── InfluxDB ──
    INFLUXDB_URL: str = "http://localhost:8086"
    INFLUXDB_TOKEN: str = "nexus-gov-influx-token"
    INFLUXDB_ORG: str = "nexus-gov"
    INFLUXDB_BUCKET: str = "city_telemetry"
    INFLUXDB_ENABLED: bool = True

    # ── Kafka / Redpanda ──
    KAFKA_BROKER_URL: str = "localhost:9092"
    USE_KAFKA: bool = False

    # ── Live Data APIs ──
    OPENWEATHERMAP_API_KEY: str = ""
    OPENWEATHERMAP_CITY_ID: str = "1269843"  # Hyderabad
    WEATHER_POLL_INTERVAL: int = 60  # seconds

    # ── JWT Auth ──
    JWT_SECRET: str = "nexus-gov-jwt-secret-2026"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()

