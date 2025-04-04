import logging
import sys
from typing import Optional

# Configure root logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

def get_logger(name: str, level: Optional[int] = None) -> logging.Logger:
    """Get a logger with the specified name and level.
    
    Args:
        name: The logger name, usually __name__
        level: The logging level, defaults to INFO if not specified
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    if level is not None:
        logger.setLevel(level)
    
    return logger
