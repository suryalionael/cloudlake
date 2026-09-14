# ADR-005: Athena Query Layer

## Status
Accepted

## Context
Need SQL query interface over S3 data lake. Options include Athena, Redshift, Redshift Spectrum, self-hosted Presto/Trino, or no query layer (direct S3 access).

## Decision
Use **Amazon Athena** as the SQL query engine for processed and analytics layers.

No Redshift. No self-hosted query engine.

## Alternatives Considered

### Alternative 1: Amazon Redshift Serverless
- **Pros**: Full data warehouse, consistent performance, materialized views
- **Cons**: $300+/month minimum usage, overkill for 10K orders/day
- **Rejected**: Excessive cost, not justified by query workload

### Alternative 2: Redshift Spectrum
- **Pros**: Query S3 from Redshift, hybrid approach
- **Cons**: Requires Redshift cluster ($180+/month), adds complexity
- **Rejected**: Still requires expensive base cluster

### Alternative 3: Self-Hosted Presto/Trino on EC2
- **Pros**: Open source, powerful query engine
- **Cons**: $30-50/month EC2 cost, operational overhead, no catalog integration
- **Rejected**: Operational complexity, cost not justified

### Alternative 4: Local DuckDB
- **Pros**: Free, fast for small data, local execution
- **Cons**: Requires downloading data from S3, not cloud-native, single-user
- **Rejected**: Defeats cloud platform purpose, not shareable

### Alternative 5: No Query Layer (Direct S3 Access)
- **Pros**: Zero query cost
- **Cons**: No SQL interface, requires Python/Pandas, not analyst-friendly
- **Rejected**: SQL interface is requirement for analytics enablement

## Rationale

**Athena advantages**:
- **Serverless**: No clusters to manage, pay per query
- **Cost**: $5/TB scanned (16GB/month = $0.08)
- **Presto-based**: Standard SQL, compatible with BI tools
- **S3-native**: Direct query over data lake, no data loading
- **Glue Catalog integration**: Automatic schema discovery
- **Partition pruning**: Reduces cost via date filters

**Appropriate for workload**:
- Batch analytics (not real-time)
- Low concurrency (5-10 users, not 100s)
- Small-to-medium data (GBs, not TBs per query)
- Intermittent queries (not continuous)

**Cost example**:
```sql
-- Without partition pruning: scans 30GB = $0.15
SELECT * FROM fact_order;

-- With partition pruning: scans 1GB = $0.005
SELECT * FROM fact_order 
WHERE order_date = DATE '2026-09-14';
```

**dbt integration**:
- dbt-athena adapter exists
- dbt models execute as Athena queries
- Incremental models supported

## Consequences

**Positive**:
- Cost-effective: $0.08/month for expected usage
- No operational overhead (serverless)
- Standard SQL interface for analysts
- BI tool compatible (Power BI, Tableau can connect)
- Demonstrates cloud query layer pattern

**Negative**:
- Query performance variable (not guaranteed like Redshift)
- Cost per query (not flat monthly rate) → requires partition discipline
- Limited optimization features vs Redshift (no materialized views, no sort keys)
- Concurrency limits (20 queries by default) → not issue for portfolio

**When to reconsider**:
- If query volume > 1TB/month → Redshift may be cheaper
- If need sub-second query latency → Redshift or caching layer
- If need high concurrency (50+ users) → Redshift

## Validation
- Estimated monthly scans: 16GB
- Cost: $0.08/month
- Query performance: 3-10 seconds for typical aggregations (acceptable)
- Redshift Serverless equivalent: $300+/month
- **Cost savings**: 99.97%

## References
- [Athena Pricing](https://aws.amazon.com/athena/pricing/)
- [Athena Performance Tuning](https://docs.aws.amazon.com/athena/latest/ug/performance-tuning.html)
- [Athena vs Redshift Decision Guide](https://aws.amazon.com/blogs/big-data/amazon-athena-vs-amazon-redshift/)
