"""
Simple REST API for querying MongoDB data

Provides endpoints for common query patterns and reporting.
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from datetime import datetime, timedelta
from typing import Dict, Any
import os

from queries.examples import QueryExamples

app = Flask(__name__)
CORS(app)  # Enable CORS for frontend integration

# Initialize query examples
mongodb_uri = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
queries = QueryExamples(mongodb_uri)


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat()
    })


@app.route("/api/transactions/recent", methods=["GET"])
def get_recent_transactions():
    """Get recent transactions"""
    limit = int(request.args.get("limit", 10))
    transactions = queries.get_recent_transactions(limit)
    
    # Convert ObjectId to string for JSON serialization
    for tx in transactions:
        if "_id" in tx:
            tx["_id"] = str(tx["_id"])
        if "timestamp" in tx and isinstance(tx["timestamp"], datetime):
            tx["timestamp"] = tx["timestamp"].isoformat()
        if "created_at" in tx and isinstance(tx["created_at"], datetime):
            tx["created_at"] = tx["created_at"].isoformat()
        if "updated_at" in tx and isinstance(tx["updated_at"], datetime):
            tx["updated_at"] = tx["updated_at"].isoformat()
    
    return jsonify({
        "count": len(transactions),
        "transactions": transactions
    })


@app.route("/api/transactions/search", methods=["GET"])
def search_transactions():
    """Search transactions"""
    search_term = request.args.get("q", "")
    field = request.args.get("field", "product_id")
    limit = int(request.args.get("limit", 100))
    
    if not search_term:
        return jsonify({"error": "Search term 'q' is required"}), 400
    
    results = queries.search_transactions(search_term, field, limit)
    
    # Convert ObjectId and datetime for JSON
    for tx in results:
        if "_id" in tx:
            tx["_id"] = str(tx["_id"])
        if "timestamp" in tx and isinstance(tx["timestamp"], datetime):
            tx["timestamp"] = tx["timestamp"].isoformat()
    
    return jsonify({
        "count": len(results),
        "transactions": results
    })


@app.route("/api/transactions/paginated", methods=["GET"])
def get_paginated_transactions():
    """Get paginated transactions"""
    page = int(request.args.get("page", 1))
    page_size = int(request.args.get("page_size", 20))
    
    result = queries.get_paginated_transactions(page, page_size)
    
    # Convert ObjectId and datetime for JSON
    for tx in result["transactions"]:
        if "_id" in tx:
            tx["_id"] = str(tx["_id"])
        if "timestamp" in tx and isinstance(tx["timestamp"], datetime):
            tx["timestamp"] = tx["timestamp"].isoformat()
    
    return jsonify(result)


@app.route("/api/products/top", methods=["GET"])
def get_top_products():
    """Get top products by revenue"""
    limit = int(request.args.get("limit", 10))
    products = queries.get_top_products_by_revenue(limit)
    
    return jsonify({
        "count": len(products),
        "products": products
    })


@app.route("/api/categories/revenue", methods=["GET"])
def get_category_revenue():
    """Get revenue breakdown by category"""
    categories = queries.get_revenue_by_category()
    
    return jsonify({
        "count": len(categories),
        "categories": categories
    })


@app.route("/api/regions/performance", methods=["GET"])
def get_region_performance():
    """Get performance summary by region"""
    performance = queries.get_region_performance_summary()
    
    return jsonify({
        "count": len(performance),
        "regions": performance
    })


@app.route("/api/trends/daily", methods=["GET"])
def get_daily_trends():
    """Get daily revenue trends"""
    days = int(request.args.get("days", 30))
    trends = queries.get_daily_revenue_trends(days)
    
    # Convert datetime to string
    for trend in trends:
        if "updated_at" in trend and isinstance(trend["updated_at"], datetime):
            trend["updated_at"] = trend["updated_at"].isoformat()
    
    return jsonify({
        "count": len(trends),
        "trends": trends
    })


@app.route("/api/customers/<customer_id>/history", methods=["GET"])
def get_customer_history(customer_id: str):
    """Get purchase history for a customer"""
    history = queries.get_customer_purchase_history(customer_id)
    
    # Convert ObjectId and datetime for JSON
    for tx in history:
        if "_id" in tx:
            tx["_id"] = str(tx["_id"])
        if "timestamp" in tx and isinstance(tx["timestamp"], datetime):
            tx["timestamp"] = tx["timestamp"].isoformat()
    
    return jsonify({
        "customer_id": customer_id,
        "count": len(history),
        "transactions": history
    })


if __name__ == "__main__":
    port = int(os.getenv("API_PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "False").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
