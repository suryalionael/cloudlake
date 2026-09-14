# CloudLake Project Contract

## Project Name

**CloudLake**

## Project Type

Cloud-native retail data platform

## Portfolio Purpose

CloudLake demonstrates professional capabilities in:

- **Cloud Data Engineering**: serverless ingestion, data lake architecture, AWS service integration
- **Data Platform Engineering**: multi-stage storage (raw/processed/analytics), schema management, data cataloging
- **Analytics Engineering**: dimensional modeling, dbt transformation layer, analytics marts
- **Infrastructure as Code**: Terraform-managed AWS resources, environment management, reproducible infrastructure
- **Data Quality Engineering**: multi-stage validation, automated testing, failure detection
- **Observability**: structured logging, metrics, alerting, pipeline monitoring
- **CI/CD for Data**: automated testing, deployment pipelines, quality gates

### Differentiation from Existing Portfolio

**FraudLens**: Risk/fraud detection, ML classification, decision intelligence  
**Toronto Mobility Intelligence**: Analytics, BI dashboards, spatial analysis, business storytelling  
**CloudLake**: Cloud data platform, data engineering, infrastructure, pipeline orchestration

CloudLake focuses on **how data moves, survives, transforms, validates, and becomes usable in the cloud**, not on end-user analytics or ML modeling.

## Business Problem

A fictional mid-size retail company operates:
- Multiple store locations
- E-commerce platform
- Product catalog
- Customer base

Current state:
- Operational data scattered across systems
- Manual reporting processes
- No historical analysis capability
- Limited data quality visibility
- No self-service analytics

Required capabilities:
- Centralized data storage
- Automated ingestion from multiple sources
- Historical data preservation
- Data quality validation
- Analytics-ready data models
- Self-service query capability

## Business Users

**Analytics Team**: daily/weekly performance reports, trend analysis  
**Business Intelligence Analysts**: dashboard creation, metric tracking  
**Operations Team**: inventory monitoring, order fulfillment tracking  
**Management**: strategic decision support, performance review  
**Data Scientists**: customer segmentation, predictive modeling (downstream)

## Core Questions

### Sales Performance
- What are daily/weekly/monthly sales by store?
- Which products generate the most revenue?
- What is average order value over time?

### Customer Behavior
- How many new vs returning customers per period?
- What is customer purchase frequency?
- What is customer lifetime value distribution?

### Product Performance
- Which products have highest volume?
- Which product categories perform best?
- What is inventory turnover?

### Store Performance
- Which stores exceed targets?
- How do stores compare by revenue/volume?
- What are store-level trends?

### Data Operations
- Did today's ingestion succeed?
- Are there data quality failures?
- When did each pipeline last run successfully?

## Business Scope Boundaries

CloudLake is **not**:
- A real-time streaming platform
- A transactional system
- A customer-facing application
- An enterprise data warehouse replacement
- A distributed compute platform

CloudLake **is**:
- A batch-oriented data platform
- A historical data repository
- An analytics enablement layer
- A data quality enforcement system
- A demonstration of cloud data engineering practices

## Success Criteria

The platform succeeds when:
1. Data flows reliably from sources to analytics layer
2. Raw data remains recoverable
3. Transformations are reproducible
4. Quality failures are detected and observable
5. Analysts can query data without engineering intervention
6. Infrastructure is version-controlled and reproducible
7. Pipeline failures are visible within minutes
8. Monthly AWS cost remains under $20
9. Documentation enables knowledge transfer
10. Architecture decisions are defensible in technical interviews
