"""
AWS Glue ETL Job: Process raw JSON data to typed Parquet.

Reads from S3 raw layer, validates, transforms, and writes to S3 processed layer.
"""

import sys
import os
import json
import logging
from datetime import datetime

from awsglue.utils import getResolvedOptions
from pyspark.context import SparkContext
from pyspark.sql import functions as F
from pyspark.sql.types import (
    StructType, StructField, StringType, DecimalType,
    IntegerType, TimestampType, DateType
)
from awsglue.context import GlueContext
from awsglue.job import Job

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Entity schemas
SCHEMAS = {
    "customers": StructType([
        StructField("customer_id", StringType(), False),
        StructField("email", StringType(), False),
        StructField("first_name", StringType(), False),
        StructField("last_name", StringType(), False),
        StructField("city", StringType(), True),
        StructField("state", StringType(), True),
        StructField("country", StringType(), False),
        StructField("created_at", StringType(), False),
        StructField("updated_at", StringType(), False),
    ]),
    "products": StructType([
        StructField("product_id", StringType(), False),
        StructField("name", StringType(), False),
        StructField("category", StringType(), False),
        StructField("subcategory", StringType(), True),
        StructField("price", DecimalType(10, 2), False),
        StructField("cost", DecimalType(10, 2), True),
        StructField("created_at", StringType(), False),
        StructField("updated_at", StringType(), False),
    ]),
    "stores": StructType([
        StructField("store_id", StringType(), False),
        StructField("store_name", StringType(), False),
        StructField("city", StringType(), False),
        StructField("state", StringType(), False),
        StructField("country", StringType(), False),
        StructField("opened_at", StringType(), False),
        StructField("closed_at", StringType(), True),
    ]),
    "orders": StructType([
        StructField("order_id", StringType(), False),
        StructField("customer_id", StringType(), False),
        StructField("store_id", StringType(), True),
        StructField("order_date", StringType(), False),
        StructField("status", StringType(), False),
        StructField("total_amount", DecimalType(12, 2), False),
    ]),
    "order_items": StructType([
        StructField("order_item_id", StringType(), False),
        StructField("order_id", StringType(), False),
        StructField("product_id", StringType(), False),
        StructField("quantity", IntegerType(), False),
        StructField("unit_price", DecimalType(10, 2), False),
        StructField("line_total", DecimalType(12, 2), False),
    ]),
}


def validate_entity(spark, df, entity):
    """Validate DataFrame against expected schema."""
    logger.info(f"Validating {entity}: {df.count()} records")

    # Check required fields exist
    required_fields = [f.name for f in SCHEMAS[entity].fields if not f.nullable]
    for field in required_fields:
        if field not in df.columns:
            raise ValueError(f"Missing required field: {field}")

    # Check for null values in required fields
    for field in required_fields:
        null_count = df.filter(F.col(field).isNull()).count()
        if null_count > 0:
            logger.warning(f"Found {null_count} null values in required field: {field}")
            df = df.filter(F.col(field).isNotNull())

    # Remove exact duplicates
    before_count = df.count()
    df = df.dropDuplicates()
    after_count = df.count()
    if before_count != after_count:
        logger.warning(f"Removed {before_count - after_count} duplicate records")

    logger.info(f"Validation passed for {entity}: {after_count} valid records")
    return df


def type_cast(df, entity):
    """Cast columns to appropriate types."""
    cast_map = {
        "customers": {
            "created_at": "timestamp",
            "updated_at": "timestamp",
        },
        "products": {
            "price": "decimal(10,2)",
            "cost": "decimal(10,2)",
            "created_at": "timestamp",
            "updated_at": "timestamp",
        },
        "stores": {
            "opened_at": "date",
            "closed_at": "date",
        },
        "orders": {
            "order_date": "timestamp",
            "total_amount": "decimal(12,2)",
        },
        "order_items": {
            "quantity": "int",
            "unit_price": "decimal(10,2)",
            "line_total": "decimal(12,2)",
        },
    }

    for col_name, dtype in cast_map.get(entity, {}).items():
        df = df.withColumn(col_name, F.col(col_name).cast(dtype))

    return df


def validate_business_rules(df, entity):
    """Apply business rule validation."""
    rejected = df

    if entity == "products":
        # Price must be > 0
        rejected = df.filter(F.col("price") <= 0)
        df = df.filter(F.col("price") > 0)

    elif entity == "orders":
        # total_amount must be >= 0
        rejected = df.filter(F.col("total_amount") < 0)
        df = df.filter(F.col("total_amount") >= 0)

    elif entity == "order_items":
        # quantity must be > 0, line_total >= 0
        rejected = df.filter(
            (F.col("quantity") <= 0) | (F.col("line_total") < 0)
        )
        df = df.filter(
            (F.col("quantity") > 0) & (F.col("line_total") >= 0)
        )

    if rejected.count() > 0:
        logger.warning(f"Rejected {rejected.count()} records by business rules for {entity}")

    return df


def process_entity(spark, glueContext, entity, date_str):
    """Process a single entity: read, validate, transform, write."""
    logger.info(f"Processing {entity} for date={date_str}")

    year, month, day = date_str.split("-")
    source_bucket = os.environ.get("SOURCE_BUCKET", os.environ.get("S3_BUCKET", "cloudlake-data"))
    target_bucket = os.environ.get("TARGET_BUCKET", source_bucket)

    input_path = f"s3://{source_bucket}/raw/{entity}/year={year}/month={month}/day={day}/"
    output_path = f"s3://{target_bucket}/processed/{entity}/year={year}/month={month}/day={day}/"
    rejected_path = f"s3://{target_bucket}/rejected/{entity}/year={year}/month={month}/day={day}/"

    # Read raw JSON
    try:
        raw_df = spark.read.json(input_path)
    except Exception as e:
        logger.error(f"Failed to read {entity} from {input_path}: {e}")
        return 0

    input_count = raw_df.count()
    if input_count == 0:
        logger.warning(f"No records found for {entity} at {input_path}")
        return 0

    logger.info(f"Read {input_count} raw records")

    # Validate
    validated_df = validate_entity(spark, raw_df, entity)

    # Type cast
    typed_df = type_cast(validated_df, entity)

    # Business rules
    clean_df = validate_business_rules(typed_df, entity)

    # Write to processed layer
    clean_df.write.mode("overwrite").parquet(output_path)
    output_count = clean_df.count()

    logger.info(f"Wrote {output_count} records to {output_path}")

    return output_count


def main(spark, glueContext, entity, date_str):
    """Main processing entry point."""
    job = Job(glueContext)
    job.init(os.environ.get("JOB_NAME", "cloudlake-processing"))

    try:
        count = process_entity(spark, glueContext, entity, date_str)

        logger.info(json.dumps({
            "event": "processing_complete",
            "entity": entity,
            "date": date_str,
            "records_processed": count,
            "timestamp": datetime.utcnow().isoformat()
        }))

        job.commit()

    except Exception as e:
        logger.error(json.dumps({
            "event": "processing_failed",
            "entity": entity,
            "date": date_str,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }))
        raise


# Entry point for standalone execution
if __name__ == "__main__":
    args = getResolvedOptions(sys.argv, ['JOB_NAME', 'entity', 'date'])
    sc = SparkContext()
    glueContext = GlueContext(sc)
    spark = glueContext.spark_session

    main(spark, glueContext, args['entity'], args['date'])
