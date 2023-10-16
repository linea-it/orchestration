import os

LOGGING_LEVEL = os.getenv("ORCHEST_LOGGING_LEVEL", "INFO")
LOG_DIR = os.getenv("ORCHEST_LOG_DIR", "../logs")
LOGGING = {
    "version": 1,
    "formatters": {
        "standard": {
            "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "process": {
            "format": "%(asctime)s [%(levelname)s] worker-id:%(process)d: %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "default": {
            "level": "DEBUG",
            "formatter": "standard",
            "class": "logging.StreamHandler",
        },
        "process": {
            "level": LOGGING_LEVEL,
            "formatter": "process",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "process.log"),
            "maxBytes": 1024 * 1024 * 5,  # 5 MB
            "backupCount": 2,
        },
    },
    "loggers": {
        "": {  # root logger
            "handlers": ["default"],
            "propagate": False,
        },
        "orchest": {
            "handlers": ["default", "process"],
            "level": LOGGING_LEVEL,
            "propagate": False,
        },
    },
}
