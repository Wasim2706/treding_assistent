import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        timestamp = self.formatTime(record, self.datefmt)
        level = record.levelname
        message = record.getMessage()
        extra = {k: v for k, v in record.__dict__.items() if k not in {
            "name", "msg", "args", "levelname", "levelno", "pathname", "filename",
            "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName",
            "created", "msecs", "relativeCreated", "thread", "threadName",
            "processName", "process", "message"
        }}
        extra_str = f" | {extra}" if extra else ""
        return f"[{timestamp}] [{level:<8}] {record.name}: {message}{extra_str}"


def setup_logger(name: str = "trading_assistant", level: int = logging.INFO) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S"))
        logger.addHandler(handler)
    logger.propagate = False
    return logger


logger = setup_logger()
