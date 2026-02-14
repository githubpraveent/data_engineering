"""
Aggregation Logic
Builds daily/weekly aggregates and rollups for analytics
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta
from collections import defaultdict

# Add parent directory to path for imports
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.bigtable_client import BigTableClient
from utils.retry_handler import RetryHandler

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Aggregator:
    """
    Aggregates data from fact table into aggregate tables
    """

    def __init__(
        self,
        project_id: str,
        instance_id: str,
        fact_table: str = "events_fact",
        aggregate_table: str = "events_aggregate",
    ):
        """
        Initialize aggregator

        Args:
            project_id: GCP project ID
            instance_id: Bigtable instance ID
            fact_table: Name of fact table
            aggregate_table: Name of aggregate table
        """
        self.bigtable_client = BigTableClient(
            project_id, instance_id, fact_table, aggregate_table
        )
        self.retry_handler = RetryHandler(max_retries=5)

    def compute_daily_aggregates(
        self, date: datetime, dimensions: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compute daily aggregates for a specific date

        Args:
            date: Date to aggregate
            dimensions: List of dimensions to aggregate by (e.g., ['user_id', 'song_id'])

        Returns:
            Dictionary of aggregate statistics
        """
        dimensions = dimensions or ["user_id"]

        logger.info(f"Computing daily aggregates for {date.strftime('%Y-%m-%d')}")

        # Calculate date range
        start_date = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_date = start_date + timedelta(days=1)

        # Note: In production, you would scan the fact table for events in this date range
        # For this example, we'll compute aggregates from retrieved events
        # In a real implementation, you might:
        # 1. Scan fact table by timestamp range
        # 2. Process events in batches
        # 3. Compute aggregates in-memory
        # 4. Write aggregates back to aggregate table

        aggregates = {}
        total_events = 0

        # For each dimension, compute aggregates
        for dimension in dimensions:
            dim_aggregates = defaultdict(lambda: {"count": 0})

            # In a real implementation, you would:
            # 1. Scan fact table with row key prefix filters
            # 2. Group events by dimension value
            # 3. Compute statistics

            # Placeholder: In production, replace with actual fact table scan
            logger.debug(f"Computing aggregates for dimension: {dimension}")

            # Example structure (replace with actual data retrieval)
            aggregates[f"{dimension}_stats"] = dim_aggregates

        # Write aggregates to Bigtable
        for dimension in dimensions:
            # For each unique dimension value, write aggregate
            # This is a simplified example
            stats = {
                "total_events": total_events,
                "date": date.strftime("%Y-%m-%d"),
            }
            # In production, iterate through actual dimension values
            # self.bigtable_client.write_aggregate(dimension, dim_value, date, stats)

        logger.info(
            f"Computed daily aggregates for {date.strftime('%Y-%m-%d')}: "
            f"{total_events} total events"
        )

        return aggregates

    def compute_user_daily_stats(
        self, user_id: str, date: datetime
    ) -> Dict[str, Any]:
        """
        Compute daily statistics for a specific user

        Args:
            user_id: User ID
            date: Date to aggregate

        Returns:
            Dictionary of user statistics
        """
        logger.debug(f"Computing daily stats for user {user_id} on {date.strftime('%Y-%m-%d')}")

        # Retrieve user events for the day
        start_time = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_time = start_time + timedelta(days=1)

        try:
            events = self.retry_handler.execute_with_retry(
                self.bigtable_client.get_user_events,
                user_id,
                start_time,
                end_time,
                10000,  # Limit
            )

            # Compute statistics
            stats = {
                "user_id": user_id,
                "date": date.strftime("%Y-%m-%d"),
                "total_events": len(events),
                "event_types": defaultdict(int),
            }

            # Count event types (if event_type field exists)
            for event in events:
                event_type = event.get("event_type") or event.get("type", "unknown")
                stats["event_types"][event_type] += 1

            # Convert defaultdict to regular dict for JSON serialization
            stats["event_types"] = dict(stats["event_types"])

            # Write aggregate to Bigtable
            self.retry_handler.execute_with_retry(
                self.bigtable_client.write_aggregate,
                "user",
                user_id,
                date,
                stats,
            )

            logger.info(
                f"Computed stats for user {user_id}: {stats['total_events']} events"
            )

            return stats

        except Exception as e:
            logger.error(f"Error computing user stats: {str(e)}", exc_info=True)
            raise

    def compute_hourly_aggregates(
        self, date: datetime
    ) -> Dict[str, Dict[str, Any]]:
        """
        Compute hourly aggregates for a specific date

        Args:
            date: Date to aggregate

        Returns:
            Dictionary mapping hour to aggregate statistics
        """
        logger.info(f"Computing hourly aggregates for {date.strftime('%Y-%m-%d')}")

        hourly_stats = {}

        # For each hour of the day
        for hour in range(24):
            hour_start = date.replace(hour=hour, minute=0, second=0, microsecond=0)
            hour_end = hour_start + timedelta(hours=1)

            # In production, scan fact table for events in this hour range
            # For this example, we'll create placeholder stats

            stats = {
                "hour": hour,
                "total_events": 0,  # Replace with actual count
                "date": date.strftime("%Y-%m-%d"),
            }

            hourly_stats[f"{hour:02d}:00"] = stats

        logger.info(f"Computed hourly aggregates for {date.strftime('%Y-%m-%d')}")
        return hourly_stats

    def compute_weekly_aggregates(
        self, week_start_date: datetime
    ) -> Dict[str, Any]:
        """
        Compute weekly aggregates for a week starting on week_start_date

        Args:
            week_start_date: Start date of the week (Monday)

        Returns:
            Dictionary of weekly aggregate statistics
        """
        logger.info(
            f"Computing weekly aggregates for week starting {week_start_date.strftime('%Y-%m-%d')}"
        )

        # Aggregate data for the entire week
        week_end_date = week_start_date + timedelta(days=7)

        # In production, scan fact table for events in this date range
        stats = {
            "week_start": week_start_date.strftime("%Y-%m-%d"),
            "week_end": week_end_date.strftime("%Y-%m-%d"),
            "total_events": 0,  # Replace with actual count
        }

        logger.info(
            f"Computed weekly aggregates for week starting {week_start_date.strftime('%Y-%m-%d')}"
        )
        return stats

    def run_daily_aggregation_job(self, date: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Run daily aggregation job for a specific date

        Args:
            date: Date to aggregate (defaults to yesterday)

        Returns:
            Job statistics
        """
        if date is None:
            # Default to yesterday
            date = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=1)

        logger.info(f"Starting daily aggregation job for {date.strftime('%Y-%m-%d')}")

        job_stats = {
            "date": date.strftime("%Y-%m-%d"),
            "started_at": datetime.utcnow().isoformat(),
            "daily_aggregates": 0,
            "hourly_aggregates": 0,
            "errors": [],
        }

        try:
            # Compute daily aggregates
            daily_agg = self.compute_daily_aggregates(date)
            job_stats["daily_aggregates"] = len(daily_agg)

            # Compute hourly aggregates
            hourly_agg = self.compute_hourly_aggregates(date)
            job_stats["hourly_aggregates"] = len(hourly_agg)

            job_stats["completed_at"] = datetime.utcnow().isoformat()
            job_stats["status"] = "success"

            logger.info(
                f"Daily aggregation job completed for {date.strftime('%Y-%m-%d')}"
            )

        except Exception as e:
            logger.error(f"Error in daily aggregation job: {str(e)}", exc_info=True)
            job_stats["status"] = "failed"
            job_stats["errors"].append(str(e))

        return job_stats

    def close(self):
        """Close connections"""
        self.bigtable_client.close()


def main():
    """Main entry point for aggregation job"""
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Run aggregation job")
    parser.add_argument(
        "--project-id",
        default=os.getenv("GCP_PROJECT_ID"),
        help="GCP project ID",
    )
    parser.add_argument(
        "--instance-id",
        default=os.getenv("BIGTABLE_INSTANCE"),
        help="Bigtable instance ID",
    )
    parser.add_argument(
        "--date",
        help="Date to aggregate (YYYY-MM-DD), defaults to yesterday",
    )
    parser.add_argument(
        "--dimension",
        help="Dimension to aggregate by (e.g., user_id)",
        default="user_id",
    )

    args = parser.parse_args()

    if not args.project_id or not args.instance_id:
        parser.error(
            "--project-id and --instance-id are required or set as environment variables"
        )

    # Parse date
    date = None
    if args.date:
        try:
            date = datetime.strptime(args.date, "%Y-%m-%d")
        except ValueError:
            parser.error(f"Invalid date format: {args.date}. Use YYYY-MM-DD")

    # Create aggregator
    aggregator = Aggregator(args.project_id, args.instance_id)

    try:
        # Run aggregation job
        stats = aggregator.run_daily_aggregation_job(date)
        print(f"Aggregation job stats: {stats}")

    except Exception as e:
        logger.error(f"Aggregation job failed: {str(e)}", exc_info=True)
        return 1
    finally:
        aggregator.close()

    return 0


if __name__ == "__main__":
    exit(main())
