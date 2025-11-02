# src/core/nlp_utils.py
import os
import re
from typing import Tuple, Dict
from loguru import logger

ENABLE_ML = os.getenv("ENABLE_ML", "true").lower() in ("1","true","yes")
NLP_MODE = os.getenv("NLP_MODE", "local").lower()  # local | haiku
ML_CONF_THRESHOLD = float(os.getenv("ML_CONF_THRESHOLD", "0.7"))

# lazy classifier for local zero-shot
_classifier = None
def _get_local_classifier():
    global _classifier
    if _classifier:
        return _classifier
    if not ENABLE_ML:
        return None
    try:
        # Ensure PyTorch is available before using transformers' PyTorch-based pipelines.
        try:
            import torch  # noqa: F401
        except Exception:
            logger.warning("PyTorch not available; skipping local ML classifier")
            _classifier = None
            return _classifier

        from transformers import pipeline
        _classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        logger.info("Local ML classifier initialized")
    except Exception as e:
        logger.exception("Failed to init local classifier: %s", e)
        _classifier = None
    return _classifier

# anthropic client (Haiku fallback)
_haiku_client = None
def _get_haiku_client():
    global _haiku_client
    if _haiku_client:
        return _haiku_client
    if NLP_MODE != "haiku":
        return None
    try:
        from anthropic import Anthropic
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            logger.warning("Haiku enabled but ANTHROPIC_API_KEY not set")
            return None
        _haiku_client = Anthropic(api_key=key)
        logger.info("Anthropic Haiku client initialized")
    except Exception as e:
        logger.exception("Failed to init anthropic client: %s", e)
        _haiku_client = None
    return _haiku_client

INTENTS = [
    "create_s3_bucket", "list_s3_buckets",
    "create_dynamodb_table", "list_dynamodb_tables",
    "start_ec2_instance", "stop_ec2_instance", "list_ec2_instances", "describe_ec2_instances",
    "create_iam_user", "list_iam_users",
    "invoke_lambda", "list_lambda_functions",
    "unknown"
]

def _rule_intent_and_entities(text: str) -> Tuple[str, Dict]:
    t = text.lower()
    r = re.search(r"(?:in\s+|region\s+)(us-[a-z0-9-]+)", t)
    region = r.group(1) if r else None

    # S3
    if re.search(r"\b(create|make)\b.*\b(s3|bucket)\b", t):
        m = re.search(r"(?:named|called|name(?:d)?|bucket\s+named|bucket\s+)([a-z0-9][a-z0-9\-\.]{2,62})", t)
        bucket = m.group(1) if m else None
        return "create_s3_bucket", {"bucket": bucket, "region": region}
    if re.search(r"\b(list|show)\b.*\b(s3|buckets)\b", t):
        return "list_s3_buckets", {"region": region}

    # DynamoDB
    if re.search(r"\b(create|make)\b.*\b(dynamo|dynamodb|table)\b", t):
        m = re.search(r"(?:table\s+named|table\s+)([A-Za-z0-9_\-]+)", t)
        return "create_dynamodb_table", {"table": m.group(1) if m else None, "region": region}
    if re.search(r"\b(list|show)\b.*\b(dynamo|tables)\b", t):
        return "list_dynamodb_tables", {"region": region}

    # EC2
    m_start = re.search(r"\b(start|run)\b.*\b(ec2|instance)\b.*\b(i-[0-9a-fA-F]+)\b", t)
    if m_start:
        return "start_ec2_instance", {"instance_id": m_start.group(3), "region": region}
    m_stop = re.search(r"\b(stop|terminate)\b.*\b(ec2|instance)\b.*\b(i-[0-9a-fA-F]+)\b", t)
    if m_stop:
        return "stop_ec2_instance", {"instance_id": m_stop.group(3), "region": region}
    if re.search(r"\b(list|show|describe)\b.*\b(ec2|instances)\b", t):
        m_tag = re.search(r"tag\s+([A-Za-z0-9\-_]+)=([A-Za-z0-9\-_]+)", t)
        tag = {m_tag.group(1): m_tag.group(2)} if m_tag else None
        return "describe_ec2_instances", {"region": region, "tag": tag}

    # IAM
    if re.search(r"\b(create|add)\b.*\b(iam|user)\b", t):
        m = re.search(r"(?:user\s+named|user\s+)([A-Za-z0-9_\-]+)", t)
        return "create_iam_user", {"user": m.group(1) if m else None}
    if re.search(r"\b(list|show)\b.*\b(iam|users)\b", t):
        return "list_iam_users", {}

    # Lambda
    if re.search(r"\b(invoke|call)\b.*\b(lambda)\b", t):
        m = re.search(r"(?:function\s+named|function\s+|named\s+)([A-Za-z0-9_\-]+)", t)
        return "invoke_lambda", {"function": m.group(1) if m else None, "region": region}
    if re.search(r"\b(list|show)\b.*\b(lambda|functions)\b", t):
        return "list_lambda_functions", {"region": region}

    return ("unknown", {})

def _ml_intent(text: str):
    classifier = _get_local_classifier()
    if not classifier:
        return None
    try:
        res = classifier(text, candidate_labels=INTENTS, multi_label=False)
        # bart-large-mnli returns dict with labels + scores
        labels = res.get("labels", [])
        scores = res.get("scores", [])
        if labels and scores and float(scores[0]) >= ML_CONF_THRESHOLD:
            return labels[0]
    except Exception as e:
        logger.exception("ML classification failed: %s", e)
    return None

def _haiku_intent(text: str):
    client = _get_haiku_client()
    if not client:
        return None
    try:
        prompt = f"Extract intent from this user request. Return a single label from: {', '.join(INTENTS)}. Request: {text}\nLabel:"
        resp = client.completions.create(model="claude-3-haiku", prompt=prompt, max_tokens_to_sample=32)
        lbl = resp.completion.strip().split()[0]
        if lbl in INTENTS:
            return lbl
    except Exception as e:
        logger.exception("Haiku classification failed: %s", e)
    return None

def nlp_mode_summary():
    return {"mode": NLP_MODE, "enable_ml": ENABLE_ML}

def parse_nlp(text: str) -> Tuple[str, Dict]:
    text = text.strip()
    # 1) If haiku selected, try it first
    if NLP_MODE == "haiku":
        lbl = _haiku_intent(text)
        if lbl:
            _, entities = _rule_intent_and_entities(text)
            return lbl, entities

    # 2) Local ml attempt
    if ENABLE_ML:
        lbl = _ml_intent(text)
        if lbl:
            _, entities = _rule_intent_and_entities(text)
            return lbl, entities

    # 3) fallback rules
    intent, entities = _rule_intent_and_entities(text)
    return intent, entities
