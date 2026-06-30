import logging
import uuid
from contextvars import ContextVar
from typing import Optional

# Context variable to store correlation IDs
request_id_ctx_var: ContextVar[Optional[str]] = ContextVar("request_id", default=None)

class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        req_id = request_id_ctx_var.get()
        record.correlation_id = req_id if req_id else "N/A"
        return True

def setup_logging():
    logger = logging.getLogger("backend")
    logger.setLevel(logging.INFO)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] [req_id=%(correlation_id)s] %(name)s: %(message)s"
        )
        handler.setFormatter(formatter)
        handler.addFilter(CorrelationIdFilter())
        logger.addHandler(handler)
        
    return logger

logger = setup_logging()

def set_request_id(req_id: Optional[str] = None) -> str:
    if not req_id:
        req_id = str(uuid.uuid4())
    request_id_ctx_var.set(req_id)
    return req_id
