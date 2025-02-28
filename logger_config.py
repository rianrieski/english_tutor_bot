import logging
import os
from datetime import datetime

def setup_logger(name, log_file=None):
    """Configure logger with standard format"""
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # Set format
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Set level
    logger.setLevel(logging.INFO)
    
    # Add console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Add file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(f'logs/{log_file}')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Add error handler that logs to a separate error file
    error_handler = logging.FileHandler('logs/error.log')
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s\nStack trace:\n%(exc_info)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    ))
    logger.addHandler(error_handler)
    
    return logger

def log_error(logger, error_msg, exc_info=None):
    """Utility function to log errors with stack trace"""
    logger.error(error_msg, exc_info=exc_info if exc_info else True) 