"""Structured logging system for Titanium platform."""

import json
import logging
import os
import sys
from datetime import UTC, datetime


class JSONFormatter(logging.Formatter):
    """JSON log formatter for production."""

    def __init__(self, service_name: str = "titanium"):
        super().__init__()
        self.service_name = service_name

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
        }

        if record.exc_info and record.exc_info[0]:
            log_entry["exception"] = self.formatException(record.exc_info)

        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_entry["user_id"] = record.user_id

        if hasattr(record, "extra_data"):
            log_entry["data"] = record.extra_data

        return json.dumps(log_entry)


class ContextFilter(logging.Filter):
    """Add request context to log records."""

    def __init__(self, request_id: str | None = None, user_id: str | None = None):
        super().__init__()
        self.request_id = request_id
        self.user_id = user_id

    def filter(self, record: logging.LogRecord) -> bool:
        if self.request_id:
            record.request_id = self.request_id
        if self.user_id:
            record.user_id = user_id
        return True


class TitaniumLogger:
    """Centralized logger for Titanium platform."""

    _instance = None

    @classmethod
    def get_instance(cls, service_name: str = "titanium") -> "TitaniumLogger":
        if cls._instance is None:
            cls._instance = cls(service_name)
        return cls._instance

    def __init__(self, service_name: str = "titanium"):
        self.service_name = service_name
        self.env = os.getenv("APP_ENV", "development")
        self.log_level = os.getenv("LOG_LEVEL", "DEBUG" if self.env == "development" else "INFO")

        self.logger = logging.getLogger(service_name)
        self.logger.setLevel(getattr(logging, self.log_level, logging.INFO))

        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Configure log handlers based on environment."""
        if self.env == "production":
            handler = logging.StreamHandler(sys.stdout)
            handler.setFormatter(JSONFormatter(self.service_name))
        else:
            handler = logging.StreamHandler(sys.stderr)
            handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S",
                )
            )

        self.logger.addHandler(handler)

    def info(self, message: str, **kwargs):
        self.logger.info(message, extra={"extra_data": kwargs} if kwargs else {})

    def warning(self, message: str, **kwargs):
        self.logger.warning(message, extra={"extra_data": kwargs} if kwargs else {})

    def error(self, message: str, **kwargs):
        self.logger.error(message, extra={"extra_data": kwargs} if kwargs else {})

    def debug(self, message: str, **kwargs):
        self.logger.debug(message, extra={"extra_data": kwargs} if kwargs else {})

    def critical(self, message: str, **kwargs):
        self.logger.critical(message, extra={"extra_data": kwargs} if kwargs else {})

    def exception(self, message: str, **kwargs):
        self.logger.exception(message, extra={"extra_data": kwargs} if kwargs else {})

    def log_request(self, method: str, path: str, status_code: int, duration_ms: float, **kwargs):
        """Log an HTTP request."""
        level = logging.WARNING if status_code >= 500 else logging.INFO
        self.logger.log(
            level,
            f"{method} {path} {status_code} {duration_ms:.0f}ms",
            extra={
                "extra_data": {
                    "type": "http_request",
                    "method": method,
                    "path": path,
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                    **kwargs,
                }
            },
        )

    def log_agent_task(self, task_id: str, agent_type: str, status: str, **kwargs):
        """Log an agent task event."""
        self.logger.info(
            f"Agent task {task_id} ({agent_type}): {status}",
            extra={
                "extra_data": {
                    "type": "agent_task",
                    "task_id": task_id,
                    "agent_type": agent_type,
                    "status": status,
                    **kwargs,
                }
            },
        )


titanium_logger = TitaniumLogger.get_instance()
