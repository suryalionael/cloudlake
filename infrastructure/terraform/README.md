# CloudLake Terraform Configuration

This directory contains Infrastructure as Code (IaC) for CloudLake's AWS resources.

## Prerequisites

- Terraform >= 1.0
- AWS CLI configured with appropriate credentials
- AWS account with permissions to create resources

## Initial Setup

### 1. Configure Backend (Optional but Recommended)

Create a backend configuration file:

```bash
cat > backend.tfvars <<EOF
bucket         = "cloudlake-terraform-state-YOUR_ACCOUNT_ID"
key            = "cloudlake/terraform.tfstate"
region         = "us-east-1"
encrypt        = true
dynamodb_table = "cloudlake-terraform-locks"
EOF
```

Note: You must create the S3 bucket and DynamoDB table manually before running terraform init.

### 2. Initialize Terraform

```bash
cd infrastructure/terraform
terraform init
```

With backend configuration:
```bash
terraform init -backend-config=backend.tfvars
```

## Usage

### Validate Configuration

```bash
terraform validate
```

### Format Code

```bash
terraform fmt -recursive
```

### Plan Deployment

```bash
terraform plan
```

### Apply (Deploy to AWS)

**⚠️ WARNING: This will create AWS resources and incur costs**

```bash
terraform apply
```

### Destroy Infrastructure

```bash
terraform destroy
```

## Configuration Files

- `main.tf` - Entry point and documentation
- `providers.tf` - Terraform and AWS provider configuration
- `variables.tf` - Input variables with defaults
- `outputs.tf` - Output values after deployment
- `s3.tf` - S3 buckets for data lake and Athena results
- `iam.tf` - IAM roles and policies (Lambda, Glue, Athena)
- `lambda.tf` - Lambda functions for data ingestion
- `glue.tf` - Glue catalog, jobs, and crawlers
- `athena.tf` - Athena workgroup configuration
- `monitoring.tf` - CloudWatch alarms

## Variables

Key variables (see `variables.tf` for complete list):

- `aws_region` - AWS region (default: us-east-1)
- `environment` - Environment name (default: dev)
- `project_name` - Project name (default: cloudlake)
- `data_retention_days` - Raw data retention (default: 90 days)
- `log_retention_days` - CloudWatch logs retention (default: 14 days)

Override variables:
```bash
terraform plan -var="aws_region=us-west-2"
```

Or create `terraform.tfvars`:
```hcl
aws_region         = "us-east-1"
environment        = "dev"
data_retention_days = 90
```

## Resources Created

### Storage
- S3 bucket: `cloudlake-data-{account_id}`
- S3 bucket: `cloudlake-athena-results-{account_id}`

### Compute
- Lambda functions: `cloudlake-ingestion-{entity}` (customers, products, stores, orders)
- Glue job: `cloudlake-processing`

### Data Catalog
- Glue database: `cloudlake`
- Glue crawler: `cloudlake-processed-crawler`

### Query
- Athena workgroup: `cloudlake`

### IAM
- Lambda execution role: `cloudlake-lambda-ingestion-role`
- Glue execution role: `cloudlake-glue-processing-role`
- Athena query role: `cloudlake-athena-query-role`

### Monitoring
- CloudWatch log groups for Lambda and Glue
- CloudWatch alarms for failures

### Scheduling
- EventBridge rules for daily Lambda invocation (6 AM UTC)

## Estimated Monthly Cost

See `docs/COST.md` for detailed cost breakdown.

**Estimated: $2.33/month**
- S3 storage: $0.05
- Lambda: $0.00 (free tier)
- Glue: $2.20
- Athena: $0.08
- CloudWatch: $0.00 (free tier)

## Security Features

- S3 encryption at rest (SSE-S3)
- S3 public access blocked
- S3 bucket versioning enabled
- IAM least privilege policies
- HTTPS-only data transfer
- CloudWatch Logs encryption

## State Management

Terraform state is stored in S3 with:
- Encryption at rest
- Versioning enabled
- DynamoDB locking to prevent concurrent modifications

## Deployment Workflow

1. **Local validation**: `terraform validate` and `terraform plan`
2. **Review plan output**: Verify expected resource changes
3. **Manual approval**: Confirm changes are intentional
4. **Apply**: `terraform apply`
5. **Verify**: Check AWS console or use `terraform output`

## Troubleshooting

### Error: Backend initialization required

Run `terraform init` first.

### Error: Access denied creating S3 bucket

Ensure AWS credentials have sufficient permissions.

### Error: Resource already exists

If resources were created outside Terraform, either import them or use different names.

### Placeholder Lambda functions

Lambda functions are created with placeholder code. Actual ingestion code will be deployed in Phase 3.

## Phase 2 Status

**Status**: Configuration complete, not yet deployed

This Terraform configuration is ready for validation but has not been applied to AWS. No resources have been created. No costs incurred.

**Next steps**:
1. Review configuration files
2. Run `terraform validate` and `terraform plan`
3. Await approval for Phase 3 deployment
