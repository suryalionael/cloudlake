# Security Architecture

## Security Philosophy

Defense in depth: Multiple layers of security controls. Least privilege: Grant minimum permissions required. Never commit secrets: All credentials external to code.

## AWS IAM Strategy

### Least Privilege Principle

Each service receives only the permissions required for its specific function.

### Lambda Execution Role

**Role**: `cloudlake-lambda-ingestion-role`

**Permissions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:PutObjectAcl"
      ],
      "Resource": "arn:aws:s3:::cloudlake-data-*/raw/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws/lambda/cloudlake-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "secretsmanager:GetSecretValue"
      ],
      "Resource": "arn:aws:secretsmanager:*:*:secret:cloudlake/api/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "CloudLake/Ingestion"
        }
      }
    }
  ]
}
```

**Justification**:
- S3 PutObject: Write ingested data to raw layer only (not processed/analytics)
- CloudWatch Logs: Standard Lambda logging
- Secrets Manager: Read API credentials
- CloudWatch Metrics: Publish custom metrics (namespace-restricted)

**Not granted**:
- S3 DeleteObject: Lambda should never delete data
- S3 GetObject: Lambda does not read from S3
- IAM permissions: Lambda should not modify IAM
- Glue permissions: Lambda does not trigger Glue jobs directly

### Glue Job Execution Role

**Role**: `cloudlake-glue-processing-role`

**Permissions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::cloudlake-data-*/raw/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::cloudlake-data-*/processed/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject"
      ],
      "Resource": "arn:aws:s3:::cloudlake-data-*/rejected/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:CreateTable",
        "glue:UpdateTable",
        "glue:CreatePartition",
        "glue:UpdatePartition",
        "glue:BatchCreatePartition"
      ],
      "Resource": [
        "arn:aws:glue:*:*:catalog",
        "arn:aws:glue:*:*:database/cloudlake",
        "arn:aws:glue:*:*:table/cloudlake/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "logs:CreateLogGroup",
        "logs:CreateLogStream",
        "logs:PutLogEvents"
      ],
      "Resource": "arn:aws:logs:*:*:log-group:/aws-glue/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "cloudwatch:namespace": "CloudLake/Processing"
        }
      }
    }
  ]
}
```

**Justification**:
- S3 GetObject on raw: Read input data
- S3 PutObject/DeleteObject on processed: Overwrite partitions (idempotency)
- S3 PutObject on rejected: Write validation failures
- Glue Catalog: Register tables and partitions
- CloudWatch Logs/Metrics: Observability

**Not granted**:
- S3 DeleteObject on raw: Glue should never delete source data
- IAM permissions
- Lambda invocation

### Athena Execution Role

**Role**: `cloudlake-athena-query-role` (for dbt/analysts)

**Permissions**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetObject",
        "s3:ListBucket"
      ],
      "Resource": [
        "arn:aws:s3:::cloudlake-data-*",
        "arn:aws:s3:::cloudlake-data-*/processed/*",
        "arn:aws:s3:::cloudlake-data-*/analytics/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::cloudlake-data-*/analytics/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:GetBucketLocation",
        "s3:ListBucket"
      ],
      "Resource": "arn:aws:s3:::cloudlake-athena-results-*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject"
      ],
      "Resource": "arn:aws:s3:::cloudlake-athena-results-*/*"
    },
    {
      "Effect": "Allow",
      "Action": [
        "glue:GetDatabase",
        "glue:GetTable",
        "glue:GetPartitions",
        "glue:CreateTable",
        "glue:UpdateTable",
        "glue:CreatePartition"
      ],
      "Resource": [
        "arn:aws:glue:*:*:catalog",
        "arn:aws:glue:*:*:database/cloudlake",
        "arn:aws:glue:*:*:table/cloudlake/*"
      ]
    },
    {
      "Effect": "Allow",
      "Action": [
        "athena:StartQueryExecution",
        "athena:GetQueryExecution",
        "athena:GetQueryResults",
        "athena:StopQueryExecution",
        "athena:GetWorkGroup"
      ],
      "Resource": "arn:aws:athena:*:*:workgroup/cloudlake"
    }
  ]
}
```

**Justification**:
- S3 GetObject on processed/analytics: Read data for queries
- S3 PutObject/DeleteObject on analytics: dbt writes transformed data
- Athena query results bucket: Standard Athena requirement
- Glue Catalog read: Discover tables and schemas
- Glue CreateTable/UpdateTable: dbt creates/modifies tables
- Athena query execution: Run SQL queries

**Not granted**:
- S3 access to raw layer: Analysts query processed/analytics, not raw
- S3 DeleteObject on processed: Analysts should not delete source data
- Glue DeleteTable: Prevent accidental catalog deletions

### Terraform Execution Role

**Role**: `cloudlake-terraform-deploy-role` (assumed by GitHub Actions OIDC)

**Permissions**: 
- Full administrative access during development
- Production: Restrict to specific resources

**Initial (development)**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "lambda:*",
        "glue:*",
        "athena:*",
        "iam:*",
        "logs:*",
        "cloudwatch:*",
        "events:*",
        "secretsmanager:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringEquals": {
          "aws:RequestedRegion": "us-east-1"
        }
      }
    }
  ]
}
```

**Production (future)**: Restrict to cloudlake-* resources only.

## Secrets Management

### API Credentials

**Never commit**:
- API keys
- API tokens
- Passwords
- AWS access keys
- Any credential

### Storage: AWS Secrets Manager

**Secret name**: `cloudlake/api/customers-api-key`

**Secret value**:
```json
{
  "api_key": "abc123...",
  "api_url": "https://api.example.com/customers"
}
```

**Lambda retrieval**:
```python
import boto3
import json

def get_api_credentials(secret_name):
    client = boto3.client('secretsmanager')
    response = client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

credentials = get_api_credentials('cloudlake/api/customers-api-key')
api_key = credentials['api_key']
```

**Rotation**: Manual initially. AWS Secrets Manager supports automatic rotation (future enhancement).

**Cost**: $0.40/secret/month + $0.05/10K API calls

### GitHub Actions Secrets

**For CI/CD**:
- AWS_ACCOUNT_ID (not sensitive, but convenient)
- GITHUB_OIDC_ROLE (ARN of Terraform deploy role)

**Not stored in GitHub Secrets**:
- AWS Access Keys (use OIDC instead)
- API keys (stored in Secrets Manager, not GitHub)

### OIDC Authentication (GitHub Actions → AWS)

**Preferred method**: OpenID Connect federation (no long-lived credentials)

**Trust policy** for `cloudlake-terraform-deploy-role`:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Principal": {
        "Federated": "arn:aws:iam::ACCOUNT_ID:oidc-provider/token.actions.githubusercontent.com"
      },
      "Action": "sts:AssumeRoleWithWebIdentity",
      "Condition": {
        "StringEquals": {
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com",
          "token.actions.githubusercontent.com:sub": "repo:USERNAME/cloudlake:ref:refs/heads/main"
        }
      }
    }
  ]
}
```

**Benefit**: No AWS credentials stored in GitHub. Temporary credentials issued per workflow run.

**GitHub Actions workflow**:
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v2
  with:
    role-to-assume: arn:aws:iam::ACCOUNT_ID:role/cloudlake-terraform-deploy-role
    aws-region: us-east-1
```

## S3 Bucket Security

### Bucket Policy

**Deny public access**:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyPublicAccess",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::cloudlake-data-*",
        "arn:aws:s3:::cloudlake-data-*/*"
      ],
      "Condition": {
        "StringNotEquals": {
          "aws:PrincipalOrgID": "o-XXXXXXXXXX"
        }
      }
    }
  ]
}
```

**Alternative**: Use S3 Block Public Access settings (simpler)

**Terraform**:
```hcl
resource "aws_s3_bucket_public_access_block" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}
```

### Encryption at Rest

**S3 Server-Side Encryption (SSE-S3)**:
- AES-256 encryption
- Managed by AWS
- No additional cost
- Enabled by default (AWS default since 2023)

**Terraform**:
```hcl
resource "aws_s3_bucket_server_side_encryption_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
    bucket_key_enabled = true
  }
}
```

**Not using SSE-KMS**:
- Adds cost ($1/month per key + $0.03/10K requests)
- No additional security benefit for portfolio scope
- Complicates key management

### Encryption in Transit

**HTTPS only**:

Bucket policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "DenyInsecureTransport",
      "Effect": "Deny",
      "Principal": "*",
      "Action": "s3:*",
      "Resource": [
        "arn:aws:s3:::cloudlake-data-*",
        "arn:aws:s3:::cloudlake-data-*/*"
      ],
      "Condition": {
        "Bool": {
          "aws:SecureTransport": "false"
        }
      }
    }
  ]
}
```

Lambda/Glue use boto3 with HTTPS by default.

## Logging Security

### Sensitive Data in Logs

**Never log**:
- API keys
- Passwords
- Customer PII (email, names) in error messages
- Full record payloads

**Log safely**:
- Record counts
- Schema structures
- Error types (not error payloads with PII)
- Identifiers (customer_id, order_id) without personal details

**Example**:
```python
# Bad
logger.error(f"Failed to process customer: {customer}")

# Good
logger.error(f"Failed to process customer_id: {customer['customer_id']}")
```

### CloudWatch Logs Encryption

**Encryption at rest**: KMS encryption for log groups (optional)

**Terraform**:
```hcl
resource "aws_cloudwatch_log_group" "lambda_ingestion" {
  name              = "/aws/lambda/cloudlake-ingestion"
  retention_in_days = 14
  kms_key_id        = aws_kms_key.cloudwatch.arn  # Optional
}
```

**Cost trade-off**: KMS adds cost. For portfolio scope, default encryption sufficient.

## Network Security

### Lambda VPC Configuration

**Not using VPC** for Lambda initially.

**Rationale**:
- Lambda accesses public API endpoints (S3, Secrets Manager)
- No private VPC resources
- VPC adds NAT Gateway cost (~$32/month)
- VPC adds cold start latency

**When to add VPC**:
- If data source is in private VPC (e.g., RDS, internal API)
- If compliance requires network isolation

### Glue VPC Configuration

**Not using VPC** for Glue jobs initially (same rationale as Lambda).

### Athena

**No VPC configuration**: Athena is fully managed, no network access control required.

## Access Control

### AWS Console Access

**Root account**:
- Enable MFA
- Never use for day-to-day operations
- Rotate credentials

**IAM User** (for development):
- Individual IAM user per developer
- Require MFA
- Least privilege (restrict to cloudlake-* resources)
- Console + programmatic access

**Example IAM policy** for developer:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:*",
        "lambda:*",
        "glue:*",
        "athena:*",
        "logs:*",
        "cloudwatch:*"
      ],
      "Resource": "*",
      "Condition": {
        "StringLike": {
          "aws:ResourceTag/Project": "cloudlake"
        }
      }
    }
  ]
}
```

Tag all resources with `Project=cloudlake` to enable scoped access.

### Athena Workgroup Access

**Workgroup**: `cloudlake`

**Access control**: IAM-based (athena:StartQueryExecution on workgroup ARN)

**Query result bucket**: Separate from data lake bucket (prevent accidental data exposure)

**Cost control**: Workgroup settings limit query scan size (future enhancement)

## Terraform State Security

### State Storage

**S3 backend**:
```hcl
terraform {
  backend "s3" {
    bucket         = "cloudlake-terraform-state-ACCOUNT_ID"
    key            = "cloudlake/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "cloudlake-terraform-locks"
  }
}
```

**Encryption**: S3 SSE enabled

**Versioning**: Enabled (recover from accidental deletion/corruption)

**Access control**: Restrict to Terraform deploy role only

**State locking**: DynamoDB table prevents concurrent modifications

### State File Contents

**Contains sensitive data**:
- IAM role ARNs
- S3 bucket names
- Resource IDs

**Does not contain**:
- API keys (stored in Secrets Manager, referenced by ARN)
- Passwords

**Security**: State file is not secret, but should not be public. S3 bucket is private.

## Compliance and Auditing

### CloudTrail

**Enable CloudTrail** for audit logging:
- All API calls logged
- Who created/modified/deleted resources
- When actions occurred

**Log storage**: S3 bucket with long retention (1 year+)

**Cost**: ~$2/month for CloudLake scale

**Not implemented initially** (cost optimization), but should be enabled for production-grade operation.

### Resource Tagging

**Standard tags**:
```hcl
tags = {
  Project     = "cloudlake"
  Environment = "prod"
  ManagedBy   = "terraform"
  Owner       = "data-engineering"
}
```

**Benefits**:
- Cost allocation
- Access control (tag-based IAM policies)
- Resource inventory

## Data Privacy

### PII Handling

**PII in dataset**:
- Customer email
- Customer name
- Customer address (city/state)

**No special handling required** for portfolio scope (fictional data).

**Production considerations**:
- Encryption at rest (already enabled)
- Access control (IAM roles)
- Audit logging (CloudTrail)
- Data retention policies
- Right to deletion (manual process)

### Data Retention

**Raw layer**: 90 days (S3 lifecycle policy)
**Processed layer**: 1 year
**Analytics layer**: Indefinite (small volume)

**Rationale**: Balance recoverability vs cost vs compliance.

## Security Checklist

Deployment checklist:

- [ ] S3 Block Public Access enabled
- [ ] S3 encryption at rest enabled (SSE-S3)
- [ ] S3 bucket policy enforces HTTPS
- [ ] IAM roles follow least privilege
- [ ] No hardcoded credentials in code
- [ ] API credentials stored in Secrets Manager
- [ ] GitHub Actions uses OIDC (no long-lived keys)
- [ ] Terraform state encrypted and versioned
- [ ] CloudWatch Logs retention configured
- [ ] All resources tagged with Project=cloudlake
- [ ] Root account MFA enabled
- [ ] IAM user MFA enabled
- [ ] No AWS Access Keys committed to Git
- [ ] .gitignore excludes secrets files

## Secrets in Git Prevention

### .gitignore

Already includes:
```
.env
.env.*
secrets/
*.key
*.secret
terraform.tfvars
*.tfvars
```

### Pre-commit Hooks (Future)

Install `git-secrets` or `truffleHog`:
```bash
git secrets --install
git secrets --register-aws
```

Prevents accidental commits of AWS credentials.

### Code Review

Manual review before merge: Check for hardcoded credentials.

## Incident Response

### Scenario: API Key Leaked

**Detection**: GitHub secret scanning alert, manual discovery

**Response**:
1. Immediately revoke leaked key in source system
2. Rotate secret in Secrets Manager
3. Update Lambda to use new secret
4. Review CloudTrail for unauthorized access
5. Remove leaked key from Git history (`git filter-branch` or BFG Repo-Cleaner)

### Scenario: Unauthorized S3 Access

**Detection**: CloudTrail logs, S3 access logs, GuardDuty (if enabled)

**Response**:
1. Identify compromised IAM credentials
2. Revoke credentials (delete IAM user, rotate keys)
3. Review accessed objects
4. Check for data exfiltration
5. Restore from backup if modified

### Scenario: Terraform State Exposed

**Risk**: State file contains resource metadata (ARNs, IDs), but not secrets

**Response**:
1. Restrict state bucket access
2. Review who accessed state file (CloudTrail)
3. Rotate any credentials referenced in state (if applicable)
4. Audit infrastructure for unauthorized changes

## Security Roadmap

**Phase 2** (Infrastructure):
- Implement S3 bucket with Block Public Access
- Enable S3 encryption
- Create IAM roles with least privilege
- Set up Terraform state backend with encryption

**Phase 3** (Ingestion):
- Store API credentials in Secrets Manager
- Implement Lambda IAM role
- Test credential retrieval

**Phase 5** (CI/CD):
- Set up GitHub OIDC provider in AWS
- Configure GitHub Actions with OIDC
- Remove any AWS Access Keys from GitHub Secrets

**Phase 10** (Production Audit):
- Enable CloudTrail
- Review all IAM policies for over-permissions
- Security penetration test (attempt to access restricted resources)
- Document incident response procedures

## Trade-offs

**Not implemented** (excessive for portfolio):
- AWS GuardDuty: $30+/month for threat detection
- AWS Security Hub: Additional cost, enterprise-focused
- VPC for Lambda/Glue: $32+/month NAT Gateway cost
- SSE-KMS encryption: $1+/month per key
- AWS WAF: No public endpoints to protect
- Secrets Manager rotation Lambda: Adds complexity

**Implemented** (appropriate):
- IAM least privilege
- S3 encryption and access controls
- Secrets Manager for credentials
- GitHub OIDC (no long-lived credentials)
- HTTPS enforcement
- MFA for console access

**Principle**: Use AWS-native security features. Avoid third-party security tools unless clear compliance requirement.
