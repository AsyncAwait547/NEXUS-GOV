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

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
