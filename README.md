# {MISSION NAME HERE} Data Reprocessing Workflow (Python Implementation)

## Workflow Components

1. **Request Submission**: Users submit JSON requests following the schema
2. **Validation**: Automated validation of requests against schema
3. **Processing**: Generation of event payloads and Lambda invocation
4. **Monitoring**: Tracking through Grafana and S3 index pages

## Python Scripts

- `scripts/validator.py`: Validates request JSON against schema
- `scripts/payload_generator.py`: Generates Lambda event payloads
- `scripts/rename_sorter.py`: Organizes request files
- `scripts/lambda_invoker.py`: Invokes processing Lambda functions

## Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# How to test if a request is valid locally
python -m scripts.validator requests/submit/request.json
