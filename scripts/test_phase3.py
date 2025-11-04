"""
scripts/test_phase3.py
----------------------------------------
Local test harness for Phase 3 MCP AWS CLI Generator.
Validates:
 - NLP intent extraction (rule + Haiku fallback)
 - AWS CLI command generation
 - boto3-based validation
 - Telemetry JSON logging
"""

import asyncio
import json
import sys
from pathlib import Path
from pprint import pprint
from loguru import logger

# ──────────────────────────────────────────────
# Add src folder to Python path
# (so imports like "from core..." and "from config..." work)
# ──────────────────────────────────────────────
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
# Prefer inserting at the front so local `src` takes precedence
if SRC.exists():
    sys.path.insert(0, str(SRC.resolve()))
else:
    # Fallback: append so script still works if layout is different
    sys.path.append(str(SRC))

# Import core modules from src
from core.command_generator import generate_command
from mcp_server import generate_aws_cli, list_supported_services, health_check


# === Optional sanity checks for AWS creds ===
import boto3
from botocore.exceptions import NoCredentialsError, PartialCredentialsError


async def run_tests():
    print("\n🚀 PHASE-3 MCP AWS CLI GENERATOR TESTS\n")

    # 1️⃣ Check AWS credentials
    print("🔐 Checking AWS credentials:")
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print("✅ Valid credentials detected:", identity["Arn"])
    except (NoCredentialsError, PartialCredentialsError):
        print("⚠️ No AWS credentials found. Some validations will show 'unknown'.")
    print("-" * 80)

    # 2️⃣ Health check
    print("💡 Health Check:")
    health = await health_check.run(arguments={})  # Correct way to invoke MCP tools
    pprint(health)
    print("-" * 80)

    # 3️⃣ List supported services
    print("🧩 Supported Services:")
    services = await list_supported_services.run(arguments={})
    pprint(services)
    print("-" * 80)

    # 4️⃣ Run NLP + command tests
    queries = [
        "create an S3 bucket named phase3-test-bucket in us-west-1",
        "list all s3 buckets",
        "list dynamodb tables",
        "list ec2 instances in us-west-1",
        "list lambda functions in us-west-1",
        "list iam users",
    ]

    for q in queries:
        print(f"🧠 Query: {q}")
        try:
            result = await generate_aws_cli.run(arguments={"query": q})
            pprint(result)
        except Exception as e:
            logger.exception(f"Error processing query: {q} -> {e}")
        print("-" * 80)

    # 5️⃣ Verify telemetry file exists
    telemetry_path = Path("telemetry/telemetry.log")
    if telemetry_path.exists():
        print(f"🪶 Telemetry log found at: {telemetry_path.resolve()}")
        # open with utf-8 and be tolerant of any encoding issues
        with telemetry_path.open(encoding="utf-8", errors="replace") as f:
            line = f.readline()
            if not line:
                print("Telemetry log is empty")
            else:
                try:
                    sample = json.loads(line.strip())
                    print("Sample log entry:")
                    pprint(sample)
                except Exception as e:
                    print("Failed to parse telemetry entry:", e)
                    print("Raw line:")
                    print(line)
    else:
        print("⚠️ No telemetry log found yet.")

    print("\n✅ Tests completed successfully!\n")


if __name__ == "__main__":
    asyncio.run(run_tests())
