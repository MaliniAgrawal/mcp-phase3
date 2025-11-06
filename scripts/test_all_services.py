"""Test all AWS services command generation and validation."""
import sys
from pathlib import Path
from pprint import pprint

# Add src folder to Python path
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if SRC.exists():
    sys.path.insert(0, str(SRC.resolve()))

from core.aws_parsers.s3_parser import parse_s3_intent
from core.aws_parsers.ec2_parser import parse_ec2_intent
from core.aws_parsers.lambda_parser import parse_lambda_intent
from core.aws_parsers.dynamodb_parser import parse_dynamodb_intent
from core.aws_parsers.iam_parser import parse_iam_intent
from core.aws_validator import validate_command_safe

def test_service_command(service, intent, entities):
    print(f"\n{'='*80}")
    print(f"Testing {service.upper()} Service")
    print(f"Intent: {intent}")
    print(f"Entities: {entities}")
    print(f"{'-'*80}")
    
    # Get the appropriate parser function
    parser_funcs = {
        's3': parse_s3_intent,
        'ec2': parse_ec2_intent,
        'lambda': parse_lambda_intent,
        'dynamodb': parse_dynamodb_intent,
        'iam': parse_iam_intent
    }
    
    parser = parser_funcs.get(service)
    if not parser:
        print(f"No parser found for service: {service}")
        return
    
    # Generate command
    command = parser(intent, entities)
    print(f"\nCommand generated: {command}")
    
    # Validate command
    validation = validate_command_safe(intent, entities)
    print(f"\nValidation result:")
    print(f"Status: {validation.get('status')}")
    print(f"Details: {validation.get('details')}")
    print(f"Risk level: {validation.get('risk_level')}")

def run_all_tests():
    # Test cases for each service
    test_cases = [
        # S3 Tests
        {
            'service': 's3',
            'intent': 'create_s3_bucket',
            'entities': {'bucket': 'phase3-test-bucket', 'region': 'us-west-1'}
        },
        {
            'service': 's3',
            'intent': 'list_s3_buckets',
            'entities': {}
        },
        
        # EC2 Tests
        {
            'service': 'ec2',
            'intent': 'list_ec2_instances',
            'entities': {'region': 'us-west-1'}
        },
        {
            'service': 'ec2',
            'intent': 'start_ec2_instance',
            'entities': {'instance_id': 'i-1234567890abcdef0', 'region': 'us-west-1'}
        },
        
        # Lambda Tests
        {
            'service': 'lambda',
            'intent': 'list_lambda_functions',
            'entities': {'region': 'us-west-1'}
        },
        {
            'service': 'lambda',
            'intent': 'invoke_lambda',
            'entities': {'function_name': 'test-function', 'region': 'us-west-1'}
        },
        
        # DynamoDB Tests
        {
            'service': 'dynamodb',
            'intent': 'list_dynamodb_tables',
            'entities': {}
        },
        {
            'service': 'dynamodb',
            'intent': 'create_dynamodb_table',
            'entities': {'table': 'test-table', 'region': 'us-west-1'}
        },
        
        # IAM Tests
        {
            'service': 'iam',
            'intent': 'list_iam_users',
            'entities': {}
        },
        {
            'service': 'iam',
            'intent': 'create_iam_user',
            'entities': {'user_name': 'test-user'}
        }
    ]
    
    for test in test_cases:
        test_service_command(
            test['service'],
            test['intent'],
            test['entities']
        )

if __name__ == "__main__":
    print("\n🚀 Testing All AWS Services Command Generation and Validation\n")
    
    # Test AWS credentials
    import boto3
    from botocore.exceptions import NoCredentialsError, PartialCredentialsError
    
    print("🔐 Checking AWS credentials:")
    try:
        sts = boto3.client("sts")
        identity = sts.get_caller_identity()
        print("✅ Valid credentials detected:", identity["Arn"])
    except (NoCredentialsError, PartialCredentialsError):
        print("⚠️ No AWS credentials found. Some validations will show 'unknown'.")
    
    run_all_tests()