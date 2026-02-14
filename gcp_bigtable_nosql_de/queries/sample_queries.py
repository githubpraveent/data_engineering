"""
Sample Queries for Bigtable
Example queries for retrieving and analyzing data from Bigtable
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add pipelines directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "pipelines"))

from pipelines.utils.bigtable_client import BigTableClient


def get_user_events_example():
    """Example: Get recent events for a user"""
    print("\n=== Get User Events Example ===")

    # Initialize client
    client = BigTableClient(
        project_id=os.getenv("GCP_PROJECT_ID"),
        instance_id=os.getenv("BIGTABLE_INSTANCE"),
    )

    user_id = "user123"

    # Get events from the last 24 hours
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=1)

    events = client.get_user_events(
        user_id=user_id, start_time=start_time, end_time=end_time, limit=100
    )

    print(f"Found {len(events)} events for user {user_id}")
    for event in events[:5]:  # Show first 5
        print(f"  Event: {event.get('row_key', 'N/A')}")
        print(f"    Metadata: {event.get('metadata_event_id', 'N/A')}")

    client.close()


def get_daily_aggregates_example():
    """Example: Get daily aggregates for a user"""
    print("\n=== Get Daily Aggregates Example ===")

    client = BigTableClient(
        project_id=os.getenv("GCP_PROJECT_ID"),
        instance_id=os.getenv("BIGTABLE_INSTANCE"),
    )

    user_id = "user123"
    date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

    aggregates = client.get_daily_aggregates("user", user_id, date)

    if aggregates:
        print(f"Daily aggregates for user {user_id} on {date.strftime('%Y-%m-%d')}:")
        for key, value in aggregates.items():
            print(f"  {key}: {value}")
    else:
        print(f"No aggregates found for user {user_id} on {date.strftime('%Y-%m-%d')}")

    client.close()


def top_users_by_event_count():
    """Example: Find top N users by event count (conceptual)"""
    print("\n=== Top Users by Event Count Example ===")

    client = BigTableClient(
        project_id=os.getenv("GCP_PROJECT_ID"),
        instance_id=os.getenv("BIGTABLE_INSTANCE"),
    )

    # Note: This is a simplified example
    # In production, you would:
    # 1. Scan the aggregate table for user aggregates
    # 2. Sort by event count
    # 3. Return top N

    print("Top users (this requires scanning aggregate table):")
    print("  Implementation depends on your aggregation strategy")

    client.close()


def events_by_time_range():
    """Example: Get events within a time range"""
    print("\n=== Events by Time Range Example ===")

    client = BigTableClient(
        project_id=os.getenv("GCP_PROJECT_ID"),
        instance_id=os.getenv("BIGTABLE_INSTANCE"),
    )

    # Define time range
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(hours=1)

    print(f"Querying events between {start_time} and {end_time}")

    # Note: In production, you would scan the fact table with appropriate row key filters
    # This is a conceptual example

    client.close()


def hourly_event_counts():
    """Example: Get hourly event counts for a day"""
    print("\n=== Hourly Event Counts Example ===")

    client = BigTableClient(
        project_id=os.getenv("GCP_PROJECT_ID"),
        instance_id=os.getenv("BIGTABLE_INSTANCE"),
    )

    date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

    # Get hourly aggregates from aggregate table
    # In production, you would scan the aggregate table for hourly_stats column family

    print(f"Hourly event counts for {date.strftime('%Y-%m-%d')}:")
    print("  (Implementation requires scanning aggregate table)")

    client.close()


def write_event_example():
    """Example: Write a new event"""
    print("\n=== Write Event Example ===")

    client = BigTableClient(
        project_id=os.getenv("GCP_PROJECT_ID"),
        instance_id=os.getenv("BIGTABLE_INSTANCE"),
    )

    # Create a sample event
    user_id = "user123"
    event_id = f"event_{datetime.utcnow().timestamp()}"
    event_data = {
        "event_type": "page_view",
        "page_url": "/products/item123",
        "session_id": "session456",
        "duration_seconds": 45,
    }

    success = client.write_event(
        user_id=user_id, event_id=event_id, event_data=event_data
    )

    if success:
        print(f"Successfully wrote event {event_id} for user {user_id}")
    else:
        print(f"Failed to write event {event_id}")

    client.close()


def batch_write_example():
    """Example: Write multiple events in a batch"""
    print("\n=== Batch Write Example ===")

    client = BigTableClient(
        project_id=os.getenv("GCP_PROJECT_ID"),
        instance_id=os.getenv("BIGTABLE_INSTANCE"),
    )

    # Create sample events
    events = []
    for i in range(10):
        events.append(
            {
                "user_id": f"user{i % 3}",  # 3 different users
                "event_id": f"event_{datetime.utcnow().timestamp()}_{i}",
                "event_data": {
                    "event_type": "click",
                    "element_id": f"button_{i}",
                    "timestamp": datetime.utcnow().isoformat(),
                },
                "timestamp": datetime.utcnow(),
            }
        )

    written_count = client.batch_write_events(events, batch_size=5)
    print(f"Successfully wrote {written_count} events in batch")

    client.close()


def main():
    """Run all example queries"""
    print("Bigtable Sample Queries")
    print("=" * 50)

    # Check environment variables
    if not os.getenv("GCP_PROJECT_ID") or not os.getenv("BIGTABLE_INSTANCE"):
        print("Error: GCP_PROJECT_ID and BIGTABLE_INSTANCE environment variables must be set")
        return

    try:
        # Run examples
        write_event_example()
        batch_write_example()
        get_user_events_example()
        get_daily_aggregates_example()
        events_by_time_range()
        hourly_event_counts()
        top_users_by_event_count()

        print("\n" + "=" * 50)
        print("All examples completed!")

    except Exception as e:
        print(f"Error running examples: {str(e)}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
