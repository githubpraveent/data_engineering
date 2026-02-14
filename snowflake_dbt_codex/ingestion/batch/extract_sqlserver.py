import os


def extract_sqlserver():
    # Placeholder for SQL Server extraction logic.
    # Use pyodbc or sqlalchemy to connect and pull incremental tables.
    return [
        {"type": "sqlserver", "table": "claims", "watermark": "updated_at"},
        {"type": "sqlserver", "table": "members", "watermark": "updated_at"},
    ]
