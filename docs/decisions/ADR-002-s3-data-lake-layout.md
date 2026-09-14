# ADR-002: S3 Data Lake Layout

## Status
Accepted

## Context
S3 will serve as the data lake foundation. Need to determine the directory structure, partitioning strategy, and naming conventions that balance query performance, cost, and operational simplicity.

## Decision
Implement three-layer data lake:
```
raw/        - Immutable source data (JSON/CSV)
processed/  - Typed, cleaned Parquet
analytics/  - dbt transformation output
```

Date-based partitioning: `year=YYYY/month=MM/day=DD/`

## Alternatives Considered

### Alternative 1: Two-Layer (Raw + Analytics)
- Skip processed layer, transform directly from raw to analytics
- **Rejected**: No intermediate recovery point, harder to debug, mixing storage formats

### Alternative 2: Five-Layer (Bronze/Silver/Gold + Staging + Archive)
- Additional intermediate layers
- **Rejected**: Over-engineered for scale, adds complexity without benefit

### Alternative 3: Hive-Style Partitioning by Entity Attributes
- Partition by customer_id, product_category, etc.
- **Rejected**: Creates excessive small files, date is primary query filter

### Alternative 4: No Partitioning
- Flat directory structure
- **Rejected**: Athena scans entire dataset, high cost, poor performance

## Rationale

**Three layers**:
- **Raw**: Source of truth, recoverable history, original format preserved
- **Processed**: Query-optimized format, typed schema, quality-validated
- **Analytics**: Business-ready, denormalized, pre-aggregated

**Date partitioning**:
- Aligns with typical analytical queries ("last 30 days", "this month")
- Enables S3 lifecycle policies (delete after 90 days)
- Athena partition pruning reduces scan cost
- Simple to understand and maintain

**Naming conventions**:
- Entity name in path for clarity
- Hive-style partition keys for Athena compatibility
- Timestamp + run_id in filename for idempotency

## Consequences

**Positive**:
- Clear separation of concerns (raw vs processed vs analytics)
- Raw data immutability enables reprocessing
- Partition pruning reduces Athena query cost 90%+
- Lifecycle policies control storage cost

**Negative**:
- Three copies of data (raw, processed, analytics) increases storage cost
- Date partitioning not optimal for "customer by ID" queries (acceptable: not primary use case)

**Mitigation**:
- Compression (Parquet Snappy) reduces processed/analytics size
- Lifecycle policies delete old raw data
- Total storage cost still < $0.20/month

## Validation
- Athena query with partition filter: scans 1GB instead of 30GB
- Storage cost for 6 months: ~$0.12/month
- Reprocessing scenario tested: raw → processed regeneration successful
