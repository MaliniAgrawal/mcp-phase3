
# MCP AWS CLI Generator (Phase 2.5)

Small utility that converts natural-language intents into AWS CLI commands. This repo contains a lightweight rule+ML-based intent parser and an AWS CLI command generator for common services (S3, EC2, DynamoDB, IAM, Lambda).

## Requirements

- Python 3.10+ (project used Python 3.11 in development)
- pip
- Optional: `transformers` package if you want ML-based intent classification (controlled by `ENABLE_ML` env var)

## Setup (Windows / PowerShell)

1. Create and activate a virtual environment (recommended):

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
```

2. Install dependencies:

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

3. (Optional) For development/test dependencies:

```powershell
pip install -r requirements-dev.txt
```

4. If you want to enable the ML classifier, install `transformers` and a backend like `torch` (this can be heavy):

```powershell
pip install transformers[torch]
```

Set environment variables in PowerShell if desired:

```powershell
$env:ENABLE_ML = 'true'       # or 'false'
$env:ML_CONF_THRESHOLD = '0.7'
```

## Running the project

There is a simple entry point in `src/main.py`. You can run it directly for quick manual tests:

```powershell
python -m src.main
```

Or use the server module `mcp_server` for a small HTTP API (if implemented):

```powershell
python -m src.mcp_server
```

## Tests

Run the unit tests with pytest:

```powershell
pytest -q
```

If you only want to run a specific test file, for example for the command generator:

```powershell
pytest -q tests/test_command_generator.py
```

## Usage examples

The parser accepts plain English. Examples and the resulting generated AWS CLI command:

- "Describe EC2 instances in us-west-2"
	- CLI: `aws ec2 describe-instances --region us-west-2`

- "Describe instance i-0abc1234 in us-east-1"
	- CLI: `aws ec2 describe-instances --instance-ids i-0abc1234 --region us-east-1`

- "Start instance i-0abc1234"
	- CLI: `aws ec2 start-instances --instance-ids i-0abc1234 --region us-east-1`

- "List S3 buckets"
	- CLI: `aws s3 ls`

## Development notes

- Intent parsing is handled in `src/core/nlp_utils.py`. It prioritizes an ML classifier (if enabled) and falls back to rule-based regex extraction.
- CLI generation lives in `src/core/command_generator.py`.

## Contributing

File a PR with a clear description. Add unit tests in `tests/` for new intents or command changes.

## License

Project license not specified in the repo. Add a LICENSE file if you want to open-source this project.

