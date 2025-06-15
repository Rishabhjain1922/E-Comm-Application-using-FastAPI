import logging
import logging.config
from pathlib import Path
from app.core.config import settings

def setup_logging():

    try:
        log_dir = Path(__file__).parent.parent / "logs"
        log_dir.mkdir(exist_ok=True)

        debug_mode = getattr(settings, "DEBUG", True)
        print(f"Debug mode: {debug_mode}")
    # Simple formatter if JSON logger not available


        LOGGING_CONFIG = {
            "version": 1,
            "disable_existing_loggers": False,
            "formatters": {
                "standard": {
                    "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    "datefmt": "%Y-%m-%d %H:%M:%S"
                }
            },
            "handlers": {
                "console": {
                    "class": "logging.StreamHandler",
                    "level": "DEBUG" if debug_mode else "INFO",
                    "formatter": "standard",
                    "stream": "ext://sys.stdout"
                },
                "file": {
                    "class": "logging.FileHandler",  # Use simple FileHandler first
                    "level": "DEBUG" if debug_mode else "INFO",
                    "formatter": "standard",
                    "filename": log_dir / "app.log",
                    "encoding": "utf8",
                    "mode": "a"  # Append mode
                }
            },
            "loggers": {
                "app": {
                    "handlers": ["console", "file"],
                    "level": "DEBUG" if debug_mode else "INFO",
                    "propagate": False
                },
                "app.auth": {  # Specific logger for auth
                    "handlers": ["console", "file"],
                    "level": "INFO",
                    "propagate": False
                }
            }
        }
        logging.config.dictConfig(LOGGING_CONFIG)
        logger = logging.getLogger("app")
        logger.info("Logging configured successfully")
        return logger
    except Exception as e:
        print(f"Logging setup failed: {str(e)}")
    raise
