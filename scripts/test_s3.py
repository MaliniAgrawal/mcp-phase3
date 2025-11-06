"""Test S3 command generation and validation directly."""
import sys
from pathlib import Path

# Add src folder to Python path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC.resolve()))

from core.aws_parsers.s3_parser import parse_s3_intent
from core.aws_validator import validate_command_safe

def test_s3_command():
    # Test create bucket
    intent = "create_s3_bucket"
    entities = {
        "bucket": "phase3-test-bucket",
        "region": "us-west-1"
    }
    
    command = parse_s3_intent(intent, entities)
    print(f"\nCommand generated: {command}")
    
    validation = validate_command_safe(intent, entities)
    print(f"\nValidation result:")
    print(f"Status: {validation.get('status')}")
    print(f"Details: {validation.get('details')}")
    print(f"Risk level: {validation.get('risk_level')}")

if __name__ == "__main__":
    test_s3_command()