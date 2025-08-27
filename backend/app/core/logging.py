"""
Logging configuration
"""

import logging
import sys
from typing import Any

def setup_logging(level: str = "INFO") -> None:
    """Setup application logging configuration"""
    
    # Configure root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific logger levels
    logging.getLogger("uvicorn.access").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    
    # Application loggers
    logging.getLogger("app").setLevel(logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("✅ Logging configured successfully")