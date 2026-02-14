"""
Data Transformer

Transforms raw extracted data into normalized fact and dimension collections.
"""

from datetime import datetime
from typing import List, Dict, Any, Optional
from loguru import logger
from pymongo.database import Database

from config.settings import Settings


class DataTransformer:
    """Transforms data into MongoDB schema"""

    def __init__(self, settings: Settings):
        self.settings = settings

    def transform(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Transform raw data into fact collection format"""
        logger.info(f"Transforming {len(raw_data)} records")

        transformed_records = []
        
        for idx, record in enumerate(raw_data):
            try:
                transformed = self._transform_record(record, idx)
                if transformed:
                    transformed_records.append(transformed)
            except Exception as e:
                logger.warning(f"Failed to transform record {idx}: {str(e)}")
                continue

        logger.info(f"Successfully transformed {len(transformed_records)} records")
        return transformed_records

    def _transform_record(self, record: Dict[str, Any], index: int) -> Optional[Dict[str, Any]]:
        """Transform a single record into fact table format"""
        # Generate unique ID if not present
        record_id = record.get("id") or record.get("_id") or f"record_{index}_{datetime.now().timestamp()}"
        
        # Normalize transaction fact record
        fact_record = {
            "_id": str(record_id),
            "transaction_id": str(record.get("transaction_id") or record_id),
            "timestamp": self._parse_timestamp(record.get("timestamp") or record.get("date") or datetime.now()),
            "product_id": str(record.get("product_id") or record.get("product") or ""),
            "customer_id": str(record.get("customer_id") or record.get("customer") or ""),
            "quantity": self._parse_numeric(record.get("quantity") or record.get("qty") or 1),
            "unit_price": self._parse_numeric(record.get("unit_price") or record.get("price") or 0.0),
            "total_amount": self._parse_numeric(record.get("total_amount") or record.get("total") or 0.0),
            "currency": record.get("currency") or "USD",
            "payment_method": record.get("payment_method") or record.get("payment") or "unknown",
            "region": record.get("region") or record.get("location") or "unknown",
            "category": record.get("category") or record.get("product_category") or "unknown",
            "metadata": {
                "source": self.settings.source_type,
                "extracted_at": datetime.now().isoformat(),
                "original_record": {k: v for k, v in record.items() if k not in ["id", "_id", "transaction_id", "timestamp", "date"]}
            },
            "created_at": datetime.now(),
            "updated_at": datetime.now()
        }

        # Calculate total if not present
        if not fact_record["total_amount"] or fact_record["total_amount"] == 0:
            fact_record["total_amount"] = fact_record["quantity"] * fact_record["unit_price"]

        return fact_record

    def _parse_timestamp(self, value: Any) -> datetime:
        """Parse timestamp from various formats"""
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            # Try common date formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%d",
                "%m/%d/%Y",
                "%d/%m/%Y"
            ]
            
            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            
            # Try ISO format
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                pass

        # Default to now if parsing fails
        logger.warning(f"Could not parse timestamp: {value}, using current time")
        return datetime.now()

    def _parse_numeric(self, value: Any) -> float:
        """Parse numeric value"""
        if isinstance(value, (int, float)):
            return float(value)
        
        if isinstance(value, str):
            # Remove currency symbols and commas
            cleaned = value.replace("$", "").replace(",", "").strip()
            try:
                return float(cleaned)
            except ValueError:
                return 0.0

        return 0.0

    def build_aggregates(self, db: Database):
        """Build aggregate collections from fact data"""
        logger.info("Building aggregate collections")

        try:
            facts_collection = db[self.settings.collection_facts]
            aggregates_collection = db[self.settings.collection_aggregates]

            # Daily aggregates pipeline
            pipeline = [
                {
                    "$group": {
                        "_id": {
                            "date": {
                                "$dateToString": {
                                    "format": "%Y-%m-%d",
                                    "date": "$timestamp"
                                }
                            },
                            "region": "$region",
                            "category": "$category"
                        },
                        "total_transactions": {"$sum": 1},
                        "total_revenue": {"$sum": "$total_amount"},
                        "total_quantity": {"$sum": "$quantity"},
                        "avg_transaction_value": {"$avg": "$total_amount"},
                        "unique_products": {"$addToSet": "$product_id"},
                        "unique_customers": {"$addToSet": "$customer_id"}
                    }
                },
                {
                    "$project": {
                        "_id": 0,
                        "date": "$_id.date",
                        "region": "$_id.region",
                        "category": "$_id.category",
                        "total_transactions": 1,
                        "total_revenue": 1,
                        "total_quantity": 1,
                        "avg_transaction_value": 1,
                        "unique_products_count": {"$size": "$unique_products"},
                        "unique_customers_count": {"$size": "$unique_customers"},
                        "updated_at": datetime.now()
                    }
                },
                {
                    "$merge": {
                        "into": self.settings.collection_aggregates,
                        "whenMatched": "replace",
                        "whenNotMatched": "insert"
                    }
                }
            ]

            result = facts_collection.aggregate(pipeline)
            count = len(list(result))
            
            logger.info(f"Created/updated {count} aggregate records")

            # Create indexes on aggregates collection
            aggregates_collection.create_index([("date", 1), ("region", 1), ("category", 1)])
            aggregates_collection.create_index([("date", 1)])

        except Exception as e:
            logger.error(f"Failed to build aggregates: {str(e)}")
            raise
