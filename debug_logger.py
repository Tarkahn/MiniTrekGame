"""
Debug logging system for MiniTrekGame
Captures all debug output to a file for troubleshooting
"""

import logging
import os
from datetime import datetime

# Create debug log file
log_filename = f"debug_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
log_path = os.path.join(os.path.dirname(__file__), log_filename)

# Configure logging to write to file
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_path, mode='w'),
        logging.StreamHandler()  # Also print to console if available
    ]
)

# Create a specific logger for our debug output
debug_logger = logging.getLogger('MINITREK_DEBUG')

def log_debug(message):
    """Log a debug message to both file and console"""
    debug_logger.info(message)
    print(f"[DEBUG] {message}")  # Also print for immediate visibility

def get_log_path():
    """Get the current log file path"""
    return log_path

# Log initialization
log_debug(f"Debug logging initialized. Log file: {log_filename}")
log_debug("=" * 80)