"""
Example MongoDB Queries

Demonstrates various query patterns for fact and aggregate collections.
"""

from datetime import datetime, timedelta
from typing import List, Dict, Any
from pymongo import MongoClient
from pymongo.collation import Collation


class QueryExamples:
    """Example queries for MongoDB collections"""

    def __init__(self, mongodb_uri: str, database: str = "data_pipeline"):
        self.client = MongoClient(mongodb_uri)
        self.db = self.client[database]
        self.facts_collection = self.db["transactions_fact"]
        self.aggregates_collection = self.db["daily_aggregates"]

    def get_recent_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent transactions ordered by timestamp"""
        return list(
            self.facts_collection
            .find()
            .sort("timestamp", -1)
            .limit(limit)
        )

    def get_transactions_by_date_range(
        self, 
        start_date: datetime, 
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Get transactions within a date range"""
        return list(
            self.facts_collection.find({
                "timestamp": {
                    "$gte": start_date,
                    "$lte": end_date
                }
            }).sort("timestamp", ASCENDING)
        )

    def get_transactions_by_region(self, region: str) -> List[Dict[str, Any]]:
        """Get all transactions for a specific region"""
        return list(
            self.facts_collection.find({"region": region})
            .sort("timestamp", -1)
        )

    def get_top_products_by_revenue(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top products by total revenue using aggregation"""
        pipeline = [
            {
                "$group": {
                    "_id": "$product_id",
                    "total_revenue": {"$sum": "$total_amount"},
                    "total_quantity": {"$sum": "$quantity"},
                    "transaction_count": {"$sum": 1}
                }
            },
            {
                "$sort": {"total_revenue": -1}
            },
            {
                "$limit": limit
            },
            {
                "$project": {
                    "_id": 0,
                    "product_id": "$_id",
                    "total_revenue": 1,
                    "total_quantity": 1,
                    "transaction_count": 1,
                    "avg_transaction_value": {
                        "$divide": ["$total_revenue", "$transaction_count"]
                    }
                }
            }
        ]
        
        return list(self.facts_collection.aggregate(pipeline))

    def get_revenue_by_category(self) -> List[Dict[str, Any]]:
        """Get revenue breakdown by category"""
        pipeline = [
            {
                "$group": {
                    "_id": "$category",
                    "total_revenue": {"$sum": "$total_amount"},
                    "transaction_count": {"$sum": 1},
                    "avg_transaction": {"$avg": "$total_amount"}
                }
            },
            {
                "$sort": {"total_revenue": -1}
            },
            {
                "$project": {
                    "_id": 0,
                    "category": "$_id",
                    "total_revenue": 1,
                    "transaction_count": 1,
                    "avg_transaction": 1
                }
            }
        ]
        
        return list(self.facts_collection.aggregate(pipeline))

    def get_daily_revenue_trends(
        self, 
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """Get daily revenue trends using aggregate collection"""
        start_date = (datetime.now() - timedelta(days=days)).strftime("%Y-%m-%d")
        
        return list(
            self.aggregates_collection.find({
                "date": {"$gte": start_date}
            })
            .sort("date", 1)
        )

    def get_customer_purchase_history(
        self, 
        customer_id: str
    ) -> List[Dict[str, Any]]:
        """Get purchase history for a specific customer"""
        return list(
            self.facts_collection.find({"customer_id": customer_id})
            .sort("timestamp", -1)
        )

    def search_transactions(
        self,
        search_term: str,
        field: str = "product_id",
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search transactions by field value (case-insensitive)"""
        return list(
            self.facts_collection.find({
                field: {"$regex": search_term, "$options": "i"}
            })
            .limit(limit)
            .sort("timestamp", -1)
        )

    def get_paginated_transactions(
        self,
        page: int = 1,
        page_size: int = 20
    ) -> Dict[str, Any]:
        """Get paginated transactions"""
        skip = (page - 1) * page_size
        
        total = self.facts_collection.count_documents({})
        transactions = list(
            self.facts_collection.find()
            .sort("timestamp", -1)
            .skip(skip)
            .limit(page_size)
        )
        
        return {
            "transactions": transactions,
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total": total,
                "total_pages": (total + page_size - 1) // page_size
            }
        }

    def get_region_performance_summary(self) -> List[Dict[str, Any]]:
        """Get performance summary by region"""
        pipeline = [
            {
                "$group": {
                    "_id": "$region",
                    "total_revenue": {"$sum": "$total_amount"},
                    "transaction_count": {"$sum": 1},
                    "unique_customers": {"$addToSet": "$customer_id"},
                    "unique_products": {"$addToSet": "$product_id"}
                }
            },
            {
                "$project": {
                    "_id": 0,
                    "region": "$_id",
                    "total_revenue": 1,
                    "transaction_count": 1,
                    "unique_customers_count": {"$size": "$unique_customers"},
                    "unique_products_count": {"$size": "$unique_products"},
                    "avg_transaction_value": {
                        "$divide": ["$total_revenue", "$transaction_count"]
                    }
                }
            },
            {
                "$sort": {"total_revenue": DESCENDING}
            }
        ]
        
        return list(self.facts_collection.aggregate(pipeline))

    def close(self):
        """Close MongoDB connection"""
        self.client.close()


# Example usage function
def run_example_queries(mongodb_uri: str):
    """Run example queries and print results"""
    queries = QueryExamples(mongodb_uri)
    
    print("=== Example Queries ===\n")
    
    # Recent transactions
    print("1. Recent Transactions (10):")
    recent = queries.get_recent_transactions(10)
    print(f"   Found {len(recent)} transactions\n")
    
    # Top products
    print("2. Top Products by Revenue:")
    top_products = queries.get_top_products_by_revenue(5)
    for product in top_products:
        print(f"   Product {product['product_id']}: ${product['total_revenue']:,.2f}")
    print()
    
    # Revenue by category
    print("3. Revenue by Category:")
    categories = queries.get_revenue_by_category()
    for cat in categories:
        print(f"   {cat['category']}: ${cat['total_revenue']:,.2f} ({cat['transaction_count']} transactions)")
    print()
    
    # Daily trends
    print("4. Daily Revenue Trends (last 7 days):")
    trends = queries.get_daily_revenue_trends(7)
    for trend in trends[-7:]:
        print(f"   {trend['date']}: ${trend['total_revenue']:,.2f}")
    
    queries.close()


if __name__ == "__main__":
    import os
    mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
    run_example_queries(mongodb_uri)
