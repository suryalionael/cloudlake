# Data Contracts

## Retail Domain Model

### Entity Overview

| Entity       | Purpose                           | Source      | Update Frequency | Grain           |
|--------------|-----------------------------------|-------------|------------------|-----------------|
| customers    | Customer master data              | REST API    | Daily            | One per customer|
| products     | Product catalog                   | REST API    | Daily            | One per product |
| stores       | Store location master             | CSV         | Weekly           | One per store   |
| orders       | Order header                      | REST API    | Hourly           | One per order   |
| order_items  | Line items within orders          | REST API    | Hourly           | One per line    |

### Justification

**customers**: Required for customer-level analytics, segmentation, lifetime value  
**products**: Required for product performance analysis, category reporting  
**stores**: Required for geographic analysis, store performance comparison  
**orders**: Core transaction fact, revenue aggregation  
**order_items**: Detailed product-level sales, inventory analysis

**Not included**:
- **payments**: Payment method does not add meaningful analytical value for portfolio scope
- **inventory**: Real-time inventory tracking adds complexity without demonstrating new capabilities
- **returns**: Secondary process, would duplicate order logic

## customers

**Purpose**: Customer master dimension

### Schema

| Field          | Type      | Nullable | Description                    | Constraints           |
|----------------|-----------|----------|--------------------------------|-----------------------|
| customer_id    | STRING    | NO       | Unique customer identifier     | Primary key           |
| email          | STRING    | NO       | Customer email                 | Unique                |
| first_name     | STRING    | NO       | First name                     |                       |
| last_name      | STRING    | NO       | Last name                      |                       |
| city           | STRING    | YES      | City                           |                       |
| state          | STRING    | YES      | State/province code            | 2 chars               |
| country        | STRING    | NO       | Country code                   | ISO 3166-1 alpha-2    |
| created_at     | TIMESTAMP | NO       | Account creation timestamp     |                       |
| updated_at     | TIMESTAMP | NO       | Last update timestamp          |                       |

### Quality Rules

- `customer_id` must be unique
- `email` must be valid format
- `created_at` <= `updated_at`
- `created_at` <= current timestamp
- `country` must be valid ISO code

### Expected Volume

~50K customers initial, +500/day growth

## products

**Purpose**: Product catalog dimension

### Schema

| Field          | Type      | Nullable | Description                    | Constraints           |
|----------------|-----------|----------|--------------------------------|-----------------------|
| product_id     | STRING    | NO       | Unique product identifier      | Primary key           |
| name           | STRING    | NO       | Product name                   |                       |
| category       | STRING    | NO       | Product category               |                       |
| subcategory    | STRING    | YES      | Product subcategory            |                       |
| price          | DECIMAL   | NO       | Current price                  | > 0                   |
| cost           | DECIMAL   | YES      | Product cost                   | >= 0                  |
| created_at     | TIMESTAMP | NO       | Product creation timestamp     |                       |
| updated_at     | TIMESTAMP | NO       | Last update timestamp          |                       |

### Quality Rules

- `product_id` must be unique
- `price` > 0
- `cost` <= `price` (warning if violated, not error)
- `created_at` <= `updated_at`
- `category` must be from known set

### Expected Volume

~5K products, +50/month growth

## stores

**Purpose**: Store location dimension

### Schema

| Field          | Type      | Nullable | Description                    | Constraints           |
|----------------|-----------|----------|--------------------------------|-----------------------|
| store_id       | STRING    | NO       | Unique store identifier        | Primary key           |
| store_name     | STRING    | NO       | Store name                     |                       |
| city           | STRING    | NO       | City                           |                       |
| state          | STRING    | NO       | State/province code            | 2 chars               |
| country        | STRING    | NO       | Country code                   | ISO 3166-1 alpha-2    |
| opened_at      | DATE      | NO       | Store opening date             |                       |
| closed_at      | DATE      | YES      | Store closing date (if closed) |                       |

### Quality Rules

- `store_id` must be unique
- `opened_at` <= current date
- `closed_at` >= `opened_at` (if not null)
- `country` must be valid ISO code

### Expected Volume

~20 stores, +1-2/year growth

## orders

**Purpose**: Order transaction fact

### Schema

| Field          | Type      | Nullable | Description                    | Constraints           |
|----------------|-----------|----------|--------------------------------|-----------------------|
| order_id       | STRING    | NO       | Unique order identifier        | Primary key           |
| customer_id    | STRING    | NO       | Customer identifier            | FK to customers       |
| store_id       | STRING    | YES      | Store identifier (null=online) | FK to stores          |
| order_date     | TIMESTAMP | NO       | Order timestamp                |                       |
| status         | STRING    | NO       | Order status                   | Enum: pending/complete/cancelled |
| total_amount   | DECIMAL   | NO       | Order total                    | >= 0                  |

### Quality Rules

- `order_id` must be unique
- `customer_id` must exist in customers
- `store_id` must exist in stores (if not null)
- `order_date` <= current timestamp
- `total_amount` >= 0
- `status` must be valid enum value

### Expected Volume

~10K orders/day

## order_items

**Purpose**: Order line item detail

### Schema

| Field          | Type      | Nullable | Description                    | Constraints           |
|----------------|-----------|----------|--------------------------------|-----------------------|
| order_item_id  | STRING    | NO       | Unique line item identifier    | Primary key           |
| order_id       | STRING    | NO       | Order identifier               | FK to orders          |
| product_id     | STRING    | NO       | Product identifier             | FK to products        |
| quantity       | INTEGER   | NO       | Quantity purchased             | > 0                   |
| unit_price     | DECIMAL   | NO       | Price per unit                 | > 0                   |
| line_total     | DECIMAL   | NO       | Line total                     | >= 0                  |

### Quality Rules

- `order_item_id` must be unique
- `order_id` must exist in orders
- `product_id` must exist in products
- `quantity` > 0
- `unit_price` > 0
- `line_total` = `quantity` * `unit_price` (within rounding tolerance)

### Expected Volume

~30K line items/day (avg 3 items per order)

## Data Lineage

```
Source System
     ↓
Raw Layer (JSON/CSV)
     ↓
Processed Layer (Parquet)
     ↓
Glue Catalog
     ↓
Staging Models (dbt)
     ↓
Dimension/Fact Models (dbt)
     ↓
Analytics Marts (dbt)
```

## Schema Evolution

**Additive changes** (new nullable columns): backward compatible, no migration required  
**Breaking changes** (rename, delete, type change): require version increment, migration plan

Version strategy: timestamp-based snapshots in raw layer preserve all source schemas
