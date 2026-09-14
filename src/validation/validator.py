"""
Validation module for CloudLake data.

Validates data at ingestion stage (schema, required fields, formats).
"""

import re
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class ValidationError(Exception):
    """Custom exception for validation failures."""
    pass


class DataValidator:
    """Validate retail data records."""

    EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    ISO_COUNTRIES = ["US", "CA", "UK", "AU", "FR", "DE", "JP"]

    @staticmethod
    def validate_customer(record: Dict) -> Tuple[bool, Optional[str]]:
        """Validate customer record."""
        required_fields = ["customer_id", "email", "first_name", "last_name", "country", "created_at", "updated_at"]
        
        # Check required fields
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
            if record[field] is None or record[field] == "":
                return False, f"Field cannot be null or empty: {field}"
        
        # Validate email format
        if not DataValidator.EMAIL_REGEX.match(record["email"]):
            return False, f"Invalid email format: {record['email']}"
        
        # Validate country code
        if record["country"] not in DataValidator.ISO_COUNTRIES:
            return False, f"Invalid country code: {record['country']}"
        
        # Validate timestamps
        try:
            created_at = datetime.fromisoformat(record["created_at"].replace('Z', '+00:00'))
            updated_at = datetime.fromisoformat(record["updated_at"].replace('Z', '+00:00'))
            
            if created_at > datetime.now():
                return False, "created_at cannot be in future"
            if updated_at > datetime.now():
                return False, "updated_at cannot be in future"
            if created_at > updated_at:
                return False, "created_at cannot be after updated_at"
        except (ValueError, AttributeError) as e:
            return False, f"Invalid timestamp format: {e}"
        
        return True, None

    @staticmethod
    def validate_product(record: Dict) -> Tuple[bool, Optional[str]]:
        """Validate product record."""
        required_fields = ["product_id", "name", "category", "price", "created_at", "updated_at"]
        
        # Check required fields
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
            if record[field] is None or record[field] == "":
                return False, f"Field cannot be null or empty: {field}"
        
        # Validate price
        try:
            price = float(record["price"])
            if price <= 0:
                return False, "price must be greater than 0"
        except (ValueError, TypeError):
            return False, f"Invalid price: {record['price']}"
        
        # Validate cost if present
        if "cost" in record and record["cost"] is not None:
            try:
                cost = float(record["cost"])
                if cost < 0:
                    return False, "cost cannot be negative"
            except (ValueError, TypeError):
                return False, f"Invalid cost: {record['cost']}"
        
        # Validate timestamps
        try:
            created_at = datetime.fromisoformat(record["created_at"].replace('Z', '+00:00'))
            updated_at = datetime.fromisoformat(record["updated_at"].replace('Z', '+00:00'))
            
            if created_at > updated_at:
                return False, "created_at cannot be after updated_at"
        except (ValueError, AttributeError) as e:
            return False, f"Invalid timestamp format: {e}"
        
        return True, None

    @staticmethod
    def validate_store(record: Dict) -> Tuple[bool, Optional[str]]:
        """Validate store record."""
        required_fields = ["store_id", "store_name", "city", "state", "country", "opened_at"]
        
        # Check required fields
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
            if record[field] is None or record[field] == "":
                return False, f"Field cannot be null or empty: {field}"
        
        # Validate country
        if record["country"] not in DataValidator.ISO_COUNTRIES:
            return False, f"Invalid country code: {record['country']}"
        
        # Validate dates
        try:
            opened_at = datetime.fromisoformat(record["opened_at"].replace('Z', '+00:00'))
            
            if "closed_at" in record and record["closed_at"] is not None:
                closed_at = datetime.fromisoformat(record["closed_at"].replace('Z', '+00:00'))
                if closed_at < opened_at:
                    return False, "closed_at cannot be before opened_at"
        except (ValueError, AttributeError) as e:
            return False, f"Invalid date format: {e}"
        
        return True, None

    @staticmethod
    def validate_order(record: Dict) -> Tuple[bool, Optional[str]]:
        """Validate order record."""
        required_fields = ["order_id", "customer_id", "order_date", "status", "total_amount"]
        
        # Check required fields
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
            if record[field] is None or (isinstance(record[field], str) and record[field] == ""):
                return False, f"Field cannot be null or empty: {field}"
        
        # Validate status
        valid_statuses = ["pending", "complete", "cancelled"]
        if record["status"] not in valid_statuses:
            return False, f"Invalid status: {record['status']} (must be one of {valid_statuses})"
        
        # Validate total_amount
        try:
            total_amount = float(record["total_amount"])
            if total_amount < 0:
                return False, "total_amount cannot be negative"
        except (ValueError, TypeError):
            return False, f"Invalid total_amount: {record['total_amount']}"
        
        # Validate order_date
        try:
            order_date = datetime.fromisoformat(record["order_date"].replace('Z', '+00:00'))
            if order_date > datetime.now():
                return False, "order_date cannot be in future"
        except (ValueError, AttributeError) as e:
            return False, f"Invalid order_date format: {e}"
        
        return True, None

    @staticmethod
    def validate_order_item(record: Dict) -> Tuple[bool, Optional[str]]:
        """Validate order item record."""
        required_fields = ["order_item_id", "order_id", "product_id", "quantity", "unit_price", "line_total"]
        
        # Check required fields
        for field in required_fields:
            if field not in record:
                return False, f"Missing required field: {field}"
            if record[field] is None or record[field] == "":
                return False, f"Field cannot be null or empty: {field}"
        
        # Validate quantity
        try:
            quantity = int(record["quantity"])
            if quantity <= 0:
                return False, "quantity must be greater than 0"
        except (ValueError, TypeError):
            return False, f"Invalid quantity: {record['quantity']}"
        
        # Validate unit_price
        try:
            unit_price = float(record["unit_price"])
            if unit_price <= 0:
                return False, "unit_price must be greater than 0"
        except (ValueError, TypeError):
            return False, f"Invalid unit_price: {record['unit_price']}"
        
        # Validate line_total
        try:
            line_total = float(record["line_total"])
            if line_total < 0:
                return False, "line_total cannot be negative"
            
            # Check calculation (within rounding tolerance)
            expected_total = quantity * unit_price
            if abs(line_total - expected_total) > 0.02:
                return False, f"line_total mismatch: expected {expected_total}, got {line_total}"
        except (ValueError, TypeError):
            return False, f"Invalid line_total: {record['line_total']}"
        
        return True, None

    @staticmethod
    def validate_batch(entity: str, records: List[Dict]) -> Tuple[List[Dict], List[Dict], List[str]]:
        """
        Validate a batch of records.
        
        Returns:
            (valid_records, rejected_records, rejection_reasons)
        """
        validators = {
            "customers": DataValidator.validate_customer,
            "products": DataValidator.validate_product,
            "stores": DataValidator.validate_store,
            "orders": DataValidator.validate_order,
            "order_items": DataValidator.validate_order_item,
        }
        
        if entity not in validators:
            raise ValueError(f"Unknown entity: {entity}")
        
        validator = validators[entity]
        
        valid_records = []
        rejected_records = []
        rejection_reasons = []
        
        for record in records:
            is_valid, reason = validator(record)
            if is_valid:
                valid_records.append(record)
            else:
                rejected_records.append(record)
                rejection_reasons.append(reason)
        
        return valid_records, rejected_records, rejection_reasons


if __name__ == "__main__":
    # Test validation
    test_customer = {
        "customer_id": "C000001",
        "email": "test@example.com",
        "first_name": "John",
        "last_name": "Doe",
        "city": "New York",
        "state": "NY",
        "country": "US",
        "created_at": "2024-01-01T00:00:00",
        "updated_at": "2024-01-02T00:00:00",
    }
    
    is_valid, reason = DataValidator.validate_customer(test_customer)
    print(f"Customer validation: {is_valid} - {reason}")
