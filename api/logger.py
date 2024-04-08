import logging
import os
from core.config import Settings
env = Settings()

# setting up the logger
def setup_logger(log_file, logger_name = "", log_level=logging.INFO):
    # Create a logger object
    logger = logging.getLogger(logger_name)
    logger.setLevel(log_level)

    # Create a file handler for writing logs to a file
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(log_level)

    # Create a console handler for printing logs to the console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Define the log format
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger

# path to the logger file
os.makedirs(env.LOG_DIR, exist_ok=True)
logger_path = os.path.join(env.LOG_DIR, "main.log")
logger_main = setup_logger(logger_path, logger_name="logger_main")