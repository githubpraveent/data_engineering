"""
Monitoring and Alerting
Sends alerts for data quality failures and pipeline errors
"""

import logging
import os
from typing import Dict, Any, Optional
from datetime import datetime
import json

try:
    from slack_sdk import WebClient
    from slack_sdk.errors import SlackApiError
except ImportError:
    WebClient = None
    SlackApiError = None

from google.cloud import logging as cloud_logging

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manages alerts for data quality failures and pipeline errors
    """

    def __init__(
        self,
        slack_webhook_url: Optional[str] = None,
        slack_channel: str = "#data-pipeline-alerts",
        enable_cloud_logging: bool = True,
    ):
        """
        Initialize alert manager

        Args:
            slack_webhook_url: Slack webhook URL (or set SLACK_WEBHOOK_URL env var)
            slack_channel: Slack channel for alerts
            enable_cloud_logging: Enable Cloud Logging
        """
        self.slack_webhook_url = slack_webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.slack_channel = slack_channel
        self.enable_cloud_logging = enable_cloud_logging

        # Initialize Slack client if webhook URL is provided
        if self.slack_webhook_url and WebClient:
            # For webhook, we'll use requests directly
            self.use_slack = True
        else:
            self.use_slack = False
            if not self.slack_webhook_url:
                logger.warning("Slack webhook URL not provided, Slack alerts disabled")

        # Initialize Cloud Logging
        if self.enable_cloud_logging:
            try:
                self.cloud_logger = cloud_logging.Client().logger("data-pipeline")
            except Exception as e:
                logger.warning(f"Failed to initialize Cloud Logging: {str(e)}")
                self.cloud_logger = None
        else:
            self.cloud_logger = None

    def send_alert(
        self,
        title: str,
        message: str,
        severity: str = "error",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send an alert

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (info, warning, error, critical)
            metadata: Additional metadata

        Returns:
            True if alert was sent successfully
        """
        success = True

        # Log to Cloud Logging
        if self.cloud_logger:
            try:
                log_level = {
                    "info": "INFO",
                    "warning": "WARN",
                    "error": "ERROR",
                    "critical": "CRITICAL",
                }.get(severity.lower(), "ERROR")

                payload = {
                    "title": title,
                    "message": message,
                    "severity": severity,
                    "timestamp": datetime.utcnow().isoformat(),
                    "metadata": metadata or {},
                }

                self.cloud_logger.log_struct(
                    payload,
                    severity=log_level,
                    labels={"alert_type": "data_pipeline"},
                )
            except Exception as e:
                logger.error(f"Failed to log to Cloud Logging: {str(e)}")
                success = False

        # Send to Slack
        if self.use_slack:
            try:
                self._send_slack_alert(title, message, severity, metadata)
            except Exception as e:
                logger.error(f"Failed to send Slack alert: {str(e)}")
                success = False

        # Also log locally
        log_method = {
            "info": logger.info,
            "warning": logger.warning,
            "error": logger.error,
            "critical": logger.critical,
        }.get(severity.lower(), logger.error)

        log_method(f"{title}: {message}")

        return success

    def _send_slack_alert(
        self,
        title: str,
        message: str,
        severity: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Send alert to Slack via webhook"""
        import requests

        # Color mapping for severity
        color_map = {
            "info": "#36a64f",  # Green
            "warning": "#ff9800",  # Orange
            "error": "#f44336",  # Red
            "critical": "#d32f2f",  # Dark red
        }
        color = color_map.get(severity.lower(), "#f44336")

        # Build Slack message payload
        slack_payload = {
            "channel": self.slack_channel,
            "username": "Data Pipeline Alerts",
            "icon_emoji": ":warning:",
            "attachments": [
                {
                    "color": color,
                    "title": title,
                    "text": message,
                    "fields": [
                        {"title": "Severity", "value": severity.upper(), "short": True},
                        {
                            "title": "Timestamp",
                            "value": datetime.utcnow().isoformat(),
                            "short": True,
                        },
                    ],
                    "footer": "Data Pipeline",
                    "ts": int(datetime.utcnow().timestamp()),
                }
            ],
        }

        # Add metadata as additional fields
        if metadata:
            for key, value in metadata.items():
                slack_payload["attachments"][0]["fields"].append(
                    {"title": key, "value": str(value), "short": True}
                )

        # Send to Slack
        response = requests.post(self.slack_webhook_url, json=slack_payload, timeout=10)
        response.raise_for_status()

    def alert_quality_failure(
        self,
        event_id: str,
        errors: list,
        event_data: Optional[Dict[str, Any]] = None,
    ):
        """
        Send alert for data quality failure

        Args:
            event_id: Event ID that failed
            errors: List of validation errors
            event_data: Event data (optional)
        """
        title = "Data Quality Check Failed"
        message = f"Event {event_id} failed quality checks:\n" + "\n".join(
            f"- {error}" for error in errors
        )

        metadata = {
            "event_id": event_id,
            "error_count": len(errors),
            "errors": errors,
        }

        if event_data:
            metadata["user_id"] = event_data.get("user_id")

        self.send_alert(title, message, severity="error", metadata=metadata)

    def alert_pipeline_error(
        self,
        operation: str,
        error: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Send alert for pipeline error

        Args:
            operation: Operation that failed
            error: Error message
            metadata: Additional metadata
        """
        title = "Pipeline Error"
        message = f"Error in {operation}: {error}"

        alert_metadata = {"operation": operation, "error": error}
        if metadata:
            alert_metadata.update(metadata)

        self.send_alert(
            title, message, severity="error", metadata=alert_metadata
        )

    def alert_ingestion_complete(
        self,
        stats: Dict[str, Any],
        duration_seconds: float,
    ):
        """
        Send alert for ingestion completion

        Args:
            stats: Ingestion statistics
            duration_seconds: Duration of ingestion in seconds
        """
        title = "Ingestion Completed"
        message = (
            f"Ingested {stats.get('written', 0)} events. "
            f"Total: {stats.get('total_read', 0)}, "
            f"Valid: {stats.get('valid', 0)}, "
            f"Invalid: {stats.get('invalid', 0)}"
        )

        severity = "warning" if stats.get("invalid", 0) > 0 else "info"

        metadata = {
            **stats,
            "duration_seconds": duration_seconds,
        }

        self.send_alert(title, message, severity=severity, metadata=metadata)
