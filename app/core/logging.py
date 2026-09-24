import logging
import json
import re
from datetime import datetime
from contextvars import ContextVar

request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="system")

class JSONFormatter(logging.Formatter):
    PII_PATTERNS = [
        (re.compile(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'), '[REDACTED_EMAIL]'),
        (re.compile(r'\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b'), '[REDACTED_CARD]'),
    ]

    def _mask_pii(self, text: str) -> str:
        for pattern, replacement in self.PII_PATTERNS:
            text = pattern.sub(replacement, text)
        return text

    def format(self, record: logging.LogRecord) -> str:
        log_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "request_id": request_id_ctx_var.get(),
            "message": self._mask_pii(record.getMessage())
        }
        if record.exc_info:
            log_record["traceback"] = self.formatException(record.exc_info)
        return json.dumps(log_record)

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
    return logger