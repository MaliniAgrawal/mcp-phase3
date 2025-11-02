# src/mcp_server.py
import argparse
import asyncio
import os
import sys
from loguru import logger
import json

USE_HAIKU = bool(os.getenv("USE_HAIKU", "false").lower() in ["true", "1", "yes"])


# ensure src on path (if running from repo root)
sys.path.insert(0, os.path.dirname(__file__))

from fastmcp import FastMCP

from core.nlp_utils import parse_nlp, nlp_mode_summary
from core.command_generator import generate_command, list_supported_services
from core.aws_validator import validate_command_safe
from core.telemetry import telemetry_log_event

# ensure logs go to stderr and file (telemetry.log)
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("telemetry/telemetry.log", rotation="10 MB", serialize=True, retention="30 days", level="INFO")

mcp = FastMCP("aws-cli-generator")

# Tool: generate aws cli
@mcp.tool()
async def generate_aws_cli(query: str):
    from core.nlp_utils import parse_nlp
    from core.command_generator import generate_command
    # parse_nlp is a synchronous helper that returns (intent, entities)
    intent, entities = parse_nlp(query)

    # generate_command is synchronous and returns (command, explanation)
    command, explanation = generate_command(intent, entities)
    validation = validate_command_safe(intent, entities)

    response = {"command": command, "explanation": explanation, "validation": validation}
    telemetry_log_event("response.emitted", {"result_summary": {"intent": intent, "status": validation.get("status")}})
    return response

@mcp.tool()
async def health_check():
    return {"status": "ok", "model": "haiku" if USE_HAIKU else "local-transformer"}

@mcp.tool()
async def list_supported_services():
    return ["s3", "dynamodb", "ec2", "lambda", "iam"]

async def run_stdio():
    logger.info("Starting MCP stdio server")
    await mcp.run_stdio_async()

def run_http():
    # lazy import to avoid bringing FastAPI when running stdio-only
    from http_adapter import app, run_http_app
    run_http_app(app)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--http", action="store_true", help="Start HTTP adapter instead of stdio")
    args = parser.parse_args()

    if args.http:
        run_http()
    else:
        asyncio.run(run_stdio())

if __name__ == "__main__":
    main()
    __all__ = ["generate_aws_cli", "list_supported_services", "health_check"]

