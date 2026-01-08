"""Logging configuration for the application."""

import logging
import sys
from typing import Any
from app.core.config import settings


class ColoredFormatter(logging.Formatter):
    """Custom formatter with colors for console output."""
    
    grey = "\x1b[38;21m"
    blue = "\x1b[38;5;39m"
    yellow = "\x1b[38;5;226m"
    red = "\x1b[38;5;196m"
    bold_red = "\x1b[31;1m"
    reset = "\x1b[0m"
    
    FORMATS = {
        logging.DEBUG: grey + "%(levelname)s" + reset + " - %(message)s",
        logging.INFO: blue + "%(levelname)s" + reset + " - %(message)s",
        logging.WARNING: yellow + "%(levelname)s" + reset + " - %(message)s",
        logging.ERROR: red + "%(levelname)s" + reset + " - %(message)s",
        logging.CRITICAL: bold_red + "%(levelname)s" + reset + " - %(message)s",
    }
    
    def format(self, record):
        log_fmt = self.FORMATS.get(record.levelno)
        formatter = logging.Formatter(
            fmt=f"%(asctime)s - %(name)s - {log_fmt}",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        return formatter.format(record)


def setup_logging():
    """Configure application logging."""
    
    # Get log level from settings
    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    
    # Use colored formatter in development
    if settings.DEBUG:
        console_handler.setFormatter(ColoredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S"
            )
        )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    
    # Configure uvicorn loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    
    # Configure SQLAlchemy logger
    if settings.DEBUG:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
    else:
        logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """
    Get logger instance for a module.
    
    Args:
        name: Logger name (usually __name__)
    
    Returns:
        Logger instance
    """
    return logging.getLogger(name)
