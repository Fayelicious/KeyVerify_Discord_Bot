import logging
import os
import sys
from logging.handlers import TimedRotatingFileHandler
from datetime import datetime

def setup_logging(log_level_str="INFO"):
    """
    Sets up logging to both a rotating file (for the dashboard) 
    and sys.stdout (for Portainer/Docker logs).
    """
    logging_level = getattr(logging, log_level_str.upper(), logging.INFO)

    # Ensure logs/ folder exists
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)

    # Base log file name
    base_log_file = os.path.join(log_dir, "bot.log")

    # 1. File Handler with daily rotation
    # TimedRotatingFileHandler handles its own deletion via backupCount
    file_handler = TimedRotatingFileHandler(
        base_log_file,
        when="midnight",
        interval=1,
        backupCount=7,
        encoding="utf-8",
        utc=True
    )
    file_handler.suffix = "%Y-%m-%d"
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_formatter)

    # 2. Console Handler (Crucial for Portainer/Docker)
    # We explicitly use sys.stdout to ensure Portainer captures it correctly
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(file_formatter)

    # Set up root logger safely
    logger = logging.getLogger()
    logger.setLevel(logging_level)

    # Clear existing handlers to prevent duplicates (better than checking instances)
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # Optional: Initial cleanup check for very old files not caught by the handler
    delete_old_logs(log_dir, days=7)

def delete_old_logs(log_dir, days=7):
    """Manually cleans up files older than the specified days."""
    now = datetime.now()
    if not os.path.exists(log_dir):
        return
        
    for filename in os.listdir(log_dir):
        file_path = os.path.join(log_dir, filename)
        if os.path.isfile(file_path):
            try:
                # Get file modification time
                file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                if (now - file_time).days > days:
                    os.remove(file_path)
            except Exception as e:
                # Use print here because logger might not be fully ready
                print(f"Could not delete old log file {filename}: {e}")