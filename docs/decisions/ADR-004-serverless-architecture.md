# ADR-004: Serverless Architecture

## Status
Accepted

## Context
Cloud compute options include always-on instances (EC2), containers (ECS/Fargate), Kubernetes (EKS), or serverless (Lambda, Glue). Need to choose compute model for ingestion and processing.

## Decision
Use **serverless architecture**: Lambda for ingestion, Glue Python Shell jobs for processing.

No EC2, ECS, or EKS.

## Alternatives Considered

### Alternative 1: EC2 Instances
- **Setup**: t3.medium instance running Python scripts on cron
- **Cost**: $30/month (even if only running 1 hour/day)
- **Rejected**: Continuous cost, operational overhead (patching, monitoring)

### Alternative 2: ECS with Fargate
- **Setup**: Containerized ingestion/processing on Fargate
- **Cost**: $15-20/month for scheduled tasks
- **Rejected**: More expensive than serverless, adds container complexity

### Alternative 3: EKS (Kubernetes)
- **Setup**: Kubernetes cluster with batch jobs
- **Cost**: $72/month (control plane) + worker nodes
- **Rejected**: Massive overkill, excessive cost, operational complexity

### Alternative 4: Self-Hosted Airflow on EC2
- **Setup**: EC2 running Airflow for orchestration
- **Cost**: $30/month minimum
- **Rejected**: Airflow not needed for linear pipeline, EC2 cost

### Alternative 5: AWS Batch
- **Setup**: Batch jobs on Fargate Spot
- **Cost**: $5-10/month
- **Rejected**: More complex than Lambda/Glue, minimal cost savings

## Rationale

**Lambda for ingestion**:
- Sub-second invocation (no cold start concern for scheduled jobs)
- 15-minute timeout sufficient for API calls
- Free tier: 1M requests, 400K GB-seconds/month
- Automatic scaling (not needed but future-proof)
- No operational overhead (no servers to patch)

**Glue Python Shell for processing**:
- Purpose-built for data transformation
- Integrated with Glue Data Catalog
- Serverless (pay per job-second)
- Python environment with pandas, boto3 pre-installed
- Can upgrade to PySpark if volume grows

**Serverless advantages**:
- **Cost**: Pay only when running (30 minutes/day = ~$2/month vs $30/month EC2)
- **Simplicity**: No server management, patching, scaling
- **Reliability**: AWS-managed infrastructure
- **Appropriate scale**: 10K orders/day does not require persistent compute

## Consequences

**Positive**:
- Monthly cost: $2.33 (vs $30+ for instance-based)
- Zero operational overhead (no SSH, no patching, no monitoring instances)
- Automatically scales if volume increases
- Demonstrates cloud-native serverless patterns

**Negative**:
- Lambda 15-minute timeout (not an issue for current use case)
- Lambda 10GB memory limit (not an issue for current use case)
- Glue job startup time ~30-60 seconds (acceptable for daily batch)
- Less control over environment (acceptable: Python stdlib sufficient)

**When to reconsider**:
- If processing time exceeds 15 minutes regularly → use Glue PySpark (2 DPU min)
- If need persistent state/cache → add Redis/ElastiCache (not needed currently)
- If need complex orchestration → add Step Functions (not needed for linear pipeline)

## Validation
- Lambda invocation count: 150/month (free tier: 1M/month)
- Lambda compute: 750 GB-seconds/month (free tier: 400K/month) → $0
- Glue job runtime: 5 min/day × 30 days = 150 minutes/month → $2.20
- Total serverless cost: $2.20/month
- Equivalent EC2 t3.medium: $30/month
- **Savings**: 93%

## References
- [AWS Lambda Pricing](https://aws.amazon.com/lambda/pricing/)
- [AWS Glue Pricing](https://aws.amazon.com/glue/pricing/)
- [Serverless Data Processing Patterns](https://aws.amazon.com/blogs/big-data/)
