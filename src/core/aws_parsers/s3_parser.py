def parse_s3_intent(intent: str, entities: dict) -> str:
    """Generate AWS CLI for S3-related intents."""
    region = entities.get("region", "us-east-1")
    bucket = entities.get("bucket") or entities.get("bucket_name", "my-bucket")

    if "create" in intent:
        return f"aws s3api create-bucket --bucket {bucket} --region {region}"

    if "delete" in intent:
        return f"aws s3api delete-bucket --bucket {bucket}"

    if "list" in intent:
        return "aws s3api list-buckets"

    if "upload" in intent:
        file = entities.get("file_name", "file.txt")
        return f"aws s3 cp {file} s3://{bucket}/"

    if "download" in intent:
        file = entities.get("file_name", "file.txt")
        return f"aws s3 cp s3://{bucket}/{file} ."

    return "echo 'Unknown S3 intent'"
