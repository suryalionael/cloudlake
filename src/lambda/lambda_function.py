"""
Lambda function for data ingestion.

Fetches data from source (generated locally or API) and writes to S3 raw layer.
"""

import json
import os
import boto3
from datetime import datetime
import uuid
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
cloudwatch = boto3.client('cloudwatch')


def lambda_handler(event, context):
    """
    Lambda handler for data ingestion.
    
    Environment variables:
    - ENTITY: Entity name (customers, products, stores, orders)
    - S3_BUCKET: Target S3 bucket
    - S3_PREFIX: S3 prefix (e.g., raw/customers)
    - PARAMETER_PREFIX: SSM parameter prefix for API credentials (optional)
    """
    
    run_id = context.request_id
    entity = os.environ['ENTITY']
    s3_bucket = os.environ['S3_BUCKET']
    s3_prefix = os.environ['S3_PREFIX']
    
    logger.info(json.dumps({
        'event': 'ingestion_start',
        'run_id': run_id,
        'entity': entity,
        'timestamp': datetime.utcnow().isoformat()
    }))
    
    try:
        # For Phase 3, use generated data from local_data
        # In production, this would fetch from actual API
        data = generate_sample_data(entity)
        
        if not data:
            raise ValueError(f"No data generated for {entity}")
        
        record_count = len(data)
        
        logger.info(json.dumps({
            'event': 'data_fetched',
            'run_id': run_id,
            'entity': entity,
            'record_count': record_count
        }))
        
        # Validate data (basic check)
        valid_records, rejected_count = validate_records(entity, data)
        
        if rejected_count > 0:
            logger.warning(json.dumps({
                'event': 'validation_warning',
                'run_id': run_id,
                'entity': entity,
                'rejected_count': rejected_count,
                'rejection_rate': rejected_count / record_count
            }))
        
        # Write to S3
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        s3_key = f"{s3_prefix}/year={datetime.utcnow().year}/month={datetime.utcnow().month:02d}/day={datetime.utcnow().day:02d}/{timestamp}_{run_id}.json"
        
        s3_client.put_object(
            Bucket=s3_bucket,
            Key=s3_key,
            Body=json.dumps(valid_records, indent=2),
            ContentType='application/json',
            Metadata={
                'run_id': run_id,
                'entity': entity,
                'record_count': str(len(valid_records)),
                'ingestion_timestamp': timestamp
            }
        )
        
        logger.info(json.dumps({
            'event': 'ingestion_complete',
            'run_id': run_id,
            'entity': entity,
            's3_bucket': s3_bucket,
            's3_key': s3_key,
            'records_written': len(valid_records)
        }))
        
        # Publish custom metric
        try:
            cloudwatch.put_metric_data(
                Namespace='CloudLake/Ingestion',
                MetricData=[
                    {
                        'MetricName': 'RecordsIngested',
                        'Value': len(valid_records),
                        'Unit': 'Count',
                        'Timestamp': datetime.utcnow(),
                        'Dimensions': [
                            {'Name': 'Entity', 'Value': entity}
                        ]
                    },
                    {
                        'MetricName': 'RejectionRate',
                        'Value': (rejected_count / record_count * 100) if record_count > 0 else 0,
                        'Unit': 'Percent',
                        'Dimensions': [
                            {'Name': 'Entity', 'Value': entity}
                        ]
                    }
                ]
            )
        except Exception as e:
            logger.warning(f"Failed to publish metrics: {e}")
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'status': 'success',
                'entity': entity,
                'records': len(valid_records),
                's3_key': s3_key,
                'run_id': run_id
            })
        }
        
    except Exception as e:
        logger.error(json.dumps({
            'event': 'ingestion_failed',
            'run_id': run_id,
            'entity': entity,
            'error': str(e),
            'error_type': type(e).__name__
        }))
        
        return {
            'statusCode': 500,
            'body': json.dumps({
                'status': 'error',
                'entity': entity,
                'error': str(e),
                'run_id': run_id
            })
        }


def generate_sample_data(entity):
    """
    Generate sample data for testing.
    
    In production, this would be replaced with actual API calls.
    """
    from faker import Faker
    import random
    
    fake = Faker()
    Faker.seed(42 + hash(entity) % 1000)
    random.seed(42 + hash(entity) % 1000)
    
    if entity == 'customers':
        return [
            {
                "customer_id": f"C{i+1:06d}",
                "email": fake.email(),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "country": random.choice(["US", "CA", "UK", "AU"]),
                "created_at": fake.date_time_between(start_date="-2y", end_date="-30d").isoformat(),
                "updated_at": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
            }
            for i in range(50)  # Smaller batch for Lambda testing
        ]
    
    elif entity == 'products':
        categories = {
            "Electronics": ["Laptop", "Phone", "Tablet"],
            "Apparel": ["Shirt", "Pants", "Jacket"],
            "Home": ["Chair", "Desk", "Lamp"],
        }
        return [
            {
                "product_id": f"P{i+1:05d}",
                "name": f"{fake.word().capitalize()} {random.choice(list(categories.values())[0])}",
                "category": random.choice(list(categories.keys())),
                "subcategory": random.choice(list(categories.values())[0]),
                "price": round(random.uniform(10, 200), 2),
                "cost": round(random.uniform(5, 100), 2),
                "created_at": fake.date_time_between(start_date="-1y", end_date="now").isoformat(),
                "updated_at": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
            }
            for i in range(20)
        ]
    
    elif entity == 'stores':
        return [
            {
                "store_id": f"S{i+1:03d}",
                "store_name": f"{fake.city()} Store",
                "city": fake.city(),
                "state": fake.state_abbr(),
                "country": random.choice(["US", "CA"]),
                "opened_at": fake.date_between(start_date="-5y", end_date="-1y").isoformat(),
                "closed_at": None,
            }
            for i in range(5)
        ]
    
    elif entity == 'orders':
        return [
            {
                "order_id": f"O{i+1:08d}",
                "customer_id": f"C{random.randint(1, 50):06d}",
                "store_id": f"S{random.randint(1, 5):03d}" if random.random() > 0.2 else None,
                "order_date": fake.date_time_between(start_date="-30d", end_date="now").isoformat(),
                "status": random.choices(["complete", "pending", "cancelled"], weights=[0.85, 0.10, 0.05])[0],
                "total_amount": round(random.uniform(10, 500), 2),
            }
            for i in range(30)
        ]
    
    else:
        return []


def validate_records(entity, records):
    """
    Basic validation of records.
    
    Returns (valid_records, rejected_count).
    """
    valid = []
    rejected = 0
    
    for record in records:
        # Basic validation - check required fields exist
        required_fields = get_required_fields(entity)
        
        is_valid = all(field in record and record[field] is not None for field in required_fields)
        
        if is_valid:
            valid.append(record)
        else:
            rejected += 1
    
    return valid, rejected


def get_required_fields(entity):
    """Return required fields for each entity."""
    fields_map = {
        'customers': ['customer_id', 'email', 'first_name', 'last_name', 'country', 'created_at', 'updated_at'],
        'products': ['product_id', 'name', 'category', 'price', 'created_at', 'updated_at'],
        'stores': ['store_id', 'store_name', 'city', 'state', 'country', 'opened_at'],
        'orders': ['order_id', 'customer_id', 'order_date', 'status', 'total_amount'],
    }
    return fields_map.get(entity, [])
