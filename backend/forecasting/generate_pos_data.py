import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random
import argparse
import os
import uuid
from decimal import Decimal, ROUND_HALF_UP

def generate_sku_sales(store_id, product_id, start_date, days, base_demand=100):
    data = []
    date = datetime.strptime(start_date, "%Y-%m-%d")

    for i in range(days):
        current_date = date + timedelta(days=i)
        dow = current_date.weekday()

        temperature = np.random.normal(loc=85 + 5 * (dow in [5, 6]), scale=5)
        social_mentions = np.random.poisson(2)
        news_mentions = np.random.binomial(n=5, p=0.3)

        temp_factor = (temperature - 85) * 1.2
        social_factor = social_mentions * 4
        news_factor = news_mentions * 2
        noise = np.random.normal(0, 5)

        units_sold = max(0, int(base_demand + temp_factor + social_factor + news_factor + noise))
        if units_sold == 0:
            continue

        unit_price = Decimal(round(random.uniform(1.0, 5.0), 2)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        quantity = units_sold
        discount = Decimal(round(random.uniform(0, 1), 2)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        tax = (unit_price * quantity * Decimal("0.08")).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        total = (unit_price * quantity - discount + tax).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        data.append({
            "transaction_id": str(uuid.uuid4()),
            "store_id": store_id,
            "product_id": product_id,
            "quantity": quantity,
            "unit_price": float(unit_price),
            "total_amount": float(total),
            "discount": float(discount),
            "tax": float(tax),
            "date": current_date.strftime("%Y-%m-%d"),
            "temperature": round(temperature, 1),
            "social_mentions": social_mentions,
            "news_mentions": news_mentions
        })

    return data

def generate_dataset(output_path, skus, stores, start_date="2024-06-01", days=30):
    full_data = []

    for store in stores:
        for sku in skus:
            base = random.randint(80, 140)
            full_data.extend(generate_sku_sales(store, sku, start_date, days, base))

    df = pd.DataFrame(full_data)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"[✓] Generated {len(df)} rows → {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=str, default="pos_data/pos_data.csv")
    parser.add_argument("--skus", nargs="+", default=["GATORADE-TX-32OZ", "ICECREAM-CHOC-BAR", "COLA-2L-BTL",
                        "WATER-SPRING-1L", "CHIPS-BBQ-200G", "COFFEE-CAN-250ML",
                        "ENERGY-DRINK-500ML", "JUICE-APPLE-1L", "SNACK-MIX-NUTS",
                        "MILK-DAIRY-500ML", "TEA-GREEN-BAG20", "SODA-ORANGE-330ML"
    ])
    parser.add_argument("--stores", nargs="+", default=["TX001", "TX002", "TX003", "TX004"])
    parser.add_argument("--start_date", type=str, default="2024-06-01")
    parser.add_argument("--days", type=int, default=30)

    args = parser.parse_args()

    generate_dataset(
        output_path=args.output,
        skus=args.skus,
        stores=args.stores,
        start_date=args.start_date,
        days=args.days
    )
