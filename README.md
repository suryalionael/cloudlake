# CloudLake

**Cloud-Native Retail Data Platform**

> A portfolio project demonstrating production-grade cloud data engineering, analytics engineering, and infrastructure as code practices.

---

## 🎯 Project Status

**Phase**: 0 — Documentation & Architecture  
**Status**: ✅ Complete  
**Last Updated**: 2026-09-14

CloudLake is currently in the design phase. Architecture documentation is complete. No AWS resources have been deployed yet.

---

## 📋 Overview

CloudLake is a serverless data platform built on AWS that ingests multi-source retail data, preserves raw history, validates quality, transforms through dimensional models, and serves analytics via SQL.

The platform demonstrates:
- Cloud data lake architecture (S3 multi-layer design)
- Serverless data pipelines (Lambda, Glue)
- Analytics engineering (dbt dimensional modeling)
- Infrastructure as Code (Terraform)
- Data quality validation (multi-stage testing)
- Observability (CloudWatch logs, metrics, alarms)
- CI/CD for data (GitHub Actions)
- Cost optimization (< $10/month)

---

## 🏗️ Architecture

```
Data Sources (REST API, CSV)
           ↓
AWS Lambda (Ingestion)
           ↓
S3 Raw Layer (JSON/CSV, immutable)
           ↓
AWS Glue (ETL Processing)
           ↓
S3 Processed Layer (Parquet, typed)
           ↓
AWS Glue Data Catalog
           ↓
Amazon Athena (SQL Query)
           ↓
dbt (Transformations)
           ↓
S3 Analytics Layer (Marts)
           ↓
Analysts / BI Tools
```

**Supporting Infrastructure**:
- Terraform (IaC)
- GitHub Actions (CI/CD)
- CloudWatch (Observability)

---

## 🛠️ Tech Stack

**Cloud**: AWS (S3, Lambda, Glue, Athena, CloudWatch)  
**IaC**: Terraform  
**Data Transformation**: dbt  
**Languages**: Python, SQL, HCL  
**CI/CD**: GitHub Actions  
**Version Control**: Git

---

## 💾 Data Model

**Domain**: Fictional retail company

**Entities**:
- customers (50K records)
- products (5K records)
- stores (20 records)
- orders (10K/day)
- order_items (30K/day)

**Dimensional Model**:
- Staging layer (1:1 with sources)
- Dimensions (dim_customer, dim_product, dim_store)
- Fact (fact_order at line item grain)
- Marts (daily_sales, product_performance, customer_metrics, store_performance)

---

## 💰 Cost Profile

**Target**: < $10/month  
**Actual Estimate**: $2.33/month

| Service | Monthly Cost |
|---------|-------------|
| S3 Storage | $0.05 |
| Lambda | $0.00 (free tier) |
| Glue | $2.20 |
| Athena | $0.08 |
| CloudWatch | $0.00 (free tier) |
| **Total** | **$2.33** |

**Annual cost**: ~$28

---

## 📂 Repository Structure

```
cloudlake/
├── docs/
│   ├── PROJECT.md              # Business problem, scope
│   ├── DATA_CONTRACTS.md       # Entity schemas, quality rules
│   ├── AWS_DESIGN.md           # Cloud architecture, service justification
│   ├── DATA_MODEL.md           # dbt models, dimensional design
│   ├── DATA_QUALITY.md         # Validation strategy, testing
│   ├── OBSERVABILITY.md        # Logs, metrics, alarms
│   ├── SECURITY.md             # IAM, secrets, encryption
│   ├── COST.md                 # Budget analysis, optimization
│   ├── CICD.md                 # GitHub Actions pipelines
│   ├── PORTFOLIO.md            # Professional positioning
│   └── decisions/              # Architecture Decision Records
│       ├── ADR-001-cloud-platform-scope.md
│       ├── ADR-002-s3-data-lake-layout.md
│       ├── ADR-003-parquet-storage-format.md
│       ├── ADR-004-serverless-architecture.md
│       ├── ADR-005-athena-query-layer.md
│       ├── ADR-006-dbt-analytics-layer.md
│       └── ADR-007-terraform-iac.md
├── ROADMAP.md                  # Implementation phases
├── CURRENT.md                  # Current status
└── .gitignore
```

*(Infrastructure, source code, and dbt models will be added in future phases)*

---

## 🎯 Engineering Principles

1. Documentation before implementation
2. Infrastructure as Code
3. Raw data remains recoverable
4. Data transformations are reproducible
5. Data quality is part of the pipeline
6. Failures are observable
7. Idempotency is preferred
8. Least privilege security
9. Minimize cloud costs
10. Avoid unnecessary infrastructure

---

## 🚀 Roadmap

**Phase 0**: Documentation & Architecture ✅ (Complete)  
**Phase 1**: Local Data Foundation  
**Phase 2**: Infrastructure as Code (Terraform)  
**Phase 3**: Cloud Ingestion (Lambda)  
**Phase 4**: Data Processing (Glue)  
**Phase 5**: Athena & Catalog  
**Phase 6**: dbt Analytics Layer  
**Phase 7**: Data Quality  
**Phase 8**: Observability  
**Phase 9**: CI/CD  
**Phase 10**: Production Audit  
**Phase 11**: Portfolio Polish

See [ROADMAP.md](ROADMAP.md) for detailed phase breakdown.

---

## 📊 Portfolio Context

CloudLake complements existing portfolio projects:

**FraudLens**: Risk analytics, ML classification → CloudLake provides the platform that could feed such systems

**Toronto Mobility Intelligence**: BI dashboards, spatial analysis → CloudLake demonstrates how to build the data foundation

**CloudLake**: Data platform engineering, cloud infrastructure, analytics enablement

See [docs/PORTFOLIO.md](docs/PORTFOLIO.md) for detailed positioning.

---

## 🔒 Security & Compliance

- S3 encryption at rest (SSE-S3)
- HTTPS-only data transfer
- IAM least privilege roles
- Secrets stored in AWS Secrets Manager / SSM Parameter Store
- No credentials in Git
- GitHub Actions OIDC (no long-lived keys)

See [docs/SECURITY.md](docs/SECURITY.md) for complete security architecture.

---

## 📈 Data Quality

Multi-stage validation:
- **Ingestion**: Schema validation, required field checks
- **Processing**: Type conversion, range validation, referential integrity
- **Transformation**: dbt tests (unique, not_null, relationships, custom)

Rejection handling: Bad records quarantined, not propagated

See [docs/DATA_QUALITY.md](docs/DATA_QUALITY.md) for validation strategy.

---

## 🔍 Observability

- **Logs**: Structured JSON in CloudWatch
- **Metrics**: Custom metrics for record counts, rejection rates, duration
- **Alarms**: Ingestion failures, processing failures, data quality alerts
- **Traceability**: Run ID propagation through pipeline

See [docs/OBSERVABILITY.md](docs/OBSERVABILITY.md) for monitoring design.

---

## 🤝 Contributing

This is a portfolio project for demonstration purposes. Not accepting external contributions.

---

## 📝 License

This project is for portfolio demonstration only. Not licensed for production use.

---

## 👤 Author

Developed as a portfolio project demonstrating cloud data engineering and analytics engineering capabilities.

---

## 📚 Documentation

Comprehensive documentation available in `docs/`:
- 2000+ lines of technical documentation
- 7 Architecture Decision Records
- Complete design specifications for all system components

Start with [docs/PROJECT.md](docs/PROJECT.md) for business context.

---

## ⚠️ Important Notes

- **No AWS resources deployed yet** (Phase 0 complete, implementation begins Phase 1+)
- **Fictional data** (retail scenario is illustrative)
- **Portfolio scope** (intentionally scoped for demonstration, not production scale)
- **Cost-optimized** (designed for < $10/month operation)

---

## 🎓 Skills Demonstrated

**Cloud Data Engineering**: Data lake design, serverless pipelines, AWS service integration  
**Analytics Engineering**: dbt, dimensional modeling, data quality testing  
**Infrastructure**: Terraform, IaC, reproducible deployments  
**DevOps**: CI/CD, GitHub Actions, automated testing  
**Cost Engineering**: Serverless optimization, free tier maximization  
**Architecture**: Trade-off analysis, ADRs, design documentation  
**Communication**: Technical writing, documentation, decision rationale

---

**Current Phase**: Documentation complete, ready for implementation approval.
