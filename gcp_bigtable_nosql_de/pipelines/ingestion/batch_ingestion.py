"""
Batch Data Ingestion Script
Reads data from CSV/JSON files and loads into Bigtable
"""

import argparse
import csv
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Iterator
import os

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.bigtable_client import BigTableClient
from utils.retry_handler import RetryHandler
from quality.quality_checks import DataQualityChecker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class BatchIngestion:
    """
    Batch ingestion handler for loading data into Bigtable
    """

    def __init__(
        self,
        project_id: str,
        instance_id: str,
        batch_size: int = 100,
        enable_quality_checks: bool = True,
    ):
        """
        Initialize batch ingestion

        Args:
            project_id: GCP project ID
            instance_id: Bigtable instance ID
            batch_size: Batch size for writes
            enable_quality_checks: Enable data quality checks
        """
        self.bigtable_client = BigTableClient(project_id, instance_id)
        self.retry_handler = RetryHandler(max_retries=5)
        self.batch_size = batch_size
        self.quality_checker = (
            DataQualityChecker() if enable_quality_checks else None
        )

    def read_csv(self, file_path: str) -> Iterator[Dict[str, Any]]:
        """
        Read CSV file and yield rows as dictionaries

        Args:
            file_path: Path to CSV file

        Yields:
            Dictionary of row data
        """
        with open(file_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield row

    def read_json(self, file_path: str) -> List[Dict[str, Any]]:
        """
        Read JSON file and return list of records

        Args:
            file_path: Path to JSON file

        Returns:
            List of dictionaries
        """
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
            if isinstance(data, list):
                return data
            elif isinstance(data, dict):
                return [data]
            else:
                raise ValueError(f"Unsupported JSON structure in {file_path}")

    def transform_event(self, raw_event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform raw event data into Bigtable format

        Args:
            raw_event: Raw event dictionary

        Returns:
            Transformed event dictionary
        """
        # Extract required fields
        user_id = raw_event.get("user_id") or raw_event.get("userId")
        event_id = raw_event.get("event_id") or raw_event.get("eventId") or raw_event.get("id")

        if not user_id:
            raise ValueError("user_id is required in event data")
        if not event_id:
            # Generate event ID if not provided
            event_id = f"{user_id}_{datetime.utcnow().timestamp()}"

        # Parse timestamp if present
        timestamp = None
        if "timestamp" in raw_event:
            timestamp_str = raw_event["timestamp"]
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                try:
                    timestamp = datetime.fromtimestamp(float(timestamp_str))
                except (ValueError, TypeError):
                    logger.warning(f"Could not parse timestamp: {timestamp_str}")
                    timestamp = datetime.utcnow()

        # Build event data (exclude metadata fields)
        event_data = {
            k: v
            for k, v in raw_event.items()
            if k not in ["user_id", "userId", "event_id", "eventId", "id", "timestamp"]
        }

        return {
            "user_id": str(user_id),
            "event_id": str(event_id),
            "event_data": event_data,
            "timestamp": timestamp,
        }

    def ingest_file(
        self, file_path: str, file_format: str = "auto"
    ) -> Dict[str, Any]:
        """
        Ingest data from a file

        Args:
            file_path: Path to input file
            file_format: File format ('csv', 'json', or 'auto')

        Returns:
            Dictionary with ingestion statistics
        """
        file_path_obj = Path(file_path)
        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Auto-detect format if needed
        if file_format == "auto":
            if file_path_obj.suffix.lower() == ".csv":
                file_format = "csv"
            elif file_path_obj.suffix.lower() in [".json", ".jsonl"]:
                file_format = "json"
            else:
                raise ValueError(f"Could not auto-detect format for {file_path}")

        logger.info(f"Starting ingestion of {file_path} (format: {file_format})")

        stats = {
            "total_read": 0,
            "valid": 0,
            "invalid": 0,
            "written": 0,
            "errors": [],
        }

        batch = []
        transformed_events = []

        try:
            # Read events based on format
            if file_format == "csv":
                events = self.read_csv(file_path)
            elif file_format == "json":
                events = self.read_json(file_path)
            else:
                raise ValueError(f"Unsupported file format: {file_format}")

            # Process events
            for raw_event in events:
                stats["total_read"] += 1

                try:
                    # Transform event
                    transformed_event = self.transform_event(raw_event)

                    # Run quality checks if enabled
                    if self.quality_checker:
                        quality_result = self.quality_checker.validate_event(
                            transformed_event
                        )
                        if not quality_result["valid"]:
                            stats["invalid"] += 1
                            stats["errors"].append(
                                {
                                    "event_id": transformed_event.get("event_id"),
                                    "errors": quality_result.get("errors", []),
                                }
                            )
                            logger.warning(
                                f"Quality check failed for event {transformed_event.get('event_id')}: "
                                f"{quality_result.get('errors')}"
                            )
                            continue

                    transformed_events.append(transformed_event)
                    batch.append(transformed_event)
                    stats["valid"] += 1

                    # Write batch when reaching batch_size
                    if len(batch) >= self.batch_size:
                        self._write_batch(batch, stats)
                        batch = []

                except Exception as e:
                    stats["invalid"] += 1
                    stats["errors"].append(
                        {"event_id": raw_event.get("id", "unknown"), "error": str(e)}
                    )
                    logger.error(f"Error processing event: {str(e)}", exc_info=True)

            # Write remaining batch
            if batch:
                self._write_batch(batch, stats)

            logger.info(
                f"Ingestion complete. Total: {stats['total_read']}, "
                f"Valid: {stats['valid']}, Invalid: {stats['invalid']}, "
                f"Written: {stats['written']}"
            )

            return stats

        except Exception as e:
            logger.error(f"Error during ingestion: {str(e)}", exc_info=True)
            raise

    def _write_batch(self, batch: List[Dict[str, Any]], stats: Dict[str, Any]) -> None:
        """
        Write a batch of events to Bigtable with retry logic

        Args:
            batch: List of transformed events
            stats: Statistics dictionary to update
        """
        try:
            written = self.retry_handler.execute_with_retry(
                self.bigtable_client.batch_write_events,
                batch,
                self.batch_size,
            )
            stats["written"] += written
            logger.debug(f"Wrote batch of {len(batch)} events")
        except Exception as e:
            logger.error(f"Error writing batch: {str(e)}", exc_info=True)
            # Add batch events to errors
            for event in batch:
                stats["errors"].append(
                    {"event_id": event.get("event_id"), "error": str(e)}
                )

    def close(self):
        """Close connections"""
        self.bigtable_client.close()


def main():
    """Main entry point for batch ingestion"""
    parser = argparse.ArgumentParser(
        description="Batch ingestion script for Bigtable"
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to source file (CSV or JSON)",
    )
    parser.add_argument(
        "--format",
        choices=["csv", "json", "auto"],
        default="auto",
        help="File format (default: auto-detect)",
    )
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
        "--batch-size",
        type=int,
        default=100,
        help="Batch size for writes (default: 100)",
    )
    parser.add_argument(
        "--no-quality-checks",
        action="store_true",
        help="Disable data quality checks",
    )
    parser.add_argument(
        "--output-stats",
        help="Path to output statistics JSON file",
    )

    args = parser.parse_args()

    if not args.project_id or not args.instance_id:
        parser.error("--project-id and --instance-id are required or set as environment variables")

    # Create ingestion handler
    ingestion = BatchIngestion(
        project_id=args.project_id,
        instance_id=args.instance_id,
        batch_size=args.batch_size,
        enable_quality_checks=not args.no_quality_checks,
    )

    try:
        # Run ingestion
        stats = ingestion.ingest_file(args.source, args.format)

        # Output statistics
        if args.output_stats:
            with open(args.output_stats, "w") as f:
                json.dump(stats, f, indent=2, default=str)
            logger.info(f"Statistics written to {args.output_stats}")
        else:
            logger.info(f"Statistics: {json.dumps(stats, indent=2, default=str)}")

        # Exit with error code if there were failures
        if stats["invalid"] > 0:
            sys.exit(1)

    except Exception as e:
        logger.error(f"Ingestion failed: {str(e)}", exc_info=True)
        sys.exit(1)
    finally:
        ingestion.close()


if __name__ == "__main__":
    main()
