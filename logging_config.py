# utils/logging_config.py
import logging
import os
import sys


def setup_logging():  # <--- Make sure this line exists and is spelled exactly like this
    """
    Configures the Python logging system for the application.
    Log level can be controlled via the LOG_LEVEL environment variable.
    """
    # ... (rest of your logging configuration code) ...
    log_level_str = os.environ.get("LOG_LEVEL", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    # Optional: Add a file handler for more persistent logs
    # if os.environ.get('ENABLE_FILE_LOGGING', 'false').lower() == 'true':
    #     file_handler = logging.FileHandler('application.log')
    #     file_handler.setLevel(logging.INFO)
    #     file_handler.setFormatter(logging.Formatter(
    #         '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    #     ))
    #     logging.getLogger().addHandler(file_handler)

    logging.getLogger(__name__).info(
        f"Logging configured with level: {logging.getLevelName(log_level)}"
    )
