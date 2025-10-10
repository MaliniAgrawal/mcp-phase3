# src/core/nlp_utils.py
import os
import re
import logging
from typing import Tuple, Dict

logger = logging.getLogger("nlp_utils")
ENABLE_ML = os.getenv("ENABLE_ML", "true").lower() in ("1", "true", "yes")
ML_CONF_THRESHOLD = float(os.getenv("ML_CONF_THRESHOLD", "0.7"))

# Lazy classifier
_classifier = None
def _get_classifier():
    global _classifier
    if _classifier is not None:
        return _classifier
    if not ENABLE_ML:
        return None
    try:
        from transformers import pipeline
        # lightweight model; good enough for coarse intent classification
        _classifier = pipeline("zero-shot-classification", model="facebook/bart-large-mnli")
        logger.info("ML classifier initialized.")
    except Exception as e:
        logger.exception("Failed to initialize ML classifier: %s", e)
        _classifier = None
    return _classifier

# Intents we support
INTENTS = [
    "create_s3_bucket",
    "list_s3_buckets",
    "create_dynamodb_table",
    "list_dynamodb_tables",
    "start_ec2_instance",
    "stop_ec2_instance",
    "list_ec2_instances",
    "describe_ec2_instances",
    "create_iam_user",
    "list_iam_users",
    "invoke_lambda",
    "list_lambda_functions",
    "unknown"
]

def _rule_intent_and_entities(text: str) -> Tuple[str, Dict]:
    t = text.lower()

    # region detection
    r = re.search(r"(?:in\s+|region\s+)(us-[a-z0-9-]+)", t)
    region = r.group(1) if r else None

    # S3 create / list
    if re.search(r"\b(create|make|make an|create an)\b.*\bs3\b|\bbucket\b", t):
        m = re.search(r"(?:named|called|name(?:d)?|bucket\s+named|bucket\s+)([a-z0-9][a-z0-9\-\.]{2,62})", t)
        bucket = m.group(1) if m else None
        return ("create_s3_bucket", {"bucket": bucket, "region": region})

    if re.search(r"\b(list|show)\b.*\b(s3|buckets)\b", t):
        return ("list_s3_buckets", {"region": region})

    # DynamoDB
    if re.search(r"\b(create|make)\b.*\b(dynamo|dynamodb|table)\b", t):
        m = re.search(r"(?:table\s+named|table\s+)([A-Za-z0-9_\-]+)", t)
        table = m.group(1) if m else None
        return ("create_dynamodb_table", {"table": table, "region": region})

    if re.search(r"\b(list|show)\b.*\b(dynamo|dynamodb|tables)\b", t):
        return ("list_dynamodb_tables", {"region": region})

    # EC2
    m_start = re.search(r"\b(start|run)\b.*\b(ec2|instance)\b.*\b(i-[0-9a-fA-F]+)\b", t)
    if m_start:
        return ("start_ec2_instance", {"instance_id": m_start.group(3), "region": region})
    m_stop = re.search(r"\b(stop|terminate)\b.*\b(ec2|instance)\b.*\b(i-[0-9a-fA-F]+)\b", t)
    if m_stop:
        return ("stop_ec2_instance", {"instance_id": m_stop.group(3), "region": region})
    # describe (single or all) EC2 instances
    m_describe_single = re.search(r"\b(describe|show|get)\b.*\b(ec2|instance|instances)\b.*\b(i-[0-9a-fA-F]+)\b", t)
    if m_describe_single:
        return ("describe_ec2_instances", {"instance_id": m_describe_single.group(3), "region": region})
    if re.search(r"\b(describe|show|get)\b.*\b(ec2|instances)\b", t):
        # optional tag filter
        m_tag = re.search(r"tag\s+([A-Za-z0-9\-_]+)=([A-Za-z0-9\-_]+)", t)
        tag = {m_tag.group(1): m_tag.group(2)} if m_tag else None
        return ("describe_ec2_instances", {"region": region, "tag": tag})
    if re.search(r"\b(list|show)\b.*\b(ec2|instances)\b", t):
        # optional tag filter
        m_tag = re.search(r"tag\s+([A-Za-z0-9\-_]+)=([A-Za-z0-9\-_]+)", t)
        tag = {m_tag.group(1): m_tag.group(2)} if m_tag else None
        return ("list_ec2_instances", {"region": region, "tag": tag})

    # IAM
    if re.search(r"\b(create|add)\b.*\b(iam|user)\b", t):
        m = re.search(r"(?:user\s+named|user\s+)([A-Za-z0-9_\-]+)", t)
        user = m.group(1) if m else None
        return ("create_iam_user", {"user": user})
    if re.search(r"\b(list|show)\b.*\b(iam|users)\b", t):
        return ("list_iam_users", {})

    # Lambda
    if re.search(r"\b(invoke|call)\b.*\b(lambda)\b", t):
        m = re.search(r"(?:function\s+named|function\s+|named\s+)([A-Za-z0-9_\-]+)", t)
        fn = m.group(1) if m else None
        return ("invoke_lambda", {"function": fn, "region": region})
    if re.search(r"\b(list|show)\b.*\b(lambda|functions)\b", t):
        return ("list_lambda_functions", {"region": region})

    return ("unknown", {})

def parse_nlp(text: str) -> Tuple[str, Dict]:
    """
    Try ML intent classification first (if enabled), otherwise fallback to rule-based function.
    """
    text = text.strip()
    clf = _get_classifier()
    if clf:
        try:
            res = clf(text, candidate_labels=INTENTS, multi_label=False)
            if res and res.get("scores"):
                top = res["labels"][0]
                score = float(res["scores"][0])
                logger.info("ML intent=%s score=%.3f", top, score)
                if score >= ML_CONF_THRESHOLD and top != "unknown":
                    # use ML label but still extract entities with rules (quick)
                    _, entities = _rule_intent_and_entities(text)
                    return top, entities
        except Exception as e:
            logger.exception("ML classification failed: %s", e)

    # Fallback to rules
    intent, entities = _rule_intent_and_entities(text)
    logger.info("Rule intent=%s entities=%s", intent, entities)
    return intent, entities
