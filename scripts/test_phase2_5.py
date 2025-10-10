"""
scripts/test_phase2_5.py
------------------------------------
Smoke test for the Phase-2.5 MCP AWS CLI Generator.
Runs core command generation and validation logic directly (no MCP protocol).
"""

import sys
from pathlib import Path
from pprint import pprint

# Add project src to path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))

from core.command_generator import generate_command
from core.nlp_utils import parse_nlp


def run_tests():
    print("\n🚀 PHASE-2.5 MCP AWS CLI GENERATOR TESTS\n")

    queries = [
        "list all s3 buckets in us-west-1",
        "list dynamodb tables in us-west-1",
        "describe ec2 instances in us-west-1",
        "list lambda functions in us-west-1",
        "list iam users",
        "create an s3 bucket named phase25-test-bucket in us-west-1",
    ]

    for query in queries:
        print(f"\n🧠 Query: {query}")
        try:
            intent, entities = parse_nlp(query)
            print("Parsed intent:", intent, "| Entities:", entities)

            # Call sync generator
            command, explanation = generate_command(intent, entities)

            pprint({
                "command": command,
                "explanation": explanation
            })

        except Exception as e:
            print(f"❌ Error: {e}")

        print("-" * 80)

    print("\n✅ Done! (If AWS creds missing, validation.status='unknown')")


if __name__ == "__main__":
    run_tests()
