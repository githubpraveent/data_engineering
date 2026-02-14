"""
Logging configuration
"""
import logging
import sys
import colorlog


def setup_logging(level: str = "INFO", format_string: str = None):
    """Setup colored logging"""
    if format_string is None:
        format_string = (
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(blue)s%(name)s%(reset)s: %(message)s"
        )
    
    handler = colorlog.StreamHandler(sys.stdout)
    handler.setFormatter(colorlog.ColoredFormatter(format_string))
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, level.upper()))
    
    return logger

