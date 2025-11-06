def parse_dynamodb_intent(intent: str, entities: dict) -> str:
    """Generate AWS CLI for DynamoDB-related intents."""
    table = entities.get("table") or entities.get("table_name", "MyTable")
    region = entities.get("region", "us-east-1")

    if "list" in intent:
        return f"aws dynamodb list-tables --region {region}"

    if "create" in intent:
        return (
            f"aws dynamodb create-table --table-name {table} "
            "--attribute-definitions AttributeName=Id,AttributeType=S "
            "--key-schema AttributeName=Id,KeyType=HASH "
            "--provisioned-throughput ReadCapacityUnits=5,WriteCapacityUnits=5 "
            f"--region {region}"
        )

    if "delete" in intent:
        return f"aws dynamodb delete-table --table-name {table}"

    return "echo 'Unknown DynamoDB intent'"
