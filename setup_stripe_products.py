#!/usr/bin/env python3
"""
Stripe Product and Price Setup Script
This script creates the necessary products and prices in your Stripe account.
Run this once after setting up your Stripe keys.
"""

import os
import stripe
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize Stripe
stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')

def create_products_and_prices():
    """Create products and prices in Stripe"""
    
    products_config = [
        {
            'name': 'Manuscriptify Monthly Plan',
            'description': 'Monthly subscription to Manuscriptify - Generate 4 books monthly plus 2 audiobooks',
            'price_data': {
                'unit_amount': 3900,  # $39.00
                'currency': 'usd',
                'recurring': {'interval': 'month'},
                'nickname': 'monthly'
            }
        },
        {
            'name': 'Manuscriptify Entry Lifetime',
            'description': 'Entry Lifetime Plan - 6 books/month (4 Pick n\' Mix + 2 AudioBook) forever',
            'price_data': {
                'unit_amount': 9900,  # $99.00
                'currency': 'usd',
                'nickname': 'entry-lifetime'
            }
        },
        {
            'name': 'Manuscriptify Standard Lifetime',
            'description': 'Standard Lifetime Plan - 8 books/month (5 Pick n\' Mix + 3 AudioBook) forever',
            'price_data': {
                'unit_amount': 17900,  # $179.00
                'currency': 'usd',
                'nickname': 'standard-lifetime'
            }
        },
        {
            'name': 'Manuscriptify Pro Lifetime',
            'description': 'Pro Lifetime Plan - 12 books/month (8 Pick n\' Mix & 4 AudioBook) forever',
            'price_data': {
                'unit_amount': 25000,  # $250.00
                'currency': 'usd',
                'nickname': 'pro-lifetime'
            }
        },
        {
            'name': 'Manuscriptify Elite Lifetime',
            'description': 'Elite Lifetime Plan - 100 books/month (80 Pick n\' Mix & 20 AudioBooks) forever',
            'price_data': {
                'unit_amount': 99700,  # $997.00
                'currency': 'usd',
                'nickname': 'elite-lifetime'
            }
        }
    ]
    
    created_prices = {}
    
    for config in products_config:
        try:
            # Create product
            print(f"Creating product: {config['name']}")
            product = stripe.Product.create(
                name=config['name'],
                description=config['description']
            )
            
            # Create price
            price_data = config['price_data'].copy()
            price_data['product'] = product.id
            
            print(f"Creating price for {config['name']}")
            price = stripe.Price.create(**price_data)
            
            created_prices[config['price_data']['nickname']] = price.id
            
            print(f"✅ Created {config['name']}")
            print(f"   Product ID: {product.id}")
            print(f"   Price ID: {price.id}")
            print()
            
        except Exception as e:
            print(f"❌ Error creating {config['name']}: {e}")
            print()
    
    # Print environment variables to add
    print("=" * 60)
    print("ADD THESE TO YOUR .env FILE:")
    print("=" * 60)
    
    env_mapping = {
        'monthly': 'STRIPE_MONTHLY_PRICE_ID',
        'entry-lifetime': 'STRIPE_ENTRY_LIFETIME_PRICE_ID',
        'standard-lifetime': 'STRIPE_STANDARD_LIFETIME_PRICE_ID',
        'pro-lifetime': 'STRIPE_PRO_LIFETIME_PRICE_ID',
        'elite-lifetime': 'STRIPE_ELITE_LIFETIME_PRICE_ID'
    }
    
    for nickname, price_id in created_prices.items():
        env_var = env_mapping.get(nickname)
        if env_var:
            print(f"{env_var}={price_id}")
    
    print("=" * 60)
    
    return created_prices

def list_existing_products():
    """List existing products and prices"""
    print("Existing Products and Prices:")
    print("=" * 40)
    
    try:
        products = stripe.Product.list(limit=20)
        for product in products.data:
            print(f"Product: {product.name} ({product.id})")
            
            # Get prices for this product
            prices = stripe.Price.list(product=product.id)
            for price in prices.data:
                amount = price.unit_amount / 100 if price.unit_amount else 0
                currency = price.currency.upper()
                recurring = f" (recurring: {price.recurring.interval})" if price.recurring else " (one-time)"
                print(f"  Price: ${amount:.2f} {currency}{recurring} - {price.id}")
            print()
            
    except Exception as e:
        print(f"Error listing products: {e}")

if __name__ == "__main__":
    if not stripe.api_key:
        print("❌ STRIPE_SECRET_KEY not found in environment variables")
        print("Please set your Stripe secret key in the .env file")
        exit(1)
    
    print("Manuscriptify Stripe Setup")
    print("=" * 30)
    print()
    
    choice = input("Choose an option:\n1. Create new products and prices\n2. List existing products\n3. Both\nEnter choice (1-3): ")
    
    if choice in ['2', '3']:
        list_existing_products()
        print()
    
    if choice in ['1', '3']:
        confirm = input("This will create new products in your Stripe account. Continue? (y/N): ")
        if confirm.lower() == 'y':
            create_products_and_prices()
        else:
            print("Setup cancelled.")
    
    print("Setup complete!")
