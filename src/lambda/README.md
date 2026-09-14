# Lambda Deployment Package

This directory contains the packaged Lambda function code for data ingestion.

## Contents

- `lambda_function.py` - Main Lambda handler for ingestion
- `faker/` - Faker library for generating sample data (development/testing)

## Building the Package

From repository root:

```bash
cd src/lambda
pip install Faker -t .
zip -r ../../lambda_deployment.zip .
cp ../../lambda_deployment.zip ../../infrastructure/terraform/
```

## Lambda Configuration

- **Runtime**: Python 3.12
- **Handler**: `lambda_function.lambda_handler`
- **Memory**: 512 MB
- **Timeout**: 300 seconds (5 minutes)

## Environment Variables

Set by Terraform:
- `ENTITY` - Entity name (customers, products, stores, orders)
- `S3_BUCKET` - Target S3 bucket
- `S3_PREFIX` - S3 prefix (raw/entity_name)
- `PARAMETER_PREFIX` - SSM parameter prefix for API credentials

## Testing Locally

```python
import os
os.environ['ENTITY'] = 'customers'
os.environ['S3_BUCKET'] = 'test-bucket'
os.environ['S3_PREFIX'] = 'raw/customers'

from lambda_function import lambda_handler

event = {}
context = type('obj', (object,), {'request_id': 'test-123'})()

result = lambda_handler(event, context)
print(result)
```

## Production Usage

In production, replace the `generate_sample_data()` function with actual API calls to external data sources.

Store API credentials in AWS SSM Parameter Store:
```bash
aws ssm put-parameter --name "/cloudlake/api/customers-endpoint" --value "https://api.example.com/customers" --type String
aws ssm put-parameter --name "/cloudlake/api/customers-key" --value "YOUR_API_KEY" --type SecureString
```

## Phase 3 Status

Lambda code complete and packaged. Ready for deployment once AWS credentials are configured.
