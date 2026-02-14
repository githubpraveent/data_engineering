#!/usr/bin/env python3
"""
Order ingestion script
Extracts order data from source system and loads to data lake bronze layer
"""

import os
import sys
import json
import argparse
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(str(Path(__file__).parent.parent))

def connect_to_source():
    """Connect to source system (API, database, etc.)"""
    # Placeholder: Replace with actual connection logic
    # Example: database connection, API client, file system access
    print("Connecting to source system...")
    return None

def extract_orders(start_date, end_date, source_conn):
    """Extract orders from source system for date range"""
    # Placeholder: Replace with actual extraction logic
    print(f"Extracting orders from {start_date} to {end_date}")
    
    # Example extracted data
    sample_orders = [
        {
            "order_id": 1,
            "customer_id": 101,
            "store_id": 1,
            "order_date": start_date.strftime('%Y-%m-%d'),
            "total_amount": 150.00,
            "status": "COMPLETED"
        }
    ]
    
    return sample_orders

def transform_orders(orders):
    """Transform orders to standard format"""
    transformed = []
    for order in orders:
        # Standardize format, validate, clean
        transformed.append({
            "order_id": int(order.get("order_id")),
            "customer_id": int(order.get("customer_id")),
            "store_id": int(order.get("store_id")),
            "order_date": order.get("order_date"),
            "total_amount": float(order.get("total_amount", 0)),
            "status": order.get("status", "").upper().strip()
        })
    return transformed

def load_to_bronze(data, output_path, date_partition):
    """Load data to bronze layer (S3, GCS, local, etc.)"""
    # Create output directory structure
    output_dir = Path(output_path) / f"date={date_partition}"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Write data (in real implementation, this would write to cloud storage)
    output_file = output_dir / "orders.json"
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"Loaded {len(data)} orders to {output_file}")
    return str(output_file)

def main():
    parser = argparse.ArgumentParser(description='Ingest orders from source system')
    parser.add_argument('--start-date', type=str, required=True,
                       help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end-date', type=str, required=True,
                       help='End date (YYYY-MM-DD)')
    parser.add_argument('--output-path', type=str,
                       default='bronze/orders',
                       help='Output path in bronze layer')
    
    args = parser.parse_args()
    
    start_date = datetime.strptime(args.start_date, '%Y-%m-%d')
    end_date = datetime.strptime(args.end_date, '%Y-%m-%d')
    
    # Connect to source
    source_conn = connect_to_source()
    
    # Extract
    orders = extract_orders(start_date, end_date, source_conn)
    
    # Transform
    transformed_orders = transform_orders(orders)
    
    # Load (partition by date)
    for single_date in [start_date + timedelta(days=x) 
                       for x in range((end_date - start_date).days + 1)]:
        date_orders = [o for o in transformed_orders 
                      if o['order_date'] == single_date.strftime('%Y-%m-%d')]
        if date_orders:
            load_to_bronze(date_orders, args.output_path, 
                          single_date.strftime('%Y-%m-%d'))
    
    print("Order ingestion completed successfully")

if __name__ == '__main__':
    main()

