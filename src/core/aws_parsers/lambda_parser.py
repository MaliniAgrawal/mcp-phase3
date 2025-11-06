def parse_lambda_intent(intent: str, entities: dict) -> str:
    """Generate AWS CLI for Lambda-related intents."""
    function = entities.get("function") or entities.get("function_name", "my-function")
    region = entities.get("region", "us-east-1")

    if "list" in intent:
        return f"aws lambda list-functions --region {region}"

    if "invoke" in intent:
        return f"aws lambda invoke --function-name {function} response.json --region {region}"

    if "create" in intent:
        return (
            f"aws lambda create-function --function-name {function} "
            "--runtime python3.9 --role arn:aws:iam::123456789012:role/lambda-role "
            "--handler lambda_function.lambda_handler --zip-file fileb://function.zip "
            f"--region {region}"
        )

    return "echo 'Unknown Lambda intent'"
