# ADR-007: Terraform Infrastructure as Code

## Status
Accepted

## Context
AWS infrastructure can be provisioned manually via console, CLI scripts, CloudFormation, CDK, Pulumi, or Terraform. Need to choose IaC approach.

## Decision
Use **Terraform** with HCL (HashiCorp Configuration Language) for all AWS infrastructure.

Remote state in S3 with DynamoDB locking.

## Alternatives Considered

### Alternative 1: AWS Console (Manual)
- **Pros**: Visual, fast for experiments
- **Cons**: Not reproducible, no version control, error-prone, not portfolio-appropriate
- **Rejected**: Not production-grade, not demonstrable

### Alternative 2: AWS CLI Scripts
- **Pros**: Scriptable, automatable
- **Cons**: Imperative (not declarative), no state management, hard to maintain
- **Rejected**: Lacks IaC benefits (drift detection, plan/preview)

### Alternative 3: AWS CloudFormation
- **Pros**: AWS-native, no external tool
- **Cons**: YAML verbose, limited expressiveness, AWS-only (not multi-cloud)
- **Rejected**: Less industry standard than Terraform for multi-cloud shops

### Alternative 4: AWS CDK (Cloud Development Kit)
- **Pros**: Programmatic (Python/TypeScript), type safety
- **Cons**: Compiles to CloudFormation (inherits limitations), less widespread than Terraform
- **Rejected**: Terraform more common in job postings

### Alternative 5: Pulumi
- **Pros**: Programmatic (Python/TypeScript/Go), multi-cloud
- **Cons**: Smaller community than Terraform, less mature
- **Rejected**: Terraform more established, better documentation

## Rationale

**Terraform advantages**:
- **Declarative**: Describe desired state, Terraform handles how
- **Plan preview**: terraform plan shows changes before apply
- **State management**: Tracks actual vs desired, detects drift
- **Multi-cloud**: Can manage AWS, Azure, GCP (portfolio extensibility)
- **Industry standard**: Most common IaC tool in job postings
- **Module ecosystem**: Reusable community modules
- **Provider maturity**: AWS provider feature-complete

**HCL benefits**:
- Purpose-built for infrastructure (not general programming)
- Readable (less verbose than JSON/YAML)
- Supports variables, loops, conditionals

**State in S3**:
- Persistent (not local)
- Shareable (team access, CI/CD access)
- Versioned (recover from mistakes)
- Encrypted at rest

**DynamoDB locking**:
- Prevents concurrent terraform apply
- Avoids state corruption

## Consequences

**Positive**:
- Infrastructure reproducible (destroy and recreate entire platform)
- Changes reviewable (Git diff on .tf files)
- Safe updates (plan before apply)
- Demonstrates IaC best practices
- Multi-cloud transferable skill

**Negative**:
- Terraform learning curve (state, providers, modules)
- State file management complexity
- Terraform not free (enterprise features paid, but OSS sufficient)

**Terraform structure**:
```
infrastructure/terraform/
├── main.tf           # Entry point
├── providers.tf      # AWS provider config
├── variables.tf      # Input variables
├── outputs.tf        # Output values
├── s3.tf             # S3 bucket resources
├── lambda.tf         # Lambda functions
├── glue.tf           # Glue jobs, catalog
├── iam.tf            # IAM roles, policies
├── monitoring.tf     # CloudWatch alarms
└── backend.tf        # S3 state backend
```

**Workflow**:
```bash
terraform init       # Initialize providers
terraform fmt        # Format code
terraform validate   # Validate syntax
terraform plan       # Preview changes
terraform apply      # Apply changes
terraform destroy    # Tear down (when needed)
```

## Validation
- Terraform can provision all required AWS resources
- State backend configured (S3 + DynamoDB)
- terraform plan output is human-readable
- Infrastructure can be destroyed and recreated in < 10 minutes

## References
- [Terraform AWS Provider](https://registry.terraform.io/providers/hashicorp/aws/latest/docs)
- [Terraform Best Practices](https://www.terraform-best-practices.com/)
- [Terraform Backend Configuration](https://www.terraform.io/language/settings/backends/s3)
