"""
configurations for logging
"""

import logging
import logging.config

from app.config import get_settings

def setup_logging():
    if getattr(setup_logging, "_initialized", False):
        return
    
    settings = get_settings()
    log_level = settings.log_level
    log_file = settings.log_file

    if settings.env == "development":
        log_format = "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    elif settings.env == "test":
        log_format = "[%(levelname)s] %(name)s: %(message)s"
    else:  # production
        log_format = "%(asctime)s - %(levelname)s - %(message)s"

    logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {"format": log_format},
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "level": log_level,
            },
            "file": {
                "class": "logging.FileHandler",
                "formatter": "default",
                "filename": log_file,
                "level": log_level,
            },
        },
        "root": {
            "handlers": ["console", "file"],
            "level": log_level,
        },
    }

    logging.config.dictConfig(logging_config)
    setup_logging._initialized = True