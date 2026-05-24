import json
import logging
import sys
import time
from typing import Any, Dict
from datetime import datetime

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            "filename": record.filename,
            "line_number": record.lineno,
        }
        
        # Inject context (extra attributes)
        if hasattr(record, "trace_id"):
            log_data["trace_id"] = record.trace_id
        if hasattr(record, "span_id"):
            log_data["span_id"] = record.span_id
        if hasattr(record, "extra_info"):
            log_data["extra_info"] = record.extra_info
            
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
            
        return json.dumps(log_data)

def setup_logging(debug: bool = False) -> logging.Logger:
    logger = logging.getLogger("agentic-knowledge-os")
    logger.setLevel(logging.DEBUG if debug else logging.INFO)
    
    # Avoid duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
        
    # Prevent propagation to root logger to avoid double logging
    logger.propagate = False
    return logger

logger = setup_logging(debug=True)
