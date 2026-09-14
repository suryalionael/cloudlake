# Cost Architecture

## Cost Philosophy

CloudLake must operate within strict budget constraints. Target monthly cost: **< $20**. Stretch goal: **< $10**.

Serverless architecture enables pay-per-use. No resources run when idle.

## Cost Drivers

### S3 Storage

**Pricing**:
- Standard storage: $0.023/GB/month
- Intelligent-Tiering: $0.0025/1000 objects + tiered storage pricing

**Estimated volume**:
- Raw layer: 10K orders/day × 1KB avg = 10MB/day = 300MB/month
- Orders + customers + products + stores = ~500MB/month
- 90-day retention: 500MB × 3 = 1.5GB raw
- Processed layer (Parquet, compressed 3:1): 0.5GB
- Analytics layer: 0.2GB
- **Total: ~2.2GB**

**Estimated cost**: 2.2GB × $0.023 = **$0.05/month**

**Growth over 1 year**: 6GB total = **$0.14/month**

**Mitigation**:
- S3 lifecycle policies (raw → IA after 30 days, delete after 90 days)
- Parquet compression
- Partition pruning (avoid storing unnecessary intermediate files)

### Lambda

**Pricing**:
- $0.20 per 1M requests
- $0.0000166667 per GB-second

**Estimated usage**:
- 5 entities × 1 invocation/day × 30 days = 150 requests/month
- Duration: 10 seconds avg
- Memory: 512MB = 0.5GB
- Compute: 150 × 10 × 0.5 = 750 GB-seconds

**Estimated cost**: 
- Requests: 150 / 1,000,000 × $0.20 = **$0.00003**
- Compute: 750 × $0.0000166667 = **$0.0125**
- **Total: $0.01/month** (rounds to free tier)

**Free tier**: 1M requests, 400,000 GB-seconds per month (permanent)

**Result**: Lambda cost is **$0** within free tier.

**Mitigation**:
- Use minimum memory (512MB sufficient for JSON API calls)
- Optimize code (reduce duration)
- Avoid over-scheduling (daily sufficient, not hourly)

### Glue

**Pricing**:
- Python Shell: $0.44/DPU-hour (1 DPU, max 1/16 DPU-hour increments)
- PySpark: $0.44/DPU-hour (2 DPU minimum)

**Estimated usage**:
- 1 Glue job per entity per day
- 5 entities × 30 days = 150 job runs/month
- Duration: 5 minutes avg = 0.083 hours
- Python Shell (1 DPU): 150 × 0.083 × $0.44 = **$5.48/month**

**Free tier**: None for Glue

**Result**: Glue is **largest cost driver**.

**Mitigation**:
- Use Python Shell (not PySpark) for small data volumes
- Optimize job runtime (read only required partitions)
- Batch multiple entities per job (reduce job count)
- Consider consolidating to 1 job/day processing all entities
- Alternative: Use Lambda for small transformations (stay in free tier)

**Optimized approach**: Single Glue job processing all entities
- 1 job/day × 30 days = 30 runs
- Duration: 10 minutes = 0.167 hours
- Cost: 30 × 0.167 × $0.44 = **$2.20/month**

### Athena

**Pricing**:
- $5 per TB scanned

**Estimated usage**:
- Processed layer: 500MB
- Analytics layer: 200MB
- dbt daily run queries processed layer: 500MB/query
- 30 dbt runs/month × 500MB = 15GB scanned
- Ad-hoc analyst queries: 5 queries × 200MB = 1GB
- **Total: 16GB/month scanned**

**Estimated cost**: 16GB / 1024GB × $5 = **$0.08/month**

**Mitigation**:
- Parquet columnar format (scan only required columns)
- Partition pruning (WHERE date = '2026-09-14')
- LIMIT queries during development
- Use views/CTEs to avoid repeated scans
- Incremental dbt models (reduce full table scans)

**Free tier**: None for Athena

### Glue Data Catalog

**Pricing**:
- First 1M objects free
- $1 per 100K objects after

**Estimated usage**:
- 5 entities × 90 days partitions = 450 partitions
- ~20 tables (staging, dimensions, facts, marts)
- **Total: < 500 objects**

**Estimated cost**: **$0** (within free tier)

### CloudWatch Logs

**Pricing**:
- $0.50/GB ingested
- $0.03/GB/month stored

**Estimated usage**:
- Lambda: 100MB/month
- Glue: 200MB/month
- dbt: 50MB/month
- **Total: 350MB/month ingested**
- Retention: 14-30 days (negligible storage cost)

**Estimated cost**: 
- Ingestion: 0.35GB × $0.50 = **$0.175/month**
- Storage: 0.35GB × $0.03 = **$0.01/month**
- **Total: $0.19/month**

**Free tier**: 5GB ingestion, 5GB storage per month (permanent)

**Result**: CloudWatch is **$0** within free tier.

**Mitigation**:
- Structured JSON logs (compact)
- Avoid logging full payloads
- Aggressive retention (7-14 days)
- Archive to S3 if long-term storage needed

### CloudWatch Metrics

**Pricing**:
- First 10 custom metrics free
- $0.30/metric/month after

**Estimated usage**:
- 5-10 custom metrics (RecordsIngested, RejectionRate, etc.)

**Estimated cost**: **$0** (within free tier)

### CloudWatch Alarms

**Pricing**:
- First 10 alarms free
- $0.10/alarm/month after

**Estimated usage**:
- 5-10 alarms (ingestion failure, processing failure, quality alerts)

**Estimated cost**: **$0** (within free tier)

### Secrets Manager

**Pricing**:
- $0.40/secret/month
- $0.05 per 10K API calls

**Estimated usage**:
- 5 API credentials = 5 secrets
- 150 Lambda invocations/month = 150 API calls

**Estimated cost**:
- Secrets: 5 × $0.40 = **$2.00/month**
- API calls: 150 / 10,000 × $0.05 = **$0.00075**
- **Total: $2.00/month**

**Alternative**: SSM Parameter Store (free for standard parameters)

**Trade-off**: Secrets Manager provides rotation, versioning, encryption. SSM Parameter Store is simpler and free but lacks automatic rotation.

**Decision**: Use SSM Parameter Store initially, migrate to Secrets Manager if rotation needed.

**Revised cost with SSM**: **$0**

### EventBridge (CloudWatch Events)

**Pricing**:
- First 1M events free (permanently)
- $1 per million events after

**Estimated usage**:
- 5 scheduled rules (1/day each) = 5 events/day = 150 events/month

**Estimated cost**: **$0** (within free tier)

### Data Transfer

**Pricing**:
- Data transfer IN: Free
- Data transfer OUT to Internet: $0.09/GB (first 10TB)
- Data transfer between services in same region: Free

**Estimated usage**:
- All data stays in AWS (Lambda → S3, Glue → S3, Athena → S3)
- No data egress to Internet (except dbt run from local/EC2)
- dbt queries download minimal results (~1MB/month)

**Estimated cost**: **$0**

**Mitigation**:
- Keep all resources in same region (us-east-1)
- Avoid downloading large datasets to local machine
- Run dbt in AWS (Lambda, EC2, Fargate) to avoid egress

## Monthly Cost Estimate

| Service | Usage | Cost |
|---------|-------|------|
| S3 Storage | 2.2GB | $0.05 |
| Lambda | 150 invocations | $0.00 (free tier) |
| Glue (optimized) | 30 job runs × 10min | $2.20 |
| Athena | 16GB scanned | $0.08 |
| Glue Catalog | 500 objects | $0.00 (free tier) |
| CloudWatch Logs | 350MB | $0.00 (free tier) |
| CloudWatch Metrics | 10 metrics | $0.00 (free tier) |
| CloudWatch Alarms | 10 alarms | $0.00 (free tier) |
| SSM Parameter Store | 5 parameters | $0.00 |
| EventBridge | 150 events | $0.00 (free tier) |
| Data Transfer | In-region only | $0.00 |
| **Total** | | **$2.33/month** |

**Result**: Well under $10 target. **$28/year**.

## Cost Growth Projection

**6 months**:
- S3: 5GB = $0.12
- Glue: Same = $2.20
- Athena: 20GB scanned = $0.10
- **Total: $2.42/month**

**1 year**:
- S3: 8GB = $0.18
- Glue: Same = $2.20
- Athena: 25GB scanned = $0.12
- **Total: $2.50/month**

**Scaling**: Cost grows slowly with data volume. Glue dominates cost.

## Cost Alarms

### Budget Alarm

**AWS Budgets**:
- Set budget: $5/month
- Alert threshold: 80% ($4)
- Alert at 100% ($5)

**Notification**: Email (SNS)

**Cost**: First 2 budgets free, $0.02/day per budget after

### CloudWatch Cost Anomaly Detection

**AWS Cost Anomaly Detection**:
- ML-based anomaly detection
- Alerts on unexpected cost spikes
- Free service

**Configuration**:
- Monitor CloudLake resources (tag-based)
- Alert threshold: $2 above expected

## Cost Mitigation Strategies

### S3 Lifecycle Policies

**Raw layer**:
```hcl
resource "aws_s3_bucket_lifecycle_configuration" "data_lake" {
  bucket = aws_s3_bucket.data_lake.id

  rule {
    id     = "raw_layer_transition"
    status = "Enabled"
    
    filter {
      prefix = "raw/"
    }
    
    transition {
      days          = 30
      storage_class = "STANDARD_IA"
    }
    
    expiration {
      days = 90
    }
  }
  
  rule {
    id     = "processed_layer_retention"
    status = "Enabled"
    
    filter {
      prefix = "processed/"
    }
    
    expiration {
      days = 365
    }
  }
}
```

**Savings**: Transition to IA after 30 days saves 50% storage cost. Delete after 90 days eliminates cost.

### Athena Query Optimization

**Partition pruning**:
```sql
-- Bad: Full table scan
SELECT * FROM fact_order;

-- Good: Partition filter
SELECT * FROM fact_order
WHERE order_date >= DATE '2026-09-01';
```

**Savings**: 90% reduction in data scanned (30 days vs 365 days)

**Column selection**:
```sql
-- Bad: Scan all columns
SELECT * FROM fact_order
WHERE order_date = DATE '2026-09-14';

-- Good: Select only needed columns
SELECT order_id, customer_id, revenue
FROM fact_order
WHERE order_date = DATE '2026-09-14';
```

**Savings**: Parquet columnar format scans only selected columns. 70% reduction typical.

**LIMIT during development**:
```sql
SELECT * FROM fact_order LIMIT 100;
```

**Savings**: Still scans full table, but faster. Combine with partition filter.

### Glue Job Optimization

**Reduce job frequency**:
- Process all entities in single job (not 5 separate jobs)
- Daily schedule sufficient (not hourly)

**Savings**: $5.48 → $2.20 (60% reduction)

**Optimize runtime**:
- Read only required partition (not full table)
- Use pushdown predicates
- Avoid unnecessary transformations

**Example**:
```python
# Bad: Read all data
df = spark.read.json("s3://bucket/raw/orders/")

# Good: Read specific partition
df = spark.read.json("s3://bucket/raw/orders/year=2026/month=09/day=14/")
```

**Savings**: 90% reduction in read time, proportional job duration reduction

### Lambda Optimization

**Use minimum memory**:
- 512MB sufficient for API calls and JSON parsing
- Higher memory = higher cost (but faster execution)

**Optimize duration**:
- Reuse connections (requests.Session)
- Stream large responses
- Avoid unnecessary processing

**Free tier coverage**: 400K GB-seconds/month. Current usage: 750 GB-seconds. Well within limit.

### Avoid Unnecessary Services

**Not using**:
- NAT Gateway: $32/month
- RDS: $15+/month minimum
- Redshift: $180+/month minimum
- EKS: $72/month control plane + nodes
- Managed Airflow (MWAA): $300+/month

**Serverless architecture**: Only pay when running. No idle resource cost.

## Cost Monitoring

### AWS Cost Explorer

**Enable**: Free service, available by default

**Usage**:
- Daily cost breakdown by service
- Monthly cost trends
- Filter by tag (Project=cloudlake)
- Forecast future costs

### Tagging Strategy

**Required tags**:
```hcl
tags = {
  Project     = "cloudlake"
  Environment = "prod"
  ManagedBy   = "terraform"
  CostCenter  = "data-platform"
}
```

**Cost allocation tags**:
- Enable in AWS Billing console
- Group costs by Project, Environment, CostCenter

### CloudWatch Dashboard (Cost Widget)

**Metric**: AWS Cost and Usage metrics

**Widget**: Daily cost over last 30 days

**Alert**: Anomaly detection

## Alternative Architecture Trade-offs

### Option 1: Lambda-Only (No Glue)

**Architecture**: Lambda processes raw → Parquet (using PyArrow)

**Pros**:
- Eliminates $2.20 Glue cost
- Simpler architecture

**Cons**:
- Lambda 15min timeout (may not scale)
- Lambda 10GB memory max (processing limits)
- No Glue Crawler for schema discovery
- Manual catalog management

**When viable**: Data volume < 100MB/day, transformation runtime < 10min

**Cost**: $0 (free tier) → **Save $2.20/month**

**Decision for CloudLake**: Consider for Phase 1 implementation. Evaluate Glue vs Lambda based on actual data volume.

### Option 2: Local dbt (No Cloud Compute)

**Architecture**: Run dbt from local machine

**Pros**:
- No compute cost (Athena queries only)
- Simpler development workflow

**Cons**:
- Not automated (manual dbt run)
- Not reproducible CI/CD
- Data egress from AWS (minimal)

**Cost**: $0 dbt compute → **Same total cost**

**Decision for CloudLake**: Use local dbt initially. Move to AWS (Lambda, EC2, GitHub Actions runner) for CI/CD phase.

### Option 3: DuckDB Athena Alternative

**Architecture**: Download Parquet to local, query with DuckDB

**Pros**:
- Free queries (no Athena cost)
- Faster for small datasets

**Cons**:
- Data egress cost (minimal for small data)
- Not multi-user (local only)
- Defeats cloud platform purpose

**Cost**: Save $0.08 Athena → **$2.25/month total**

**Decision for CloudLake**: Not appropriate. Athena is core to portfolio (demonstrates cloud query layer).

## Cost Optimization Checklist

- [ ] S3 lifecycle policies configured (transition to IA, expiration)
- [ ] Athena queries use partition filters
- [ ] Athena queries select specific columns (not SELECT *)
- [ ] Glue jobs process single partition (not full table scan)
- [ ] Consolidate Glue jobs (5 jobs → 1 job)
- [ ] Lambda uses minimum memory (512MB)
- [ ] CloudWatch Logs retention 14 days (not indefinite)
- [ ] Use SSM Parameter Store (not Secrets Manager initially)
- [ ] All resources in same region (avoid data transfer)
- [ ] Tag all resources for cost tracking
- [ ] Enable AWS Budgets ($5/month budget, 80% alert)
- [ ] Enable AWS Cost Anomaly Detection
- [ ] Review AWS Cost Explorer monthly

## Destroy Procedure

**Critical**: Ability to tear down infrastructure when not in use.

**Terraform destroy**:
```bash
terraform destroy
```

**Destroys**:
- S3 buckets (with versioning, may need force-destroy)
- Lambda functions
- Glue jobs, crawlers, catalog
- IAM roles
- CloudWatch log groups (with retention)
- EventBridge rules

**Does not destroy**:
- S3 data (if prevent_destroy or versioning enabled)

**Force destroy S3**:
```hcl
resource "aws_s3_bucket" "data_lake" {
  bucket = "cloudlake-data-${data.aws_caller_identity.current.account_id}"
  
  force_destroy = true  # WARNING: Deletes all objects
}
```

**Cost after destroy**: $0 (except S3 data if preserved)

**Use case**: Pause project for 3 months → destroy infrastructure → save $7/month → recreate when resuming

## Annual Cost Summary

**Monthly**: $2.33  
**Annual**: $28

**Comparison**:
- Netflix subscription: $15/month
- GitHub Pro: $4/month
- AWS CloudLake: $2.33/month

**ROI**: Portfolio project demonstrating $100K+ salary skills for $28/year.

## Cost-Effective Architecture Validation

CloudLake architecture achieves:
- ✅ Serverless (no idle cost)
- ✅ Pay-per-use (no fixed costs)
- ✅ Free tier maximization (Lambda, CloudWatch, Glue Catalog)
- ✅ Under $10/month target ($2.33 actual)
- ✅ Scalable (cost grows slowly with data volume)
- ✅ Destroyable (can tear down between usage)

**Principle**: Choose services with generous free tiers. Optimize for low baseline cost. Scale only when necessary.
