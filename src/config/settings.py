# src/config/settings.py
import os, json
BASE = os.path.dirname(os.path.dirname(__file__))
CFG_PATH = os.path.join(BASE, "config", "defaults.json")
try:
    with open(CFG_PATH) as f:
        CONFIG = json.load(f)
except Exception:
    CONFIG = {}
DEFAULT_REGION = os.getenv("AWS_REGION") or CONFIG.get("default_region", "us-west-1")
