# utils/logging_config.py
import logging
import os
import sys

def setup_logging():
    """
    Configures the Python logging system for the application.
    Log level can be controlled via the LOG_LEVEL environment variable.
    Logs will go to both console (stdout) and a file.
    """
    log_level_str = os.environ.get('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Define log file path
    log_dir = "/app/logs" # Inside the Docker container
    log_file = os.path.join(log_dir, "scraper.log")

    # --- Handlers ---
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level) # Console logs can be INFO by default
    console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(console_formatter)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG) # File logs can be more verbose (DEBUG)
    file_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(pathname)s:%(lineno)d - %(message)s') # Added path and line number
    file_handler.setFormatter(file_formatter)

    # --- Root Logger Configuration ---
    # Get the root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG) # Set root logger to DEBUG to allow all messages to pass through to handlers

    # Clear existing handlers to prevent duplicate logs if setup_logging is called multiple times
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    logger = logging.getLogger(__name__) # Get a specific logger for this module to log the setup message
    logger.info(f"Logging configured. Console level: {logging.getLevelName(console_handler.level)}, File level: {logging.getLevelName(file_handler.level)}. Log file: {log_file}")