# ADR-001: Cloud Platform Scope

## Status
Accepted

## Context
CloudLake is a portfolio project demonstrating cloud data engineering capabilities. The initial proposal suggested a comprehensive AWS data platform with Lambda, Glue, S3, Athena, dbt, Terraform, and CI/CD.

Need to determine: Is this the right scope for a portfolio project? Are all components justified?

## Decision
Implement a focused serverless data platform using AWS S3 (data lake), Lambda (ingestion), Glue (ETL), Athena (query), and dbt (analytics).

**Target**: < $10/month operational cost.

## Alternatives Considered

### Alternative 1: Minimal (S3 + Local Processing)
- S3 for storage
- Local Python scripts for processing
- Local DuckDB for queries
- **Cost**: ~$1/month
- **Rejected**: Defeats cloud platform purpose, no distributed processing demonstration

### Alternative 2: Enterprise (Add Redshift, EMR, Airflow)
- Full data warehouse (Redshift Serverless)
- Spark cluster (EMR)
- Orchestration (Managed Airflow)
- **Cost**: $300+/month
- **Rejected**: Excessive cost, over-engineered for portfolio scope

### Alternative 3: Real-Time (Kinesis, DynamoDB, Lambda)
- Streaming ingestion (Kinesis)
- Real-time processing (Lambda)
- NoSQL storage (DynamoDB)
- **Cost**: ~$20/month
- **Rejected**: Different skill demonstration (streaming vs batch), overlaps with existing portfolio focus

## Rationale

**Serverless architecture**:
- Pay-per-use aligns with portfolio budget constraints
- No idle resources when not running
- Demonstrates cloud-native patterns

**S3 data lake**:
- Industry-standard cloud storage
- Multi-layer architecture (raw/processed/analytics)
- Demonstrates data lake design patterns

**Lambda for ingestion**:
- Appropriate for batch API calls
- Free tier covers expected usage
- Simple deployment model

**Glue for ETL**:
- Purpose-built for data transformation
- Integrated catalog for Athena
- Python Shell jobs sufficient for stated volume

**Athena for query**:
- Serverless SQL engine
- Pay per query (not per hour)
- Industry-relevant tool

**dbt for analytics**:
- Standard analytics engineering tool
- SQL-based transformations
- Complements cloud infrastructure

## Consequences

**Positive**:
- Cost-effective (target met)
- Demonstrates core cloud data engineering skills
- Realistic production patterns at portfolio scale
- Reproducible (Terraform IaC)

**Negative**:
- Does not demonstrate real-time streaming
- Does not demonstrate Spark cluster management
- Does not demonstrate enterprise DWH (Redshift/Snowflake)

**Acceptable trade-offs**: Portfolio should be focused, not comprehensive. Other projects can demonstrate complementary skills.

## Validation
- Monthly cost estimate: $2.33
- Aligns with data engineering role requirements
- Differentiates from notebook-only projects
