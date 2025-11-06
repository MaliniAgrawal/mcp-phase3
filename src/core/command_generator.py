# src/core/command_generator.py
# Use package-root imports (when `src` is on PYTHONPATH) — avoid importing `src.` prefix which breaks
# when running files under `src/` directly.
from config.settings import DEFAULT_REGION
from loguru import logger
from core.aws_parsers.s3_parser import parse_s3_intent
from core.aws_parsers.ec2_parser import parse_ec2_intent
from core.aws_parsers.lambda_parser import parse_lambda_intent
from core.aws_parsers.dynamodb_parser import parse_dynamodb_intent
from core.aws_parsers.iam_parser import parse_iam_intent

def list_supported_services():
    return ["s3", "ec2", "dynamodb", "iam", "lambda", "sns", "sqs", "cloudwatch", "ecs", "glue"]

def generate_command(intent: str, entities: dict):
    """Generate AWS CLI commands based on intent and entities.
    
    Args:
        intent: The classified intent string
        entities: Dict of extracted entities
        
    Returns:
        tuple: (command_str, description_str)
    """
    if "s3" in intent:
        return parse_s3_intent(intent, entities), f"S3 operation: {intent}"
    if "ec2" in intent:
        return parse_ec2_intent(intent, entities), f"EC2 operation: {intent}"
    if "lambda" in intent:
        return parse_lambda_intent(intent, entities), f"Lambda operation: {intent}"
    if "dynamodb" in intent:
        return parse_dynamodb_intent(intent, entities), f"DynamoDB operation: {intent}"
    if "iam" in intent:
        return parse_iam_intent(intent, entities), f"IAM operation: {intent}"

    return "echo 'Unknown service intent'", "Service not supported or intent unclear"

    # DynamoDB
    if intent == "create_dynamodb_table":
        table = entities.get("table") or "MyTable"
        cmd = (
            f"aws dynamodb create-table --table-name {table} "
            f"--attribute-definitions AttributeName=Id,AttributeType=S "
            f"--key-schema AttributeName=Id,KeyType=HASH "
            f"--billing-mode PAY_PER_REQUEST --region {region}"
        )
        return cmd, f"Creates a DynamoDB table named '{table}' in {region} with on-demand billing."

    if intent == "list_dynamodb_tables":
        return "aws dynamodb list-tables", "Lists DynamoDB tables."

    # EC2
    if intent == "start_ec2_instance":
        iid = entities.get("instance_id") or "<instance-id>"
        return f"aws ec2 start-instances --instance-ids {iid} --region {region}", f"Starts EC2 instance {iid} in {region}."

    if intent == "stop_ec2_instance":
        iid = entities.get("instance_id") or "<instance-id>"
        return f"aws ec2 stop-instances --instance-ids {iid} --region {region}", f"Stops EC2 instance {iid} in {region}."

    if intent == "list_ec2_instances" or intent == "describe_ec2_instances":
        return f"aws ec2 describe-instances --region {region}", f"Describes EC2 instances in {region}."

    # IAM
    if intent == "create_iam_user":
        user = entities.get("user") or "NewUser"
        return f"aws iam create-user --user-name {user}", f"Creates IAM user {user}."

    if intent == "list_iam_users":
        return "aws iam list-users", "Lists IAM users in the account."

    # Lambda
    if intent == "invoke_lambda":
        fn = entities.get("function") or "<function-name>"
        return f"aws lambda invoke --function-name {fn} out.json --cli-binary-format raw-in-base64-out", f"Invokes Lambda function '{fn}'."

    if intent == "list_lambda_functions":
        return f"aws lambda list-functions --region {region}", f"Lists Lambda functions in {region}."

    # Placeholder for other services (SNS, SQS, ECS, Glue) - add as needed
    logger.warning("Unsupported intent: %s", intent)
    return "echo 'Unsupported intent'", "Intent not supported by Phase 3 skeleton."
