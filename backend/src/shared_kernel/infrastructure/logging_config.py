# backend/src/shared_kernel/infrastructure/logging_config.py

import json
import logging
import uuid
from datetime import datetime, timezone
from typing import Callable, Optional
from fastapi import Request, Response


class JSONFormatter(logging.Formatter):
    """
    Formateur de logs JSON structurés sans PII (données personnelles) pour la production.
    """

    def format(self, record: logging.LogRecord) -> str:
        log_object = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, "correlation_id", "none"),
            "tenant_id": getattr(record, "tenant_id", "none"),
        }
        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_object)


def setup_json_logging(level: int = logging.INFO) -> None:
    """
    Configure le handler racine pour sortir les logs en JSON structuré.
    """
    handler = logging.StreamHandler()
    handler.setFormatter(JSONFormatter())

    root_logger = logging.getLogger()
    root_logger.setLevel(level)
    root_logger.handlers = [handler]


async def correlation_id_middleware(request: Request, call_next: Callable) -> Response:
    """
    Middleware qui injecte un identifiant unique X-Correlation-ID dans les logs et la réponse.
    """
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
    request.state.correlation_id = correlation_id

    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id
    return response
