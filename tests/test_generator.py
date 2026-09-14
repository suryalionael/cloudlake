"""
Unit tests for data generation module.
"""

import json
import pytest
from pathlib import Path
from src.data_generation.generator import DataGenerator


class TestDataGenerator:
    """Test data generation functionality."""

    def test_generate_customers(self):
        """Test customer generation."""
        generator = DataGenerator()
        customers = generator.generate_customers(n=10)
        
        assert len(customers) == 10
        assert all("customer_id" in c for c in customers)
        assert all("email" in c for c in customers)
        assert all("first_name" in c for c in customers)
        assert all("created_at" in c for c in customers)

    def test_generate_products(self):
        """Test product generation."""
        generator = DataGenerator()
        products = generator.generate_products(n=10)
        
        assert len(products) == 10
        assert all("product_id" in p for p in products)
        assert all("name" in p for p in products)
        assert all("category" in p for p in products)
        assert all("price" in p for p in products)
        assert all(p["price"] > 0 for p in products)

    def test_generate_stores(self):
        """Test store generation."""
        generator = DataGenerator()
        stores = generator.generate_stores(n=5)
        
        assert len(stores) == 5
        assert all("store_id" in s for s in stores)
        assert all("store_name" in s for s in stores)
        assert all("opened_at" in s for s in stores)

    def test_generate_orders(self):
        """Test order generation."""
        generator = DataGenerator()
        generator.generate_customers(n=10)
        generator.generate_stores(n=5)
        orders = generator.generate_orders(n=20)
        
        assert len(orders) == 20
        assert all("order_id" in o for o in orders)
        assert all("customer_id" in o for o in orders)
        assert all("order_date" in o for o in orders)
        assert all("status" in o for o in orders)

    def test_generate_order_items(self):
        """Test order item generation."""
        generator = DataGenerator()
        generator.generate_customers(n=10)
        generator.generate_stores(n=5)
        generator.generate_products(n=10)
        generator.generate_orders(n=10)
        order_items = generator.generate_order_items(items_per_order=3)
        
        assert len(order_items) > 0
        assert all("order_item_id" in oi for oi in order_items)
        assert all("order_id" in oi for oi in order_items)
        assert all("product_id" in oi for oi in order_items)
        assert all("quantity" in oi for oi in order_items)
        assert all("unit_price" in oi for oi in order_items)
        assert all("line_total" in oi for oi in order_items)

    def test_order_totals_calculated(self):
        """Test that order totals are calculated from order items."""
        generator = DataGenerator()
        generator.generate_customers(n=5)
        generator.generate_stores(n=2)
        generator.generate_products(n=5)
        generator.generate_orders(n=5)
        generator.generate_order_items(items_per_order=2)
        
        # Verify order totals are non-zero
        assert all(o["total_amount"] > 0 for o in generator.orders)

    def test_customer_id_format(self):
        """Test customer ID format is consistent."""
        generator = DataGenerator()
        customers = generator.generate_customers(n=100)
        
        assert customers[0]["customer_id"] == "C000001"
        assert customers[99]["customer_id"] == "C000100"

    def test_product_price_greater_than_cost(self):
        """Test that product price is generally greater than cost."""
        generator = DataGenerator()
        products = generator.generate_products(n=50)
        
        products_with_cost = [p for p in products if "cost" in p and p["cost"] is not None]
        # Most products should have price > cost (allowing for some edge cases)
        assert sum(1 for p in products_with_cost if p["price"] > p["cost"]) > len(products_with_cost) * 0.9
