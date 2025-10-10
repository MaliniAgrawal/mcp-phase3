# src/config/settings.py
import os
import json

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
CONFIG_PATH = os.path.join(BASE_DIR, "config", "defaults.json")

try:
    with open(CONFIG_PATH) as f:
        CONFIG = json.load(f)
except Exception:
    CONFIG = {}

DEFAULT_REGION = os.getenv("AWS_REGION") or CONFIG.get("default_region", "us-west-1")
