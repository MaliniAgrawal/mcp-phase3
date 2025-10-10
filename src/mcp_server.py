# src/mcp_server.py
import asyncio
from loguru import logger
from fastmcp import FastMCP

from core.nlp_utils import parse_nlp
from core.command_generator import generate_command, list_supported_services
from core.aws_validator import validate_command_safe
import sys
import os

if os.getenv("DEBUG", "false").lower() == "true":
    logger.add(sys.stderr, level="DEBUG")
else:
    logger.add(sys.stderr, level="INFO")
     
# Send logs to stderr only (safe for MCP JSON stdio)
logger.remove()
logger.add(sys.stderr, level="INFO")

mcp = FastMCP("aws-cli-generator")

@mcp.tool()
async def generate_aws_cli(query: str) -> dict:
    """
    Generate AWS CLI + explanation + validation for supported services.
    """
    logger.info("Received query: %s", query)
    intent, entities = parse_nlp(query)

    command, explanation = generate_command(intent, entities)

    # validation is safe (handles missing creds)
    validation = validate_command_safe(intent, entities)

    return {
        "command": command,
        "explanation": explanation,
        "validation": validation,
    }

@mcp.tool()
async def health_check() -> dict:
    return {"status": "ok", "message": "aws-cli-generator (phase-2.5) ready."}

@mcp.tool()
async def list_supported_services() -> dict:
    return {"services": list_supported_services()}

async def main():
    logger.info("Starting MCP stdio server (aws-cli-generator-phase2.5)")
    await mcp.run_stdio_async()

if __name__ == "__main__":
    asyncio.run(main())
