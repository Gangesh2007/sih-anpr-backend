# app/core/logging.py
import logging
import sys

def setup_logging():
    logger = logging.getLogger("anpr_system")
    logger.setLevel(logging.INFO)
    
    # Avoid duplicate logs if setup is called multiple times
    if not logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(module)s:%(lineno)d | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )
        
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
    return logger

logger = setup_logging()