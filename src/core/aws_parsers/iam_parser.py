def parse_iam_intent(intent: str, entities: dict) -> str:
    """Generate AWS CLI for IAM-related intents."""
    user = entities.get("username") or entities.get("user_name", "TestUser")

    if "list" in intent:
        return "aws iam list-users"

    if "create" in intent:
        return f"aws iam create-user --user-name {user}"

    if "delete" in intent:
        return f"aws iam delete-user --user-name {user}"

    return "echo 'Unknown IAM intent'"
