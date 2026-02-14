"""
Data Loader

Handles loading transformed data into MongoDB collections with upsert operations.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection
from loguru import logger

from config.settings import Settings


@dataclass
class LoadResult:
    """Data loading result"""
    success: bool
    records_loaded: int = 0
    records_updated: int = 0
    records_inserted: int = 0
    error_message: Optional[str] = None


class DataLoader:
    """Loads data into MongoDB collections"""

    def __init__(self, settings: Settings):
        self.settings = settings
        self.client: Optional[MongoClient] = None
        self.db: Optional[Database] = None
        self._connect()

    def _connect(self):
        """Establish MongoDB connection"""
        try:
            logger.info("Connecting to MongoDB")
            self.client = MongoClient(
                self.settings.mongodb_uri,
                serverSelectionTimeoutMS=5000
            )
            # Test connection
            self.client.admin.command('ping')
            self.db = self.client[self.settings.mongodb_database]
            logger.info(f"Connected to MongoDB database: {self.settings.mongodb_database}")
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {str(e)}")
            raise

    def load(self, data: List[Dict[str, Any]]) -> LoadResult:
        """Load data into MongoDB with upsert"""
        if not self.db:
            return LoadResult(success=False, error_message="Database connection not established")

        try:
            collection = self.db[self.settings.collection_facts]
            
            # Ensure indexes exist
            self._create_indexes(collection)

            records_inserted = 0
            records_updated = 0
            batch_size = self.settings.batch_size

            # Process in batches
            for i in range(0, len(data), batch_size):
                batch = data[i:i + batch_size]
                result = self._upsert_batch(collection, batch)
                records_inserted += result["inserted"]
                records_updated += result["updated"]
                
                logger.debug(f"Processed batch {i//batch_size + 1}: {len(batch)} records")

            total_loaded = records_inserted + records_updated
            logger.info(f"Load complete: {records_inserted} inserted, {records_updated} updated")

            return LoadResult(
                success=True,
                records_loaded=total_loaded,
                records_inserted=records_inserted,
                records_updated=records_updated
            )

        except Exception as e:
            logger.error(f"Failed to load data: {str(e)}")
            return LoadResult(
                success=False,
                error_message=str(e)
            )

    def _upsert_batch(self, collection: Collection, batch: List[Dict[str, Any]]) -> Dict[str, int]:
        """Upsert a batch of records"""
        inserted = 0
        updated = 0

        for record in batch:
            try:
                # Use transaction_id as unique identifier for upsert
                filter_query = {"transaction_id": record.get("transaction_id")}
                
                # Update with upsert
                result = collection.update_one(
                    filter_query,
                    {"$set": record},
                    upsert=True
                )

                if result.upserted_id:
                    inserted += 1
                elif result.modified_count > 0:
                    updated += 1

            except Exception as e:
                logger.warning(f"Failed to upsert record {record.get('_id')}: {str(e)}")
                continue

        return {"inserted": inserted, "updated": updated}

    def _create_indexes(self, collection: Collection):
        """Create indexes on fact collection for performance"""
        try:
            # Primary index on transaction_id
            collection.create_index("transaction_id", unique=True, background=True)
            
            # Indexes for common queries
            collection.create_index("timestamp", background=True)
            collection.create_index("product_id", background=True)
            collection.create_index("customer_id", background=True)
            collection.create_index("region", background=True)
            collection.create_index("category", background=True)
            
            # Compound indexes
            collection.create_index([("timestamp", -1), ("region", 1)], background=True)
            collection.create_index([("product_id", 1), ("timestamp", -1)], background=True)
            
            logger.info("Indexes created/verified on fact collection")

        except Exception as e:
            logger.warning(f"Failed to create some indexes: {str(e)}")

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")

    def __del__(self):
        """Cleanup on destruction"""
        self.close()
