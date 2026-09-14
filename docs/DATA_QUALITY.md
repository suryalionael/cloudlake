# Data Quality Strategy

## Quality Philosophy

Data quality is enforced at multiple stages, not just at the end. Each layer validates its inputs and outputs. Failures are detected early, logged, and escalated.

## Quality Layers

```
Source Data
    ↓ [Ingestion Validation]
Raw Layer
    ↓ [Processing Validation]
Processed Layer
    ↓ [dbt Tests]
Analytics Layer
    ↓ [Business Rules]
Consumption
```

## Ingestion Validation (Lambda)

### Purpose
Prevent bad data from entering the data lake.

### Checks

**HTTP Response Validation**:
- Status code 200
- Response body exists
- Content-Type is application/json

**JSON Structure Validation**:
- Valid JSON syntax
- Expected root structure (array or object)
- Not empty

**Schema Validation**:
- Required fields present
- Field types match expectation (string, number, etc.)
- No unexpected null values in required fields

**Timestamp Validation**:
- Date fields parse correctly
- Dates are not in future
- created_at <= updated_at

### Failure Behavior

**Hard failures** (do not write to S3):
- HTTP error (4xx, 5xx)
- Invalid JSON
- Missing required fields
- Invalid timestamp format

**Soft failures** (write to S3, log warning):
- Optional field missing
- Unexpected additional field
- Out-of-range value (log but preserve)

### Implementation

Python schema validation library (e.g., Pydantic, jsonschema, or manual validation).

Example structure:
```python
def validate_customer_schema(data):
    required_fields = ['customer_id', 'email', 'first_name', 'last_name', 'country', 'created_at', 'updated_at']
    for field in required_fields:
        if field not in data:
            raise ValueError(f"Missing required field: {field}")
    # Type and format checks...
```

## Processing Validation (Glue)

### Purpose
Ensure raw data transforms correctly into typed, clean Parquet.

### Checks

**Type Conversion**:
- String fields trim whitespace
- Numeric fields convert without error
- Timestamp fields parse to datetime
- Boolean fields map correctly

**Range Validation**:
- price > 0
- quantity > 0
- total_amount >= 0
- Dates within reasonable range (e.g., 1990 - now)

**Referential Integrity** (where feasible):
- order.customer_id exists in customers
- order_item.order_id exists in orders
- order_item.product_id exists in products

**Duplicate Detection**:
- Primary key uniqueness within batch
- Compare against previous partition (if applicable)

**Record Count Validation**:
- Input record count = output record count (minus rejected records)
- Log rejected record count
- Alert if rejection rate > threshold (e.g., 5%)

### Failure Behavior

**Hard failures** (abort job):
- Unparseable file format
- Critical schema mismatch (missing column)
- >10% records rejected

**Soft failures** (log and continue):
- Individual record validation failure (skip record, log details)
- Optional field parse error (set to null)

### Rejected Records

Write rejected records to separate S3 path:
```
s3://cloudlake-data-{account_id}/rejected/
    {entity}/year=YYYY/month=MM/day=DD/{timestamp}_rejected.json
```

Include rejection reason in metadata.

## dbt Tests

### Purpose
Validate analytical transformations and business logic.

### Generic Tests

**Staging models**:
```yaml
models:
  - name: stg_customers
    columns:
      - name: customer_id
        tests:
          - not_null
          - unique
      - name: email
        tests:
          - not_null
          - unique
      - name: country
        tests:
          - accepted_values:
              values: ['US', 'CA', 'UK', 'AU']
```

**Dimensions**:
```yaml
models:
  - name: dim_product
    columns:
      - name: product_id
        tests:
          - not_null
          - unique
      - name: current_price
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "> 0"
      - name: category
        tests:
          - not_null
          - accepted_values:
              values: ['Electronics', 'Apparel', 'Home', 'Sports', 'Books']
```

**Facts**:
```yaml
models:
  - name: fact_order
    columns:
      - name: order_item_id
        tests:
          - not_null
          - unique
      - name: customer_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_customer')
              field: customer_id
      - name: product_id
        tests:
          - not_null
          - relationships:
              to: ref('dim_product')
              field: product_id
      - name: quantity
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: "> 0"
      - name: revenue
        tests:
          - not_null
          - dbt_utils.expression_is_true:
              expression: ">= 0"
```

### Custom Data Tests

**Revenue reconciliation**:
```sql
-- tests/assert_revenue_matches_line_total.sql
SELECT
    order_item_id,
    quantity * unit_price AS calculated_revenue,
    line_total AS reported_revenue
FROM {{ ref('fact_order') }}
WHERE ABS(quantity * unit_price - line_total) > 0.01
```

**Order total reconciliation**:
```sql
-- tests/assert_order_total_matches_line_items.sql
WITH order_totals AS (
    SELECT
        order_id,
        SUM(line_total) AS calculated_total
    FROM {{ ref('fact_order') }}
    GROUP BY order_id
),
reported_totals AS (
    SELECT DISTINCT
        order_id,
        order_total_amount AS reported_total
    FROM {{ ref('fact_order') }}
)
SELECT
    o.order_id,
    o.calculated_total,
    r.reported_total
FROM order_totals o
JOIN reported_totals r ON o.order_id = r.order_id
WHERE ABS(o.calculated_total - r.reported_total) > 0.01
```

**No future dates**:
```sql
-- tests/assert_no_future_dates.sql
SELECT order_id, order_date
FROM {{ ref('fact_order') }}
WHERE order_date > CURRENT_DATE
```

**Customer has orders**:
```sql
-- tests/assert_customers_with_orders_exist_in_dimension.sql
SELECT DISTINCT f.customer_id
FROM {{ ref('fact_order') }} f
LEFT JOIN {{ ref('dim_customer') }} c ON f.customer_id = c.customer_id
WHERE c.customer_id IS NULL
```

### Test Severity

**Error** (fail dbt run):
- Primary key violations
- Referential integrity violations
- Revenue reconciliation failures

**Warn** (log but continue):
- Accepted_values violations on new categories
- Margin percent out of expected range
- Record count lower than expected

Configuration:
```yaml
tests:
  - name: category_values
    config:
      severity: warn
```

## Business Rules

### Rule Definitions

| Rule | Description | Level | Action |
|------|-------------|-------|--------|
| Price > 0 | Product price must be positive | Error | Reject record |
| Quantity > 0 | Order quantity must be positive | Error | Reject record |
| Order date not future | Order date <= today | Error | Reject record |
| Customer email format | Valid email regex | Error | Reject record |
| Revenue = qty * price | Line total matches calculation | Error | Fail dbt test |
| Margin reasonable | Margin between -10% and 90% | Warning | Log anomaly |
| Daily order count | Orders > 100/day | Warning | Alert if violated |
| Customer has name | First and last name not empty | Error | Reject record |

### Rule Implementation

**Ingestion**: Lambda validation function  
**Processing**: Glue job validation logic  
**Transformation**: dbt tests  
**Monitoring**: CloudWatch metrics + alarms

## Failure Detection

### Pipeline Failure

**Lambda failure**:
- CloudWatch alarm on Lambda error metric
- SNS notification (if configured)
- Next scheduled run retries

**Glue job failure**:
- CloudWatch alarm on Glue job failure
- Glue job bookmark prevents data loss
- Manual re-run or automatic retry

**dbt test failure**:
- dbt returns non-zero exit code
- CI/CD pipeline fails
- Logs show failed test details
- Analytics layer not updated

### Data Anomaly Detection

**Volume anomaly**:
- Metric: daily record count
- Alarm: count < 50% of 7-day average
- Action: Investigate source system

**Quality anomaly**:
- Metric: rejection rate
- Alarm: rejection rate > 5%
- Action: Review rejected records, check schema changes

**Freshness anomaly**:
- Metric: hours since last successful ingestion
- Alarm: > 26 hours (daily job missed)
- Action: Check Lambda/EventBridge, retry manually

## Idempotency

### Ingestion Idempotency

**Challenge**: Same API call made twice → duplicate records in raw layer

**Solution**: Deterministic S3 object keys

```
raw/customers/year=2026/month=09/day=14/2026-09-14T06-00-00Z_<run_id>.json
```

- Scheduled runs use fixed timestamp (e.g., 06:00 UTC)
- Manual runs use unique run_id (UUID)
- Rerunning scheduled job overwrites same object key
- No duplicate raw files for same scheduled run

**Trade-off**: Overwrites previous attempt. Acceptable because raw data source is upstream API, not S3.

### Processing Idempotency

**Challenge**: Reprocessing same raw partition → duplicate processed records

**Solution**: Partition overwrite mode

Glue job writes to partition:
```
processed/customers/year=2026/month=09/day=14/
```

Spark write mode: `overwrite` with `partitionOverwriteMode=dynamic`

Rerunning job replaces partition atomically. No duplicates.

### Transformation Idempotency

**Challenge**: Rerunning dbt → duplicate records in facts/marts

**Solution**: dbt full-refresh by default

```bash
dbt run --full-refresh
```

Drops and recreates tables. No incremental logic = no accumulation bugs.

For incremental models (future):
- Use unique_key to upsert
- Filter on order_date for incremental loads
- Idempotent: reprocessing same date replaces records

## Data Lineage Traceability

### Metadata Tracking

**Raw layer**:
- Filename includes ingestion timestamp and run_id
- Object metadata tags: ingestion_date, source_system

**Processed layer**:
- Glue job logs: input path, output path, record counts
- Partition includes processing date

**Analytics layer**:
- dbt run logs: model dependencies, row counts, test results
- dbt_run_results.json captures lineage

### Tracing Flow

Analyst sees unexpected value in `mart_daily_sales`:
1. Check dbt logs for `mart_daily_sales` last run time
2. Identify source models: `fact_order`, `dim_customer`, etc.
3. Check Glue job logs for processed layer write time
4. Identify raw S3 object by partition date
5. Download raw JSON for inspection
6. Compare to source API response (if logged)

### Run ID Propagation

Lambda generates UUID `run_id` on invocation.

Pass run_id through pipeline:
- Lambda → S3 object key metadata
- Glue reads from S3 metadata, writes to processed metadata
- dbt logs reference partition date (indirect link to run_id)

Not fully automated initially. Manual trace via CloudWatch logs + S3 metadata.

Future enhancement: Explicit run_id column in all tables.

## Data Quality Metrics

### Key Metrics

| Metric | Definition | Target | Alert Threshold |
|--------|------------|--------|-----------------|
| Ingestion success rate | Successful Lambda runs / Total runs | 99% | < 95% |
| Processing success rate | Successful Glue jobs / Total jobs | 99% | < 95% |
| dbt test pass rate | Passed tests / Total tests | 100% | < 100% |
| Record rejection rate | Rejected records / Total records | < 1% | > 5% |
| Data freshness | Hours since last update | < 2 hours | > 26 hours |
| Schema drift events | Schema changes detected | 0 | > 0 |

### Reporting

Weekly data quality report (automated query):
```sql
SELECT
    'Ingestion' AS stage,
    COUNT(*) AS total_runs,
    SUM(CASE WHEN status = 'success' THEN 1 ELSE 0 END) AS successful_runs,
    AVG(CASE WHEN status = 'success' THEN 1.0 ELSE 0.0 END) * 100 AS success_rate_pct
FROM cloudwatch_logs_parsed
WHERE log_group = '/aws/lambda/cloudlake-ingestion'
  AND date >= CURRENT_DATE - INTERVAL '7' DAY
```

Future: CloudWatch dashboard with quality metrics.

## Recovery Procedures

### Scenario: Ingestion Failure

**Detection**: CloudWatch alarm on Lambda error

**Response**:
1. Check CloudWatch logs for error details
2. If API unavailable: wait for next scheduled run
3. If schema change: update Lambda validation logic, redeploy
4. If transient error: manually invoke Lambda

**Recovery**: No data loss. Next successful run ingests latest data.

### Scenario: Processing Failure

**Detection**: CloudWatch alarm on Glue job failure

**Response**:
1. Check Glue job logs for error
2. If schema mismatch: update Glue job schema, rerun
3. If bad data: inspect rejected records, fix upstream
4. If Glue bug: fix code, redeploy, rerun

**Recovery**:
1. Raw data preserved
2. Fix issue
3. Rerun Glue job on failed partition: `--date=2026-09-14`
4. Processed partition overwritten (idempotent)

### Scenario: dbt Test Failure

**Detection**: dbt run returns exit code 1

**Response**:
1. Check dbt logs for failed test
2. Query failing model to inspect data
3. Determine if upstream bug or bad source data

**Recovery**:
1. If upstream bug: fix Glue job, reprocess, rerun dbt
2. If source data issue: investigate API, may need manual correction
3. If dbt logic bug: fix dbt model, rerun

**Trade-off**: Analytics layer not updated until tests pass. Ensures bad data does not propagate.

### Scenario: Duplicate Records

**Detection**: dbt test `unique` fails

**Response**:
1. Query fact table for duplicates
2. Trace to processed layer (check record count)
3. Trace to raw layer (check for duplicate files)

**Recovery**:
1. Identify root cause (non-idempotent ingestion? processing bug?)
2. Delete duplicate partition in processed layer
3. Rerun processing on single raw partition
4. Rerun dbt

### Scenario: Late-Arriving Data

**Not currently handled**. Batch design assumes daily cutoff.

Late data (order arrives after daily processing) will appear in next day's partition.

Historical aggregates (e.g., September total revenue) will be understated if late data not reprocessed.

Future enhancement:
- Incremental dbt models with lookback window
- Reprocess last N days on each run
- Trade-off: increased compute cost

## Quality Testing Strategy

### Local Testing

**Unit tests** (Python):
- Lambda validation functions
- Glue transformation logic
- Test with sample JSON/CSV files
- Assert expected output schema

**dbt tests**:
- Run against local dev environment (DuckDB or sample Athena data)
- Validate model logic before deploying

### Integration Testing

**End-to-end test**:
1. Ingest test dataset (small, known values)
2. Run Glue processing
3. Run dbt transformations
4. Query marts
5. Assert expected aggregates

Example:
- 10 customers, 5 products, 100 orders
- Expected mart_daily_sales total_revenue = $X
- Query and compare

**Automated in CI/CD**: Future phase

### Production Validation

**Smoke tests** after deployment:
1. Manually trigger Lambda with test API endpoint
2. Verify raw file written
3. Manually trigger Glue job on test partition
4. Verify processed Parquet exists
5. Run dbt on test data
6. Query test mart

**Automated monitoring**: CloudWatch alarms provide continuous validation

## Quality vs. Cost Trade-offs

**Not implemented** (too expensive for portfolio):
- Great Expectations (third-party library): comprehensive but adds complexity
- AWS Glue DataBrew: visual data quality, but $$ per node-hour
- Exhaustive cross-partition duplicate checks (requires full table scans)

**Implemented** (appropriate for scope):
- Simple Python validation in Lambda (free within Lambda runtime)
- PySpark validation in Glue (minimal DPU cost)
- dbt built-in tests (free, runs in Athena queries)
- CloudWatch alarms (minimal cost)

**Principle**: Use native capabilities of chosen services. Avoid third-party SaaS for quality when built-in options exist.
