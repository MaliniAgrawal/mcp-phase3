# src/core/command_generator.py
from src.config.settings import DEFAULT_REGION
from loguru import logger

def list_supported_services():
    return ["s3", "ec2", "dynamodb", "iam", "lambda", "sns", "sqs", "cloudwatch", "ecs", "glue"]

def generate_command(intent: str, entities: dict):
    region = entities.get("region") or DEFAULT_REGION

    # S3
    if intent == "create_s3_bucket":
        bucket = entities.get("bucket") or "my-bucket"
        cmd = f"aws s3 mb s3://{bucket} --region {region}"
        return cmd, f"Creates an S3 bucket named '{bucket}' in {region}."

    if intent == "list_s3_buckets":
        return "aws s3 ls", "Lists S3 buckets in your account."

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
