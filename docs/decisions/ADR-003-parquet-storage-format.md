# ADR-003: Parquet Storage Format

## Status
Accepted

## Context
Processed and analytics layers need a storage format optimized for analytical queries. Options include JSON, CSV, Avro, Parquet, and ORC.

## Decision
Use **Parquet with Snappy compression** for processed and analytics layers.

## Alternatives Considered

### Alternative 1: JSON (Keep Original Format)
- **Pros**: Simple, human-readable, no transformation needed
- **Cons**: Text format, no column pruning, 3-5x larger, slow Athena queries
- **Rejected**: Poor query performance, high storage cost, not production-appropriate

### Alternative 2: CSV
- **Pros**: Simple, widely compatible
- **Cons**: No schema enforcement, text-based, no column pruning, type ambiguity
- **Rejected**: Lacks schema, poor performance

### Alternative 3: Avro
- **Pros**: Schema evolution support, row-based, splittable
- **Cons**: Row-based (not optimal for analytics), less Athena-optimized than Parquet
- **Rejected**: Not columnar, less common in analytics stacks

### Alternative 4: ORC (Optimized Row Columnar)
- **Pros**: Columnar, highly compressed, Hive-optimized
- **Cons**: Less ecosystem support than Parquet, more Hadoop-specific
- **Rejected**: Parquet more widely adopted in cloud-native stacks

### Alternative 5: Parquet with Gzip Compression
- **Pros**: Higher compression ratio than Snappy
- **Cons**: Slower decompression, not splittable
- **Rejected**: Snappy balances compression and query speed

## Rationale

**Parquet advantages**:
- **Columnar storage**: Athena reads only required columns (not entire row)
- **Compression**: 3:1 to 5:1 compression vs JSON
- **Type safety**: Schema embedded in file
- **Predicate pushdown**: Filter before reading data
- **Industry standard**: Athena, Spark, dbt all optimized for Parquet

**Snappy compression**:
- Fast compression/decompression
- Splittable (parallel processing)
- Good balance: 70% of Gzip compression at 3x speed

**Use cases where Parquet excels**:
```sql
-- Column selection: Only scans 'revenue' column
SELECT SUM(revenue) FROM fact_order;

-- Partition + column pruning
SELECT customer_id, revenue 
FROM fact_order 
WHERE order_date = '2026-09-14';
```

## Consequences

**Positive**:
- Athena query cost reduced 70-90% vs JSON (column pruning + compression)
- Query performance improved 5-10x vs text formats
- Storage cost reduced 3x vs JSON
- Industry-standard format demonstrates best practices

**Negative**:
- Not human-readable (requires tools to inspect)
- Requires transformation step (Glue job) from raw JSON/CSV
- Adds processing complexity vs keeping JSON

**Acceptable trade-offs**:
- Raw layer preserves JSON for inspection
- Parquet inspection via Athena, Glue, or local tools (DuckDB, pandas)
- Processing cost ($2.20/month) justified by query savings

## Validation
- JSON 500MB → Parquet 150MB (3:1 compression)
- Athena query: Full table JSON scan 500MB ($0.0025), Parquet scan 50MB ($0.00025)
- Query time: JSON 12s, Parquet 3s (4x faster)

## References
- [Athena Columnar Storage Performance](https://docs.aws.amazon.com/athena/latest/ug/columnar-storage.html)
- [Parquet Documentation](https://parquet.apache.org/docs/)
