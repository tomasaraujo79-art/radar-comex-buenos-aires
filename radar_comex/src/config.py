from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]


def _coerce_env(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def load_config() -> dict[str, Any]:
    load_dotenv(ROOT / ".env")
    config_path = ROOT / "config.yaml"
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    app = config.setdefault("app", {})
    env_map = {
        "MAX_TRAVEL_MINUTES": ("max_travel_minutes", int),
        "REFERENCE_LOCATION": ("reference_location", str),
        "MIN_SCORE": ("min_score", int),
        "TIMEZONE": ("timezone", str),
        "DAILY_RUN_TIME": ("daily_run_time", str),
    }
    for env_key, (config_key, caster) in env_map.items():
        if os.getenv(env_key):
            app[config_key] = caster(os.environ[env_key])

    config.setdefault("integrations", {})
    config["integrations"]["openrouteservice_api_key"] = os.getenv("OPENROUTESERVICE_API_KEY", "")
    config["integrations"]["email"] = {
        "enabled": _coerce_env(os.getenv("ENABLE_EMAIL_NOTIFICATIONS", "false")),
        "smtp_host": os.getenv("SMTP_HOST", ""),
        "smtp_port": int(os.getenv("SMTP_PORT", "587")),
        "smtp_username": os.getenv("SMTP_USERNAME", ""),
        "smtp_password": os.getenv("SMTP_PASSWORD", ""),
        "email_from": os.getenv("EMAIL_FROM", ""),
        "email_to": os.getenv("EMAIL_TO", ""),
    }
    config["integrations"]["telegram"] = {
        "enabled": _coerce_env(os.getenv("ENABLE_TELEGRAM_NOTIFICATIONS", "false")),
        "bot_token": os.getenv("TELEGRAM_BOT_TOKEN", ""),
        "chat_id": os.getenv("TELEGRAM_CHAT_ID", ""),
    }

    for key in ["database_path", "reports_dir", "logs_dir"]:
        if key in app:
            app[key] = str((ROOT / app[key]).resolve())
    return config

