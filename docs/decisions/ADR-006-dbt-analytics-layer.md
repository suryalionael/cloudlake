# ADR-006: dbt Analytics Layer

## Status
Accepted

## Context
Need transformation layer to convert processed data into analytics-ready models. Options include custom Python scripts, SQL stored procedures, Spark transformations, or dbt.

## Decision
Use **dbt (data build tool)** with Athena adapter for all analytics transformations.

Three-layer dbt project:
- Staging (1:1 with sources)
- Dimensions/Facts (star schema)
- Marts (denormalized, aggregated)

## Alternatives Considered

### Alternative 1: Python Scripts (Pandas/PySpark)
- **Pros**: Full programming flexibility, Python ecosystem
- **Cons**: No dependency management, no testing framework, harder to review
- **Rejected**: dbt is standard for analytics engineering

### Alternative 2: Glue Jobs for All Transformations
- **Pros**: Unified platform (Glue for ETL + transformations)
- **Cons**: Mixing ETL and analytics logic, less analyst-friendly (Python not SQL)
- **Rejected**: Separation of concerns (ETL vs analytics)

### Alternative 3: Athena Views (No Transformation Tool)
- **Pros**: Simple, no additional tool
- **Cons**: No testing, no lineage, no documentation, no version control
- **Rejected**: Not production-grade, no data quality enforcement

### Alternative 4: AWS Glue DataBrew
- **Pros**: Visual ETL, no-code transformations
- **Cons**: Cost per node-hour, not SQL-based, less analytics-focused
- **Rejected**: Cost, less standard in analytics engineering roles

### Alternative 5: Spark SQL in Glue
- **Pros**: Distributed processing, Spark ecosystem
- **Cons**: Overkill for data volume, higher cost (2 DPU minimum), slower iteration
- **Rejected**: Volume does not justify distributed compute

## Rationale

**dbt advantages**:
- **SQL-based**: Analysts understand SQL, not Python
- **Testing framework**: Built-in tests (unique, not_null, relationships, custom)
- **Lineage**: Automatic dependency graph (DAG)
- **Documentation**: Auto-generated docs from schema.yml
- **Incremental models**: Optimize performance for large tables (future)
- **Version control**: Models are code (Git)
- **Industry standard**: Most analytics engineering jobs require dbt

**Three-layer structure**:
```
Staging    → Clean, rename, standardize (1:1 with sources)
Dimensions → Descriptive attributes (customers, products, stores)
Facts      → Measurements (orders, line items)
Marts      → Business-ready (daily sales, customer metrics)
```

**Athena adapter**:
- dbt-athena-community maintained
- Supports Athena-specific features (partitioning, CTAS)
- Runs queries via Athena (no separate compute)

## Consequences

**Positive**:
- SQL transformations reviewable by analysts (not just engineers)
- Data quality tests enforce validity (fail pipeline on bad data)
- Documentation generated from code (dbt docs generate)
- Incremental models reduce processing time (future optimization)
- Demonstrates analytics engineering best practices

**Negative**:
- dbt runs on local machine or CI/CD runner (not serverless by default)
- Athena query cost for dbt runs (~$0.08/month, already accounted)
- Learning curve for dbt-specific syntax (ref, source, macros)

**Where dbt runs**:
- **Phase 1-8**: Local machine (dbt run from laptop)
- **Phase 9+**: GitHub Actions (automated daily run)
- **Future**: AWS Lambda (dbt in Docker container) or EC2

## Validation
- dbt project structure follows Fishtown Analytics best practices
- Staging models: 5 (one per entity)
- Dimension models: 3 (customer, product, store)
- Fact models: 1 (order at line item grain)
- Mart models: 4 (daily sales, product performance, customer metrics, store performance)
- Tests: 45+ (generic + custom)

## References
- [dbt Documentation](https://docs.getdbt.com/)
- [dbt-athena Adapter](https://github.com/dbt-athena/dbt-athena)
- [dbt Best Practices](https://docs.getdbt.com/guides/best-practices)
