"""
Generic Orchestrator Example - Database Model

This module defines the database schema and sample data for the
generic orchestrator example.
"""

import sqlalchemy
from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
import uuid
import random

# Create the declarative base
Base = declarative_base()

# Current date for relative dates
NOW = datetime.now()

class Customer(Base):
    """Customer profile information."""
    
    __tablename__ = "customers"
    
    customer_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    email = Column(String)
    phone = Column(String)
    address = Column(String)
    date_of_birth = Column(DateTime)
    customer_since = Column(DateTime)
    customer_segment = Column(String)
    income_bracket = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    credit_profiles = relationship("CreditProfile", back_populates="customer")
    purchase_history = relationship("Purchase", back_populates="customer")
    preferences = relationship("CustomerPreference", back_populates="customer")

class CreditProfile(Base):
    """Customer credit information."""
    
    __tablename__ = "credit_profiles"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    credit_score = Column(Integer)
    debt_to_income = Column(Float)
    payment_history_score = Column(Float)  # 0-1 score of payment reliability
    income = Column(Float)
    outstanding_debt = Column(Float)
    number_of_loans = Column(Integer)
    number_of_credit_cards = Column(Integer)
    missed_payments_last_year = Column(Integer)
    credit_inquiries_last_year = Column(Integer)
    updated_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    customer = relationship("Customer", back_populates="credit_profiles")

class Product(Base):
    """Product information."""
    
    __tablename__ = "products"
    
    product_id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    category = Column(String)
    subcategory = Column(String)
    price = Column(Float)
    price_tier = Column(String)  # budget, mid-range, premium, luxury
    inventory_count = Column(Integer)
    release_date = Column(DateTime)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    purchases = relationship("Purchase", back_populates="product")

class Purchase(Base):
    """Customer purchase history."""
    
    __tablename__ = "purchases"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    product_id = Column(String, ForeignKey("products.product_id"))
    purchase_date = Column(DateTime, default=datetime.now)
    quantity = Column(Integer, default=1)
    price_paid = Column(Float)
    discount_amount = Column(Float, default=0.0)
    payment_method = Column(String)
    order_id = Column(String)
    
    # Relationships
    customer = relationship("Customer", back_populates="purchase_history")
    product = relationship("Product", back_populates="purchases")

class CustomerPreference(Base):
    """Customer preferences and behavior data."""
    
    __tablename__ = "customer_preferences"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    customer_id = Column(String, ForeignKey("customers.customer_id"))
    preferred_categories = Column(String)  # Comma-separated categories
    recent_searches = Column(String)  # Comma-separated search terms
    email_subscription = Column(Boolean, default=True)
    preferred_payment_method = Column(String)
    favorite_products = Column(String)  # Comma-separated product_ids
    average_session_duration = Column(Float)  # In minutes
    device_preference = Column(String)  # mobile, desktop, tablet
    last_login = Column(DateTime)
    visit_frequency = Column(Float)  # Average visits per week
    updated_at = Column(DateTime, default=datetime.now)
    
    # Relationships
    customer = relationship("Customer", back_populates="preferences")

# Sample data generators
def generate_customer_id():
    return f"cust_{uuid.uuid4().hex[:8]}"

def generate_product_id():
    return f"prod_{random.randint(1000, 9999)}"

def generate_customers(num=10):
    """Generate sample customer data."""
    
    segments = ["standard", "premium", "vip", "business"]
    income_brackets = ["low", "medium", "high", "very-high"]
    
    customers = []
    for i in range(1, num+1):
        customer_id = f"cust_{1000 + i}"
        customer_since = NOW - timedelta(days=random.randint(30, 1500))
        
        customers.append({
            "customer_id": customer_id,
            "name": [
                "Alice Johnson", "Bob Smith", "Charlie Lee", "Diana Patel",
                "Eric Rodriguez", "Fatima Ahmed", "George Wilson", "Hannah Chen",
                "Ian Taylor", "Julia Kim", "Kevin Martinez", "Leila Nguyen",
                "Miguel Brown", "Natalie Park", "Oliver Garcia", "Priya Singh"
            ][i % 16],
            "email": f"customer{i}@example.com",
            "phone": f"555-{100 + i:03d}-{1000 + i:04d}",
            "address": f"{1000 + random.randint(1, 999)} Main St, Anytown, ST {10000 + random.randint(1, 99999)}",
            "date_of_birth": datetime(
                year=1970 + random.randint(0, 35),
                month=random.randint(1, 12),
                day=random.randint(1, 28)
            ),
            "customer_since": customer_since,
            "customer_segment": random.choice(segments),
            "income_bracket": random.choice(income_brackets),
            "is_active": random.random() > 0.1,  # 90% active
            "created_at": customer_since,
            "updated_at": NOW - timedelta(days=random.randint(0, 30))
        })
    
    return customers

def generate_credit_profiles(customers):
    """Generate sample credit profile data."""
    
    credit_profiles = []
    for customer in customers:
        credit_score = random.randint(550, 850)
        payment_history = min(1.0, max(0.2, credit_score / 850.0))
        income = random.randint(30000, 150000)
        debt = income * random.uniform(0.1, 0.6)
        
        credit_profiles.append({
            "customer_id": customer["customer_id"],
            "credit_score": credit_score,
            "debt_to_income": debt / income,
            "payment_history_score": payment_history,
            "income": income,
            "outstanding_debt": debt,
            "number_of_loans": random.randint(0, 3),
            "number_of_credit_cards": random.randint(0, 5),
            "missed_payments_last_year": random.randint(0, 3),
            "credit_inquiries_last_year": random.randint(0, 4),
            "updated_at": NOW - timedelta(days=random.randint(0, 90))
        })
    
    return credit_profiles

def generate_products(num=20):
    """Generate sample product data."""
    
    categories = ["electronics", "clothing", "home", "beauty", "sports"]
    subcategories = {
        "electronics": ["laptops", "phones", "audio", "accessories"],
        "clothing": ["shirts", "pants", "dresses", "shoes"],
        "home": ["kitchen", "furniture", "decor", "bathroom"],
        "beauty": ["skincare", "makeup", "haircare", "fragrance"],
        "sports": ["fitness", "outdoor", "team sports", "accessories"]
    }
    price_tiers = ["budget", "mid-range", "premium", "luxury"]
    
    products = []
    for i in range(1, num+1):
        product_id = f"prod_{1000 + i}"
        category = random.choice(categories)
        
        base_price = {
            "budget": random.uniform(10, 50),
            "mid-range": random.uniform(50, 200),
            "premium": random.uniform(200, 800),
            "luxury": random.uniform(800, 3000)
        }
        
        price_tier = random.choice(price_tiers)
        price = base_price[price_tier]
        
        products.append({
            "product_id": product_id,
            "name": [
                "Wireless Headphones", "Smartphone", "Laptop", "Smart Watch",
                "Bluetooth Speaker", "Tablet", "Fitness Tracker", "Camera",
                "T-Shirt", "Jeans", "Dress", "Shoes", "Jacket", "Sunglasses",
                "Coffee Maker", "Blender", "Toaster", "Vacuum Cleaner",
                "Moisturizer", "Shampoo", "Perfume", "Makeup Kit",
                "Yoga Mat", "Dumbbells", "Tennis Racket", "Backpack"
            ][i % 26],
            "description": f"A high-quality {price_tier} product in the {category} category.",
            "category": category,
            "subcategory": random.choice(subcategories[category]),
            "price": price,
            "price_tier": price_tier,
            "inventory_count": random.randint(0, 1000),
            "release_date": NOW - timedelta(days=random.randint(0, 730)),
            "is_active": random.random() > 0.05,  # 95% active
            "created_at": NOW - timedelta(days=random.randint(100, 1000)),
            "updated_at": NOW - timedelta(days=random.randint(0, 100))
        })
    
    return products

def generate_purchases(customers, products, num_per_customer=5):
    """Generate sample purchase history."""
    
    payment_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
    
    purchases = []
    for customer in customers:
        customer_id = customer["customer_id"]
        num_purchases = random.randint(0, num_per_customer)
        
        for _ in range(num_purchases):
            product = random.choice(products)
            product_id = product["product_id"]
            price = product["price"]
            discount = price * random.uniform(0, 0.25)
            
            purchases.append({
                "customer_id": customer_id,
                "product_id": product_id,
                "purchase_date": NOW - timedelta(days=random.randint(1, 365)),
                "quantity": random.randint(1, 3),
                "price_paid": price - discount,
                "discount_amount": discount,
                "payment_method": random.choice(payment_methods),
                "order_id": f"order_{uuid.uuid4().hex[:8]}"
            })
    
    return purchases

def generate_preferences(customers):
    """Generate sample customer preferences."""
    
    categories = ["electronics", "clothing", "home", "beauty", "sports"]
    search_terms = [
        "laptop", "smartphone", "headphones", "t-shirt", "jeans", 
        "coffee maker", "moisturizer", "fitness", "camera", "shoes"
    ]
    payment_methods = ["credit_card", "debit_card", "paypal", "bank_transfer"]
    devices = ["mobile", "desktop", "tablet"]
    
    preferences = []
    for customer in customers:
        customer_id = customer["customer_id"]
        num_categories = random.randint(1, 4)
        num_searches = random.randint(0, 5)
        
        preferred_cats = ",".join(random.sample(categories, num_categories))
        recent_searches = ",".join(random.sample(search_terms, num_searches)) if num_searches > 0 else ""
        
        preferences.append({
            "customer_id": customer_id,
            "preferred_categories": preferred_cats,
            "recent_searches": recent_searches,
            "email_subscription": random.random() > 0.3,  # 70% subscribed
            "preferred_payment_method": random.choice(payment_methods),
            "favorite_products": f"prod_{1000 + random.randint(1, 20)},prod_{1000 + random.randint(1, 20)}",
            "average_session_duration": random.uniform(1, 30),
            "device_preference": random.choice(devices),
            "last_login": NOW - timedelta(days=random.randint(0, 14)),
            "visit_frequency": random.uniform(0.5, 7),
            "updated_at": NOW - timedelta(days=random.randint(0, 30))
        })
    
    return preferences

# Main function to populate the database
def populate_database(engine):
    """Populate the database with sample data."""
    
    # Create all tables
    Base.metadata.create_all(engine)
    
    # Create a session
    Session = sqlalchemy.orm.sessionmaker(bind=engine)
    session = Session()
    
    try:
        # Generate sample data
        customers_data = generate_customers(15)
        credit_profiles_data = generate_credit_profiles(customers_data)
        products_data = generate_products(30)
        purchases_data = generate_purchases(customers_data, products_data, 8)
        preferences_data = generate_preferences(customers_data)
        
        # Insert customers
        for customer_data in customers_data:
            customer = Customer(**customer_data)
            session.add(customer)
        
        # Insert credit profiles
        for profile_data in credit_profiles_data:
            profile = CreditProfile(**profile_data)
            session.add(profile)
        
        # Insert products
        for product_data in products_data:
            product = Product(**product_data)
            session.add(product)
        
        # Commit to generate IDs
        session.commit()
        
        # Insert purchases
        for purchase_data in purchases_data:
            purchase = Purchase(**purchase_data)
            session.add(purchase)
        
        # Insert preferences
        for preference_data in preferences_data:
            preference = CustomerPreference(**preference_data)
            session.add(preference)
        
        # Commit all changes
        session.commit()
        
        print(f"Successfully populated database with:")
        print(f"  - {len(customers_data)} customers")
        print(f"  - {len(credit_profiles_data)} credit profiles")
        print(f"  - {len(products_data)} products")
        print(f"  - {len(purchases_data)} purchases")
        print(f"  - {len(preferences_data)} customer preferences")
        
    except Exception as e:
        session.rollback()
        print(f"Error populating database: {str(e)}")
        raise
    finally:
        session.close()