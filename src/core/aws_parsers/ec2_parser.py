def parse_ec2_intent(intent: str, entities: dict) -> str:
    """Generate AWS CLI for EC2-related intents."""
    region = entities.get("region", "us-east-1")
    instance_id = entities.get("instance_id", "i-1234567890abcdef")

    if "list" in intent or "describe" in intent:
        return f"aws ec2 describe-instances --region {region}"

    if "start" in intent:
        return f"aws ec2 start-instances --instance-ids {instance_id} --region {region}"

    if "stop" in intent:
        return f"aws ec2 stop-instances --instance-ids {instance_id} --region {region}"

    if "terminate" in intent:
        return f"aws ec2 terminate-instances --instance-ids {instance_id} --region {region}"

    return "echo 'Unknown EC2 intent'"
