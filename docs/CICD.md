# CI/CD Strategy

## CI/CD Philosophy

Automated testing catches errors before production. Infrastructure changes are reviewed and validated. Deployments are reproducible and auditable.

## Pipeline Architecture

```mermaid
graph LR
    A[Pull Request] --> B[Lint & Format]
    B --> C[Unit Tests]
    C --> D[Terraform Validate]
    D --> E[Code Review]
    E --> F[Merge to Main]
    F --> G[Terraform Plan]
    G --> H[Manual Approval]
    H --> I[Terraform Apply]
    I --> J[Smoke Tests]
    J --> K[Deployment Complete]
```

## GitHub Actions Workflows

### Workflow 1: Pull Request Checks

**File**: `.github/workflows/pr-checks.yml`

**Trigger**: Pull request to main branch

**Jobs**:

#### Lint and Format
- Python: `black`, `flake8`, `isort`
- Terraform: `terraform fmt -check`
- SQL (dbt): `sqlfluff lint`

#### Unit Tests
- Python Lambda functions: `pytest`
- Python Glue jobs: `pytest` with PySpark mocks
- Test coverage threshold: 70%

#### Terraform Validation
- `terraform init`
- `terraform validate`
- `terraform plan` (no apply)
- `tflint` (Terraform linting)

#### dbt Checks
- `dbt parse` (validate model syntax)
- `dbt compile` (validate SQL compilation)
- `dbt run --select model+ --dry-run` (if supported)

**Exit criteria**: All checks pass before merge allowed

**Estimated runtime**: 3-5 minutes

**Cost**: GitHub Actions free tier (2000 minutes/month for public repos, 500 for private)

### Workflow 2: Main Branch Deployment

**File**: `.github/workflows/deploy.yml`

**Trigger**: Push to main branch (after merge)

**Jobs**:

#### Terraform Plan
- Authenticate to AWS (OIDC)
- `terraform init`
- `terraform plan -out=tfplan`
- Upload plan artifact
- Comment plan summary on commit (optional)

#### Manual Approval
- GitHub Environment protection rule
- Require reviewer approval before apply
- Prevents accidental deployment

#### Terraform Apply
- Download plan artifact
- `terraform apply tfplan`
- Upload state to S3 backend
- Comment apply result

#### Smoke Tests
- Verify S3 buckets exist
- Verify Lambda functions deployed
- Verify Glue jobs exist
- Optionally trigger test Lambda invocation

**Exit criteria**: Terraform apply succeeds, smoke tests pass

**Estimated runtime**: 5-10 minutes

**Cost**: Free tier

### Workflow 3: Data Pipeline Run

**File**: `.github/workflows/pipeline.yml`

**Trigger**: 
- Schedule (cron: daily at 06:00 UTC)
- Manual workflow_dispatch

**Jobs**:

#### Invoke Ingestion
- Trigger Lambda functions (one per entity)
- Wait for completion
- Check CloudWatch logs for success

#### Run Glue Processing
- Trigger Glue job
- Poll for completion
- Check job status

#### Run dbt Transformations
- Authenticate to AWS
- `dbt run --profiles-dir ./profiles`
- `dbt test`
- Upload logs to S3 or artifact

#### Pipeline Status
- Aggregate results
- Post status (success/failure)
- Alert on failure (if SNS configured)

**Exit criteria**: All stages succeed

**Estimated runtime**: 15-30 minutes

**Cost**: Lambda/Glue/Athena usage (already accounted in cost model)

## GitHub Actions Configuration

### OIDC Authentication

**AWS IAM Identity Provider**:
```hcl
resource "aws_iam_openid_connect_provider" "github" {
  url = "https://token.actions.githubusercontent.com"
  
  client_id_list = ["sts.amazonaws.com"]
  
  thumbprint_list = [
    "6938fd4d98bab03faadb97b34396831e3780aea1"  # GitHub Actions OIDC thumbprint
  ]
}
```

**Trust policy** (cloudlake-terraform-deploy-role):
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
          "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
        },
        "StringLike": {
          "token.actions.githubusercontent.com:sub": "repo:USERNAME/cloudlake:*"
        }
      }
    }
  ]
}
```

**Workflow step**:
```yaml
- name: Configure AWS credentials
  uses: aws-actions/configure-aws-credentials@v2
  with:
    role-to-assume: arn:aws:iam::${{ secrets.AWS_ACCOUNT_ID }}:role/cloudlake-terraform-deploy-role
    aws-region: us-east-1
```

**Benefit**: No long-lived AWS credentials in GitHub Secrets.

### GitHub Secrets

**Required secrets**:
- `AWS_ACCOUNT_ID`: AWS account number (not sensitive, but convenient)

**Not required** (using OIDC):
- ~~AWS_ACCESS_KEY_ID~~
- ~~AWS_SECRET_ACCESS_KEY~~

### GitHub Environments

**Environment**: `production`

**Protection rules**:
- Required reviewers: 1 (yourself for portfolio)
- Wait timer: 0 minutes
- Deployment branches: main only

**Purpose**: Manual gate before Terraform apply.

## Testing Strategy

### Local Testing

**Before pushing**:
```bash
# Python
black src/
flake8 src/
pytest tests/

# Terraform
terraform fmt -recursive
terraform validate

# dbt
dbt parse
dbt compile
```

### Unit Tests (Python)

**Lambda function tests**:
```python
# tests/test_lambda_ingestion.py
import pytest
from src.lambda_ingestion import validate_customer_schema, lambda_handler

def test_validate_customer_schema_valid():
    data = {
        "customer_id": "c123",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "country": "US",
        "created_at": "2026-09-14T00:00:00Z",
        "updated_at": "2026-09-14T00:00:00Z"
    }
    assert validate_customer_schema(data) == True

def test_validate_customer_schema_missing_field():
    data = {"customer_id": "c123"}
    with pytest.raises(ValueError):
        validate_customer_schema(data)

def test_lambda_handler_success(mocker):
    mocker.patch('src.lambda_ingestion.fetch_api_data', return_value=[...])
    mocker.patch('src.lambda_ingestion.write_to_s3', return_value='s3://...')
    
    result = lambda_handler({}, {})
    assert result['status'] == 'success'
```

**Glue job tests**:
```python
# tests/test_glue_processing.py
import pytest
from pyspark.sql import SparkSession
from src.glue_processing import validate_schema, transform_to_parquet

@pytest.fixture(scope="module")
def spark():
    return SparkSession.builder.master("local[1]").getOrCreate()

def test_validate_schema(spark):
    data = [{"customer_id": "c123", "email": "test@example.com", ...}]
    df = spark.createDataFrame(data)
    validated_df = validate_schema(df)
    assert validated_df.count() == 1
```

### Integration Tests

**End-to-end test** (run manually, not in CI initially):
```bash
# 1. Deploy infrastructure
terraform apply

# 2. Upload test data
aws s3 cp test_data/customers.json s3://cloudlake-data-.../raw/customers/year=2026/month=09/day=14/

# 3. Trigger Glue job
aws glue start-job-run --job-name cloudlake-processing --arguments='{"--date":"2026-09-14"}'

# 4. Wait for completion
aws glue get-job-run --job-name cloudlake-processing --run-id <run-id>

# 5. Run dbt
dbt run
dbt test

# 6. Query result
aws athena start-query-execution --query-string "SELECT COUNT(*) FROM analytics.stg_customers"

# 7. Verify count matches expected
```

**Automated integration test** (future):
- Separate test environment
- GitHub Actions workflow
- Tear down after test

### Infrastructure Tests

**Terraform validation**:
```yaml
- name: Terraform Validate
  run: |
    terraform init
    terraform validate
    terraform fmt -check -recursive
```

**tflint**:
```yaml
- name: TFLint
  uses: terraform-linters/setup-tflint@v3
  with:
    tflint_version: latest
- run: tflint --init
- run: tflint -f compact
```

**checkov** (security/compliance scanning):
```yaml
- name: Checkov
  uses: bridgecrewio/checkov-action@master
  with:
    directory: infrastructure/terraform/
    framework: terraform
```

### dbt Tests

**Generic tests** (in schema.yml):
```yaml
models:
  - name: stg_customers
    columns:
      - name: customer_id
        tests:
          - not_null
          - unique
```

**Custom tests** (in tests/):
```sql
-- tests/assert_revenue_positive.sql
SELECT *
FROM {{ ref('fact_order') }}
WHERE revenue < 0
```

**Run in CI**:
```yaml
- name: dbt Test
  run: |
    dbt run --select tag:test_data
    dbt test
```

## Deployment Workflow

### Pull Request Flow

1. Developer creates feature branch
2. Makes changes (code, Terraform, dbt)
3. Commits and pushes
4. Opens pull request
5. **GitHub Actions runs PR checks** (lint, test, validate)
6. If checks fail, developer fixes and pushes again
7. If checks pass, reviewer approves
8. Developer merges to main

### Deployment Flow

1. Merge to main triggers deployment workflow
2. **Terraform plan runs**, outputs summary
3. **Manual approval required** (GitHub Environment protection)
4. Reviewer inspects plan, approves deployment
5. **Terraform apply executes**
6. Infrastructure changes deployed
7. **Smoke tests verify** deployment
8. Workflow completes

### Rollback Procedure

**Scenario**: Terraform apply breaks infrastructure

**Option 1**: Revert commit
```bash
git revert <commit-sha>
git push origin main
# Triggers new deployment with reverted state
```

**Option 2**: Manual Terraform
```bash
git checkout <previous-commit>
terraform apply
```

**Option 3**: Restore from state backup
```bash
# S3 versioning enabled on state bucket
aws s3api list-object-versions --bucket cloudlake-terraform-state-ACCOUNT_ID --prefix cloudlake/terraform.tfstate
aws s3api get-object --bucket ... --key ... --version-id ... terraform.tfstate
terraform apply
```

## Branch Strategy

**Main branch**: Production-ready code only

**Feature branches**: `feature/add-products-entity`, `fix/lambda-timeout`

**No dev/staging branches initially**: Single environment simplifies workflow

**Future**: Add staging branch if multi-environment needed

## Deployment Frequency

**Infrastructure changes**: As needed (infrequent, ~1-2x/week during development)

**Data pipeline**: Daily (scheduled via EventBridge, not CI/CD)

**dbt models**: Daily (part of data pipeline)

**Lambda code updates**: As needed (redeploy via Terraform)

## Versioning Strategy

**Git tags**: Tag releases
```bash
git tag -a v0.1.0 -m "Initial infrastructure deployment"
git push origin v0.1.0
```

**Semantic versioning**: MAJOR.MINOR.PATCH
- MAJOR: Breaking changes (schema change, API change)
- MINOR: New features (new entity, new mart)
- PATCH: Bug fixes

**Lambda versions**: Use Git commit SHA in Lambda description

**Terraform workspace**: Not using workspaces (single environment)

## CI/CD Observability

### Workflow Status

**GitHub Actions UI**: 
- Workflow runs visible in Actions tab
- Status badges in README (optional)

**Notifications**:
- Email on workflow failure (GitHub notifications)
- Slack integration (future)

### Deployment Logs

**Terraform output**: Captured in GitHub Actions logs

**Deployment history**: Git commit history + tags

**State changes**: Terraform state history in S3 versioning

## Security in CI/CD

### Secret Management

**Never commit**:
- AWS credentials (use OIDC)
- API keys (stored in AWS Secrets Manager/SSM)
- Terraform state files

### Code Scanning

**GitHub Advanced Security** (free for public repos):
- Dependabot (dependency vulnerability scanning)
- CodeQL (static analysis)
- Secret scanning (detects committed secrets)

**Enable**:
```yaml
# .github/dependabot.yml
version: 2
updates:
  - package-ecosystem: "pip"
    directory: "/"
    schedule:
      interval: "weekly"
  - package-ecosystem: "terraform"
    directory: "/infrastructure/terraform"
    schedule:
      interval: "weekly"
```

### Least Privilege

**GitHub Actions OIDC role**: Only permissions needed for Terraform

**Separate roles** (future):
- terraform-deploy-role: Full infrastructure access
- pipeline-execution-role: Lambda/Glue invocation only (no IAM changes)

## CI/CD Cost

**GitHub Actions**:
- Free tier: 2000 minutes/month (public repo) or 500 minutes/month (private repo)
- Estimated usage: ~100 minutes/month (10 PRs × 5 min + 30 deployments × 2 min)
- **Cost: $0** (within free tier)

**AWS**:
- Terraform plan/apply: No cost (API calls within free tier)
- Lambda/Glue invocations: Counted in data pipeline cost
- **Cost: $0**

**Total CI/CD cost**: **$0**

## CI/CD Maturity Roadmap

### Phase 1: Manual
- Local Terraform apply
- Manual testing
- No automation

### Phase 2: Basic CI
- GitHub Actions PR checks (lint, test)
- Manual deployment

### Phase 3: Automated Deployment
- GitHub Actions Terraform apply
- Manual approval gate

### Phase 4: Full Automation
- Automated integration tests
- Automated smoke tests
- Scheduled pipeline runs

### Phase 5: Advanced
- Multi-environment (dev/prod)
- Blue-green deployment
- Automated rollback

**CloudLake target**: Phase 3 (automated deployment with manual approval)

## Monitoring and Alerting

### Workflow Failures

**GitHub Actions**: Email notification on failure

**CloudWatch**: Pipeline execution failures logged and alarmed (see OBSERVABILITY.md)

### Deployment Success Rate

**Metric**: % of Terraform applies that succeed

**Query** (manual, via GitHub API):
```bash
gh run list --workflow=deploy.yml --limit=100 --json conclusion
```

**Target**: >95% success rate

## Testing Checklist

**Before opening PR**:
- [ ] Run `black`, `flake8`, `isort` locally
- [ ] Run `pytest` locally (all tests pass)
- [ ] Run `terraform fmt` and `terraform validate`
- [ ] Run `dbt parse` and `dbt compile`
- [ ] Test Lambda function with sample input
- [ ] Review changed files (no secrets committed)

**Before merging PR**:
- [ ] GitHub Actions checks pass
- [ ] Code review approved
- [ ] No merge conflicts

**Before approving deployment**:
- [ ] Review Terraform plan output
- [ ] Verify expected resource changes
- [ ] Check for unintended deletions
- [ ] Confirm cost impact acceptable

## CI/CD Implementation Phases

**Phase 9** (CI/CD):
1. Create `.github/workflows/pr-checks.yml`
2. Set up Python linting and testing
3. Set up Terraform validation
4. Test PR workflow with sample PR
5. Create `.github/workflows/deploy.yml`
6. Configure GitHub OIDC provider in AWS
7. Configure GitHub Environment with protection rules
8. Test deployment workflow with infrastructure change
9. Document runbook for approval/deployment

**Phase 9b** (Pipeline Automation):
1. Create `.github/workflows/pipeline.yml`
2. Configure scheduled trigger (daily 06:00 UTC)
3. Implement Lambda invocation step
4. Implement Glue job trigger step
5. Implement dbt run step
6. Test end-to-end pipeline via GitHub Actions

## Trade-offs

**Not implemented** (excessive for portfolio):
- Jenkins: Self-hosted, operational overhead
- GitLab CI: Requires GitLab, not GitHub
- CircleCI: Third-party, additional cost
- ArgoCD: Kubernetes-focused, no k8s in CloudLake
- Terraform Cloud: $20/month for team features
- Multi-environment CI/CD: Adds complexity

**Implemented** (appropriate):
- GitHub Actions (free, native GitHub integration)
- OIDC authentication (no secrets in GitHub)
- Manual approval gate (prevents accidental deployment)
- Basic test coverage (lint, unit tests, Terraform validate)

**Principle**: Use GitHub-native CI/CD. Avoid third-party CI/CD tools. Keep pipelines simple and fast.
