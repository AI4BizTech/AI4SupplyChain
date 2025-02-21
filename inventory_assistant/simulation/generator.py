# inventory_assistant/simulation/generator.py
import random
from datetime import datetime
from uuid import uuid4
from inventory_assistant.models.laptop import Laptop, WarehouseStock, Transaction
from inventory_assistant.models.laptop import LaptopBrand, LaptopCategory, Warehouse
from inventory_assistant.config import (
    INITIAL_STOCK_RANGES,
    PRICE_RANGES,
    MIN_STOCK_LEVELS,
    LAPTOP_MODELS,
    DAILY_TRANSACTION_RANGES,
    TRANSACTION_PROBABILITY
)

class DataGenerator:
    def generate_laptop_models(self) -> list[Laptop]:
        laptops = []
        for category, models in LAPTOP_MODELS.items():
            price_range = PRICE_RANGES[category]
            min_stock = MIN_STOCK_LEVELS[category]
            
            for model_info in models:
                model_id = f"{model_info['brand'].lower()}-{model_info['model'].lower().replace(' ', '-')}"
                laptop = Laptop(
                    model_id=model_id,
                    brand=LaptopBrand[model_info['brand']],
                    model_name=model_info['model'],
                    category=LaptopCategory[category.upper()],
                    unit_price=round(random.uniform(*price_range), 2),
                    min_stock=min_stock
                )
                laptops.append(laptop)
        return laptops

    def generate_initial_stock(self, laptops: list[Laptop]) -> list[WarehouseStock]:
        stocks = []
        for laptop in laptops:
            stock_range = INITIAL_STOCK_RANGES[laptop.category.lower()]
            for warehouse in Warehouse:
                stock = WarehouseStock(
                    model_id=laptop.model_id,
                    warehouse_id=warehouse,
                    quantity=random.randint(*stock_range)
                )
                stocks.append(stock)
        return stocks

    def generate_daily_transactions(self, laptops: list[Laptop], date: datetime) -> list[Transaction]:
        transactions = []
        for laptop in laptops:
            category = laptop.category.lower()
            if random.random() <= TRANSACTION_PROBABILITY[category]:
                quantity_range = DAILY_TRANSACTION_RANGES[category]
                transaction = Transaction(
                    transaction_id=str(uuid4()),
                    date=date,
                    model_id=laptop.model_id,
                    quantity=-random.randint(*quantity_range),
                    warehouse_id=random.choice(list(Warehouse)),
                    type="SALE"
                )
                transactions.append(transaction)
        return transactions