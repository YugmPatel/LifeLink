"""
LifeLink Utility Functions
Provides logging and configuration utilities
"""

import os
import logging
from typing import Any
from dataclasses import dataclass


def get_logger(name: str) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__)
        
    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)
    
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        logger.setLevel(getattr(logging, log_level, logging.INFO))
    
    return logger


@dataclass
class Config:
    """Application configuration"""
    API_PORT: int = int(os.getenv("API_PORT", "8080"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    DEPLOYMENT_MODE: str = os.getenv("DEPLOYMENT_MODE", "local")
    GOOGLE_CLOUD_PROJECT: str = os.getenv("GOOGLE_CLOUD_PROJECT", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
    TWILIO_ACCOUNT_SID: str = os.getenv("TWILIO_ACCOUNT_SID", "")
    TWILIO_AUTH_TOKEN: str = os.getenv("TWILIO_AUTH_TOKEN", "")
    WHATSAPP_ENABLED: bool = os.getenv("WHATSAPP_ENABLED", "false").lower() == "true"


_config = None


def get_config() -> Config:
    """
    Get application configuration singleton.
    
    Returns:
        Config instance
    """
    global _config
    if _config is None:
        _config = Config()
    return _config
