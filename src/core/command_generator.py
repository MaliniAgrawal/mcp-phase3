# src/core/command_generator.py
from config.settings import DEFAULT_REGION
from loguru import logger

def list_supported_services():
    return ["s3", "ec2", "dynamodb", "iam", "lambda"]

def generate_command(intent: str, entities: dict) -> tuple[str, str]:
    region = entities.get("region") or DEFAULT_REGION

    # S3
    if intent == "create_s3_bucket":
        bucket = entities.get("bucket") or "my-bucket"
        cmd = f"aws s3 mb s3://{bucket} --region {region}"
        explanation = f"Creates an S3 bucket named '{bucket}' in region {region}."
        return cmd, explanation

    if intent == "list_s3_buckets":
        cmd = "aws s3 ls"
        explanation = "Lists S3 buckets in your account (global)."
        return cmd, explanation

    # DynamoDB
    if intent == "create_dynamodb_table":
        table = entities.get("table") or "MyTable"
        cmd = (
            f"aws dynamodb create-table --table-name {table} "
            f"--attribute-definitions AttributeName=Id,AttributeType=S "
            f"--key-schema AttributeName=Id,KeyType=HASH "
            f"--billing-mode PAY_PER_REQUEST --region {region}"
        )
        explanation = f"Creates a DynamoDB table named '{table}' in {region} with on-demand billing."
        return cmd, explanation

    if intent == "list_dynamodb_tables":
        cmd = "aws dynamodb list-tables"
        explanation = "Lists DynamoDB tables in the account/region."
        return cmd, explanation

    # EC2
    if intent == "start_ec2_instance":
        iid = entities.get("instance_id") or "<instance-id>"
        cmd = f"aws ec2 start-instances --instance-ids {iid} --region {region}"
        explanation = f"Starts EC2 instance {iid} in {region}."
        return cmd, explanation

    if intent == "stop_ec2_instance":
        iid = entities.get("instance_id") or "<instance-id>"
        cmd = f"aws ec2 stop-instances --instance-ids {iid} --region {region}"
        explanation = f"Stops EC2 instance {iid} in {region}."
        return cmd, explanation

    if intent == "describe_ec2_instances":
        # If instance_id present, describe that instance; otherwise describe all (optionally filter by tag)
        iid = entities.get("instance_id")
        tag = entities.get("tag")
        if iid:
            cmd = f"aws ec2 describe-instances --instance-ids {iid} --region {region}"
            explanation = f"Describes EC2 instance {iid} in {region}, including state and tags."
            return cmd, explanation
        if tag:
            # simple tag filter: --filters Name=tag:Key,Values=Value
            k, v = next(iter(tag.items()))
            cmd = f"aws ec2 describe-instances --filters Name=tag:{k},Values={v} --region {region}"
            explanation = f"Describes EC2 instances in {region} filtered by tag {k}={v}."
            return cmd, explanation
        cmd = f"aws ec2 describe-instances --region {region}"
        explanation = f"Describes all EC2 instances in {region}, including IDs, states, and tags."
        return cmd, explanation

    if intent == "list_ec2_instances":
        cmd = f"aws ec2 describe-instances --query 'Reservations[*].Instances[*].[InstanceId,State.Name,Tags]' --region {region}"
        explanation = f"Lists EC2 instances in {region} with IDs, state, and tags."
        return cmd, explanation

    # IAM
    if intent == "create_iam_user":
        user = entities.get("user") or "NewUser"
        cmd = f"aws iam create-user --user-name {user}"
        explanation = f"Creates an IAM user named {user}."
        return cmd, explanation

    if intent == "list_iam_users":
        cmd = "aws iam list-users"
        explanation = "Lists IAM users in the account."
        return cmd, explanation

    # Lambda
    if intent == "invoke_lambda":
        fn = entities.get("function") or entities.get("functionname") or "<function-name>"
        cmd = f"aws lambda invoke --function-name {fn} out.json --cli-binary-format raw-in-base64-out"
        explanation = f"Invokes Lambda function '{fn}' and writes result to out.json."
        return cmd, explanation

    if intent == "list_lambda_functions":
        cmd = f"aws lambda list-functions --region {region}"
        explanation = f"Lists Lambda functions in {region}."
        return cmd, explanation

    logger.warning("Unsupported intent: %s", intent)
    return "echo 'Unsupported intent'", "Intent not supported by Phase 2.5"
