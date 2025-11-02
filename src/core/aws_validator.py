# src/core/validator.py
import boto3
import botocore
from loguru import logger
from src.config.settings import DEFAULT_REGION

def _session_client(service: str, region: str):
    sess = boto3.Session()
    return sess.client(service, region_name=region)

def validate_command_safe(intent: str, entities: dict) -> dict:
    region = entities.get("region") or DEFAULT_REGION
    result = {"intent": intent, "region": region, "status": "unknown", "reason": None, "detail": {}}

    try:
        if intent == "create_s3_bucket":
            s3 = _session_client("s3", region)
            bucket = entities.get("bucket")
            if not bucket:
                result.update(status="unknown", reason="No bucket name provided.")
                return result
            try:
                s3.head_bucket(Bucket=bucket)
                result.update(status="invalid", reason=f"Bucket '{bucket}' already exists.")
            except botocore.exceptions.ClientError as e:
                err = e.response.get("Error", {}).get("Code", "")
                if err in ("404", "NoSuchBucket", "NotFound"):
                    result.update(status="valid", reason="Bucket name available.")
                else:
                    result.update(status="invalid", reason=f"{err}")
            return result

        if intent == "list_s3_buckets":
            s3 = _session_client("s3", region)
            buckets = [b["Name"] for b in s3.list_buckets().get("Buckets", [])]
            result.update(status="valid", reason="Listed buckets", detail={"buckets": buckets})
            return result

        if intent in ("describe_ec2_instances", "list_ec2_instances"):
            ec2 = _session_client("ec2", region)
            reservations = ec2.describe_instances().get("Reservations", [])
            instances = []
            for r in reservations:
                for inst in r.get("Instances", []):
                    instances.append({
                        "InstanceId": inst.get("InstanceId"),
                        "State": inst.get("State", {}).get("Name"),
                        "Tags": inst.get("Tags", [])
                    })
            result.update(status="valid", reason="Listed instances", detail={"instances": instances})
            return result

        if intent in ("create_dynamodb_table", "list_dynamodb_tables"):
            dynamodb = _session_client("dynamodb", region)
            if intent == "list_dynamodb_tables":
                tables = dynamodb.list_tables().get("TableNames", [])
                result.update(status="valid", reason="Listed tables", detail={"tables": tables})
                return result
            table = entities.get("table")
            if not table:
                result.update(status="unknown", reason="No table name provided.")
                return result
            tables = dynamodb.list_tables().get("TableNames", [])
            if table in tables:
                result.update(status="invalid", reason=f"Table '{table}' already exists.")
            else:
                result.update(status="valid", reason="Table name available.")
            return result

        if intent in ("start_ec2_instance", "stop_ec2_instance", "list_ec2_instances"):
            ec2 = _session_client("ec2", region)
            if intent == "list_ec2_instances":
                # return basic instance id + state + tags
                reservations = ec2.describe_instances().get("Reservations", [])
                instances = []
                for r in reservations:
                    for inst in r.get("Instances", []):
                        instances.append({
                            "InstanceId": inst.get("InstanceId"),
                            "State": inst.get("State", {}).get("Name"),
                            "Tags": inst.get("Tags", [])
                        })
                result.update(status="valid", reason="Listed instances", detail={"instances": instances})
                return result
            iid = entities.get("instance_id")
            if not iid:
                result.update(status="unknown", reason="No instance id provided.")
                return result
            try:
                resp = ec2.describe_instances(InstanceIds=[iid]).get("Reservations", [])
                if resp:
                    # get current state
                    state = resp[0]["Instances"][0].get("State", {}).get("Name")
                    result.update(status="valid", reason=f"Instance {iid} exists and is {state}", detail={"state": state})
                else:
                    result.update(status="invalid", reason=f"Instance {iid} not found.")
            except botocore.exceptions.ClientError as e:
                result.update(status="error", reason=str(e))
            return result

        if intent in ("create_iam_user", "list_iam_users"):
            iam = _session_client("iam", region)
            if intent == "list_iam_users":
                users = iam.list_users().get("Users", [])
                result.update(status="valid", reason="Listed users", detail={"users": [u["UserName"] for u in users]})
                return result
            user = entities.get("user")
            if not user:
                result.update(status="unknown", reason="No user provided.")
                return result
            try:
                iam.get_user(UserName=user)
                result.update(status="invalid", reason=f"User '{user}' already exists.")
            except botocore.exceptions.ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                if code in ("NoSuchEntity", "NoSuchEntityException"):
                    result.update(status="valid", reason="User does not exist; name available.")
                else:
                    result.update(status="error", reason=str(e))
            return result

        if intent in ("invoke_lambda", "list_lambda_functions"):
            lam = _session_client("lambda", region)
            if intent == "list_lambda_functions":
                funcs = lam.list_functions().get("Functions", [])
                result.update(status="valid", reason="Listed functions", detail={"functions": [f["FunctionName"] for f in funcs]})
                return result
            fn = entities.get("function")
            if not fn:
                result.update(status="unknown", reason="No function name provided.")
                return result
            try:
                lam.get_function(FunctionName=fn)
                result.update(status="valid", reason=f"Function '{fn}' exists.")
            except botocore.exceptions.ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                if code in ("ResourceNotFoundException", "ResourceNotFound"):
                    result.update(status="invalid", reason=f"Function '{fn}' not found.")
                else:
                    result.update(status="error", reason=str(e))
            return result
        # ... (as in phase-2.5 validator)
        result.update(status="unsupported", reason="Validation not implemented for this intent")
        return result

    except botocore.exceptions.NoCredentialsError:
        result.update(status="unknown", reason="AWS credentials not configured.")
        return result
    except Exception as e:
        logger.exception("Validation error: %s", e)
        result.update(status="error", reason=str(e))
        return result
