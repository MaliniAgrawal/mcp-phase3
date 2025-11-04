"""Centralized secret retrieval helpers.

Strategy:
- First check environment variables (fast, works in dev and CI).
- If not found and an AWS Secrets Manager secret name is configured via
  ANTHROPIC_SECRET_NAME (or a generic secret name env var), try Secrets Manager.
- Cache retrieved secrets in-memory for the process lifetime.

Usage:
    from config.secrets import get_secret
    key = get_secret("ANTHROPIC_API_KEY")

Notes:
- Do NOT log secret values. Only log presence / failures.
- For local dev use .env or set ANTHROPIC_API_KEY in the environment.
"""
from __future__ import annotations

import json
import os
import logging
from typing import Optional

_logger = logging.getLogger(__name__)
_CACHE: dict[str, str] = {}

try:
    import boto3
    from botocore.exceptions import ClientError
except Exception:  # boto3 optional
    boto3 = None  # type: ignore
    ClientError = Exception  # type: ignore


def _get_from_env(key: str) -> Optional[str]:
    v = os.getenv(key)
    if v:
        _logger.debug("Secret %s found in environment", key)
    return v


def _get_from_aws(secret_name: str, key: Optional[str] = None, region: Optional[str] = None) -> Optional[str]:
    """Fetch a secret from AWS Secrets Manager.

    secret_name: the name or ARN of the secret stored in Secrets Manager.
    key: if the secret is a JSON object, return secret[key]. If None, return whole string.
    region: optional AWS region override.
    """
    if not boto3:
        _logger.debug("boto3 not available; skipping AWS Secrets Manager lookup")
        return None

    try:
        client = boto3.client("secretsmanager", region_name=region) if region else boto3.client("secretsmanager")
        resp = client.get_secret_value(SecretId=secret_name)
        secret_string = resp.get("SecretString")
        if secret_string:
            # The secret may be plain text or a JSON object
            try:
                parsed = json.loads(secret_string)
                if key:
                    return parsed.get(key)
                # if no key requested, return raw string
                return secret_string
            except json.JSONDecodeError:
                # Not JSON — return raw string (or None if key requested)
                return secret_string if key is None else None
        # If secret stored as binary, return None (not handled here)
        _logger.warning("Secret %s returned no SecretString; binary secrets not supported", secret_name)
        return None
    except ClientError as e:
        _logger.warning("Unable to read secret %s from AWS Secrets Manager: %s", secret_name, e)
        return None


def get_secret(key_name: str, *, aws_secret_name_env: str = "ANTHROPIC_SECRET_NAME", aws_region_env: str = "AWS_DEFAULT_REGION") -> Optional[str]:
    """Get a secret by key name.

    Order of lookup:
    1. Direct environment variable with the same name (e.g. ANTHROPIC_API_KEY)
    2. If env var named by `aws_secret_name_env` is set, attempt to fetch it from AWS Secrets Manager

    Returns the secret string or None if not found.
    """
    if key_name in _CACHE:
        return _CACHE[key_name]

    # 1. env var
    val = _get_from_env(key_name)
    if val:
        _CACHE[key_name] = val
        return val

    # 2. AWS Secrets Manager (expects the secret itself to be either a JSON dict containing the key
    #     or the secret string when key_name is None / not required).
    secret_name = os.getenv(aws_secret_name_env)
    if secret_name:
        region = os.getenv(aws_region_env)
        val = _get_from_aws(secret_name, key=key_name, region=region)
        if val:
            _CACHE[key_name] = val
            return val

    _logger.debug("Secret %s not found (env and AWS Secrets Manager)", key_name)
    return None


def clear_cache() -> None:
    """Clear in-process secret cache (useful for tests)."""
    _CACHE.clear()
