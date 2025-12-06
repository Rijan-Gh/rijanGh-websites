import logging
import sys
import json
from datetime import datetime
from typing import Dict, Any
import traceback

class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add extra fields
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        return json.dumps(log_data)

def setup_logging():
    """Setup structured logging configuration"""
    
    # Remove default handlers
    for handler in logging.root.handlers[:]:
        logging.root.removeHandler(handler)
    
    # Create logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Console handler with JSON formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(JSONFormatter())
    logger.addHandler(console_handler)
    
    # File handler for errors
    file_handler = logging.FileHandler("logs/app.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(JSONFormatter())
    logger.addHandler(file_handler)
    
    # Set specific loggers to WARNING to reduce noise
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    return logger

def log_request(request, response, duration):
    """Log HTTP request details"""
    extra = {
        "request": {
            "method": request.method,
            "url": str(request.url),
            "client": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        },
        "response": {
            "status_code": response.status_code,
            "size": len(response.body) if hasattr(response, 'body') else 0,
        },
        "duration_ms": duration * 1000,
    }
    
    logging.info("HTTP request completed", extra=extra)

def log_exception(context: str, exception: Exception, extra: Dict[str, Any] = None):
    """Log exception with context"""
    log_extra = {"context": context}
    if extra:
        log_extra.update(extra)
    
    logging.error(
        f"Exception in {context}: {str(exception)}",
        extra=log_extra,
        exc_info=True
    )