"""
Data generation module for CloudLake.

Generates sample retail data (customers, products, stores, orders, order_items).
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict

from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)


class DataGenerator:
    """Generate sample retail data for CloudLake."""

    def __init__(self, output_dir: str = "local_data/raw"):
        self.output_dir = Path(output_dir)
        self.customers = []
        self.products = []
        self.stores = []
        self.orders = []
        self.order_items = []

    def generate_customers(self, n: int = 1000) -> List[Dict]:
        """Generate customer records."""
        customers = []
        for i in range(n):
            created = fake.date_time_between(start_date="-2y", end_date="-30d")
            updated = fake.date_time_between(start_date=created, end_date="now")
            
            customer = {
                "customer_id": f"C{i+1:06d}",
                "email": fake.email(),
                "first_name": fake.first_name(),
                "last_name": fake.last_name(),
                "city": fake.city(),
                "state": fake.state_abbr(),
                "country": random.choice(["US", "CA", "UK", "AU"]),
                "created_at": created.isoformat(),
                "updated_at": updated.isoformat(),
            }
            customers.append(customer)
        
        self.customers = customers
        return customers

    def generate_products(self, n: int = 100) -> List[Dict]:
        """Generate product records."""
        categories = {
            "Electronics": ["Laptop", "Phone", "Tablet", "Headphones", "Monitor"],
            "Apparel": ["Shirt", "Pants", "Jacket", "Shoes", "Hat"],
            "Home": ["Chair", "Desk", "Lamp", "Rug", "Shelf"],
            "Sports": ["Ball", "Racket", "Weights", "Mat", "Bottle"],
            "Books": ["Novel", "Textbook", "Magazine", "Journal", "Guide"],
        }
        
        products = []
        for i in range(n):
            category = random.choice(list(categories.keys()))
            subcategory = random.choice(categories[category])
            cost = round(random.uniform(5, 200), 2)
            price = round(cost * random.uniform(1.3, 2.5), 2)
            created = fake.date_time_between(start_date="-3y", end_date="-1y")
            updated = fake.date_time_between(start_date=created, end_date="now")
            
            product = {
                "product_id": f"P{i+1:05d}",
                "name": f"{fake.word().capitalize()} {subcategory}",
                "category": category,
                "subcategory": subcategory,
                "price": price,
                "cost": cost,
                "created_at": created.isoformat(),
                "updated_at": updated.isoformat(),
            }
            products.append(product)
        
        self.products = products
        return products

    def generate_stores(self, n: int = 20) -> List[Dict]:
        """Generate store records."""
        stores = []
        for i in range(n):
            opened = fake.date_between(start_date="-10y", end_date="-1y")
            closed = None if random.random() > 0.1 else fake.date_between(start_date=opened, end_date="today")
            
            store = {
                "store_id": f"S{i+1:03d}",
                "store_name": f"{fake.city()} {random.choice(['Mall', 'Plaza', 'Center', 'Square'])} Store",
                "city": fake.city(),
                "state": fake.state_abbr(),
                "country": random.choice(["US", "CA"]),
                "opened_at": opened.isoformat(),
                "closed_at": closed.isoformat() if closed else None,
            }
            stores.append(store)
        
        self.stores = stores
        return stores

    def generate_orders(self, n: int = 500) -> List[Dict]:
        """Generate order records."""
        if not self.customers:
            raise ValueError("Generate customers first")
        if not self.stores:
            raise ValueError("Generate stores first")
        
        active_stores = [s for s in self.stores if s["closed_at"] is None]
        
        orders = []
        for i in range(n):
            order_date = fake.date_time_between(start_date="-90d", end_date="now")
            customer = random.choice(self.customers)
            store = random.choice(active_stores) if random.random() > 0.2 else None
            status = random.choices(
                ["complete", "pending", "cancelled"],
                weights=[0.85, 0.10, 0.05]
            )[0]
            
            order = {
                "order_id": f"O{i+1:08d}",
                "customer_id": customer["customer_id"],
                "store_id": store["store_id"] if store else None,
                "order_date": order_date.isoformat(),
                "status": status,
                "total_amount": 0.0,  # Will be calculated from order_items
            }
            orders.append(order)
        
        self.orders = orders
        return orders

    def generate_order_items(self, items_per_order: int = 3) -> List[Dict]:
        """Generate order item records."""
        if not self.orders:
            raise ValueError("Generate orders first")
        if not self.products:
            raise ValueError("Generate products first")
        
        order_items = []
        item_counter = 1
        order_totals = {}
        
        for order in self.orders:
            num_items = random.randint(1, items_per_order * 2)
            order_total = 0.0
            
            for _ in range(num_items):
                product = random.choice(self.products)
                quantity = random.randint(1, 5)
                unit_price = product["price"]
                line_total = round(quantity * unit_price, 2)
                order_total += line_total
                
                order_item = {
                    "order_item_id": f"OI{item_counter:010d}",
                    "order_id": order["order_id"],
                    "product_id": product["product_id"],
                    "quantity": quantity,
                    "unit_price": unit_price,
                    "line_total": line_total,
                }
                order_items.append(order_item)
                item_counter += 1
            
            order_totals[order["order_id"]] = round(order_total, 2)
        
        # Update order totals
        for order in self.orders:
            order["total_amount"] = order_totals.get(order["order_id"], 0.0)
        
        self.order_items = order_items
        return order_items

    def save_to_json(self, entity: str, data: List[Dict], timestamp: str = None):
        """Save data to JSON file."""
        if timestamp is None:
            timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        
        output_path = self.output_dir / entity / f"{timestamp}_generated.json"
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)
        
        print(f"✓ Generated {len(data)} {entity} records → {output_path}")
        return output_path

    def generate_all(
        self,
        n_customers: int = 1000,
        n_products: int = 100,
        n_stores: int = 20,
        n_orders: int = 500,
        items_per_order: int = 3,
    ):
        """Generate all entities and save to JSON."""
        timestamp = datetime.utcnow().strftime("%Y-%m-%dT%H-%M-%S")
        
        print("Generating sample data...")
        print()
        
        self.generate_customers(n_customers)
        self.save_to_json("customers", self.customers, timestamp)
        
        self.generate_products(n_products)
        self.save_to_json("products", self.products, timestamp)
        
        self.generate_stores(n_stores)
        self.save_to_json("stores", self.stores, timestamp)
        
        self.generate_orders(n_orders)
        self.save_to_json("orders", self.orders, timestamp)
        
        self.generate_order_items(items_per_order)
        self.save_to_json("order_items", self.order_items, timestamp)
        
        print()
        print(f"✓ Data generation complete")
        print(f"  Timestamp: {timestamp}")
        print(f"  Location: {self.output_dir}")


if __name__ == "__main__":
    generator = DataGenerator()
    generator.generate_all()
