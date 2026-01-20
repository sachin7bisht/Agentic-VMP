# ==========================================
# File: config/logging_config.py
# ==========================================
import os
import logging
from datetime import datetime
import structlog

class CustomLogger:
    """
    Centralized logger configuration using structlog and standard logging.
    Source: Provided logging.py (User Upload)
    """
    def __init__(self, log_dir="logs"):
        # Resolve log directory relative to the current working directory
        self.logs_dir = os.path.join(os.getcwd(), log_dir)
        os.makedirs(self.logs_dir, exist_ok=True)
        
        # Create timestamped log file name
        log_file = f"{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log"
        self.log_file_path = os.path.join(self.logs_dir, log_file)

    def get_logger(self, name=__file__):
        logger_name = os.path.basename(name)

        # File Handler: Standard text logging
        file_handler = logging.FileHandler(self.log_file_path)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter("%(message)s"))

        # Console Handler: Standard text logging
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(logging.Formatter("%(message)s"))

        # Basic Config for standard logging
        # We reset handlers to avoid duplication if called multiple times
        logging.basicConfig(
            level=logging.INFO,
            format="%(message)s",
            handlers=[console_handler, file_handler],
            force=True 
        )

        # Structlog Configuration
        structlog.configure(
            processors=[
                structlog.processors.TimeStamper(fmt="iso", utc=True, key="timestamp"),
                structlog.processors.add_log_level,
                structlog.processors.EventRenamer(to="event"),
                structlog.processors.JSONRenderer()
            ],
            logger_factory=structlog.stdlib.LoggerFactory(),
            wrapper_class=structlog.stdlib.BoundLogger,
            cache_logger_on_first_use=True,
        )

        return structlog.get_logger(logger_name)

# Create a global instance for easy import across the application
# Usage: from config.logging_config import GLOBAL_LOGGER as logger
GLOBAL_LOGGER = CustomLogger().get_logger()