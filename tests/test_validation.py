"""
Unit tests for data validation module.
"""

import pytest
from datetime import datetime
from src.validation.validator import DataValidator, ValidationError


class TestCustomerValidation:
    """Test customer record validation."""

    def test_valid_customer(self):
        """Test validation of valid customer record."""
        customer = {
            "customer_id": "C000001",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "city": "New York",
            "state": "NY",
            "country": "US",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
        }
        is_valid, reason = DataValidator.validate_customer(customer)
        assert is_valid is True
        assert reason is None

    def test_missing_required_field(self):
        """Test validation fails when required field missing."""
        customer = {
            "customer_id": "C000001",
            "first_name": "John",
            "last_name": "Doe",
            "country": "US",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
        }
        is_valid, reason = DataValidator.validate_customer(customer)
        assert is_valid is False
        assert "email" in reason.lower()

    def test_invalid_email_format(self):
        """Test validation fails for invalid email."""
        customer = {
            "customer_id": "C000001",
            "email": "not-an-email",
            "first_name": "John",
            "last_name": "Doe",
            "city": "New York",
            "state": "NY",
            "country": "US",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
        }
        is_valid, reason = DataValidator.validate_customer(customer)
        assert is_valid is False
        assert "email" in reason.lower()

    def test_invalid_country_code(self):
        """Test validation fails for invalid country."""
        customer = {
            "customer_id": "C000001",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "city": "New York",
            "state": "NY",
            "country": "XX",
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
        }
        is_valid, reason = DataValidator.validate_customer(customer)
        assert is_valid is False
        assert "country" in reason.lower()

    def test_created_after_updated(self):
        """Test validation fails when created_at > updated_at."""
        customer = {
            "customer_id": "C000001",
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
            "city": "New York",
            "state": "NY",
            "country": "US",
            "created_at": "2024-01-02T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
        }
        is_valid, reason = DataValidator.validate_customer(customer)
        assert is_valid is False
        assert "created_at" in reason.lower() or "updated_at" in reason.lower()


class TestProductValidation:
    """Test product record validation."""

    def test_valid_product(self):
        """Test validation of valid product record."""
        product = {
            "product_id": "P00001",
            "name": "Test Product",
            "category": "Electronics",
            "subcategory": "Laptop",
            "price": 999.99,
            "cost": 500.00,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
        }
        is_valid, reason = DataValidator.validate_product(product)
        assert is_valid is True
        assert reason is None

    def test_negative_price(self):
        """Test validation fails for negative price."""
        product = {
            "product_id": "P00001",
            "name": "Test Product",
            "category": "Electronics",
            "price": -10.00,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
        }
        is_valid, reason = DataValidator.validate_product(product)
        assert is_valid is False
        assert "price" in reason.lower()

    def test_zero_price(self):
        """Test validation fails for zero price."""
        product = {
            "product_id": "P00001",
            "name": "Test Product",
            "category": "Electronics",
            "price": 0,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-02T00:00:00",
        }
        is_valid, reason = DataValidator.validate_product(product)
        assert is_valid is False
        assert "price" in reason.lower()


class TestOrderValidation:
    """Test order record validation."""

    def test_valid_order(self):
        """Test validation of valid order record."""
        order = {
            "order_id": "O00000001",
            "customer_id": "C000001",
            "store_id": "S001",
            "order_date": "2024-01-15T12:30:00",
            "status": "complete",
            "total_amount": 150.00,
        }
        is_valid, reason = DataValidator.validate_order(order)
        assert is_valid is True
        assert reason is None

    def test_invalid_status(self):
        """Test validation fails for invalid status."""
        order = {
            "order_id": "O00000001",
            "customer_id": "C000001",
            "store_id": "S001",
            "order_date": "2024-01-15T12:30:00",
            "status": "invalid_status",
            "total_amount": 150.00,
        }
        is_valid, reason = DataValidator.validate_order(order)
        assert is_valid is False
        assert "status" in reason.lower()

    def test_negative_total_amount(self):
        """Test validation fails for negative total."""
        order = {
            "order_id": "O00000001",
            "customer_id": "C000001",
            "store_id": "S001",
            "order_date": "2024-01-15T12:30:00",
            "status": "complete",
            "total_amount": -50.00,
        }
        is_valid, reason = DataValidator.validate_order(order)
        assert is_valid is False
        assert "total_amount" in reason.lower()


class TestOrderItemValidation:
    """Test order item record validation."""

    def test_valid_order_item(self):
        """Test validation of valid order item record."""
        order_item = {
            "order_item_id": "OI0000000001",
            "order_id": "O00000001",
            "product_id": "P00001",
            "quantity": 2,
            "unit_price": 50.00,
            "line_total": 100.00,
        }
        is_valid, reason = DataValidator.validate_order_item(order_item)
        assert is_valid is True
        assert reason is None

    def test_zero_quantity(self):
        """Test validation fails for zero quantity."""
        order_item = {
            "order_item_id": "OI0000000001",
            "order_id": "O00000001",
            "product_id": "P00001",
            "quantity": 0,
            "unit_price": 50.00,
            "line_total": 0.00,
        }
        is_valid, reason = DataValidator.validate_order_item(order_item)
        assert is_valid is False
        assert "quantity" in reason.lower()

    def test_line_total_mismatch(self):
        """Test validation fails when line_total doesn't match calculation."""
        order_item = {
            "order_item_id": "OI0000000001",
            "order_id": "O00000001",
            "product_id": "P00001",
            "quantity": 2,
            "unit_price": 50.00,
            "line_total": 90.00,  # Should be 100.00
        }
        is_valid, reason = DataValidator.validate_order_item(order_item)
        assert is_valid is False
        assert "line_total" in reason.lower()


class TestBatchValidation:
    """Test batch validation functionality."""

    def test_batch_validation_customers(self):
        """Test batch validation with mixed valid/invalid records."""
        records = [
            {
                "customer_id": "C000001",
                "email": "valid@example.com",
                "first_name": "John",
                "last_name": "Doe",
                "country": "US",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-02T00:00:00",
            },
            {
                "customer_id": "C000002",
                "email": "invalid-email",
                "first_name": "Jane",
                "last_name": "Smith",
                "country": "US",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-02T00:00:00",
            },
            {
                "customer_id": "C000003",
                "email": "valid2@example.com",
                "first_name": "Bob",
                "last_name": "Johnson",
                "country": "CA",
                "created_at": "2024-01-01T00:00:00",
                "updated_at": "2024-01-02T00:00:00",
            },
        ]
        
        valid, rejected, reasons = DataValidator.validate_batch("customers", records)
        
        assert len(valid) == 2
        assert len(rejected) == 1
        assert len(reasons) == 1
        assert "email" in reasons[0].lower()

    def test_batch_validation_unknown_entity(self):
        """Test batch validation fails for unknown entity."""
        with pytest.raises(ValueError, match="Unknown entity"):
            DataValidator.validate_batch("unknown_entity", [])
