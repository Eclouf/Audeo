"""
Centralized logging system for Audeo application
"""

from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime


class AudeoLogger:
    """Centralized logger with filtering and rotation capabilities"""
    
    def __init__(self, name: str = "audeo", log_dir: Optional[Path] = None):
        self._logger = logging.getLogger(name)
        self._logger.setLevel(logging.DEBUG)
        
        # Clear existing handlers to avoid duplicates
        self._logger.handlers.clear()
        
        # Setup console handler
        self._setup_console_handler()
        
        # Setup file handler if log_dir is provided
        if log_dir:
            self._setup_file_handler(log_dir)
    
    def _setup_console_handler(self) -> None:
        """Setup console handler with appropriate formatting"""
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self._logger.addHandler(console_handler)
    
    def _setup_file_handler(self, log_dir: Path) -> None:
        """Setup rotating file handler for persistent logging"""
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "audeo.log"
        
        # Rotating file handler (10MB max, keep 5 files)
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        self._logger.addHandler(file_handler)
    
    def get_logger(self) -> logging.Logger:
        """Get the configured logger instance"""
        return self._logger


class YdlLogHandler(logging.Handler):
    """Specialized handler for yt-dlp logging with intelligent filtering"""
    
    # Patterns to skip (too verbose or not useful)
    SKIP_PATTERNS = [
        '[debug] frame=',
        '[debug] request',
        '[debug] downloaded ',
        '[debug] writing ',
        '[debug] file:',
        '[debug] destination:',
        '[debug] original:',
    ]
    
    # Patterns that are important and should always be shown
    IMPORTANT_PATTERNS = [
        'error',
        'warning',
        'failed',
        'success',
        'complete',
        'downloaded',
        'extracting',
        'processing',
    ]
    
    def __init__(self, downloads_view):
        super().__init__()
        self.downloads_view = downloads_view
        self.setLevel(logging.DEBUG)
    
    def emit(self, record: logging.LogRecord) -> None:
        """Handle yt-dlp log records with intelligent filtering"""
        try:
            if not self.downloads_view:
                return
            
            message = record.getMessage()
            message_lower = message.lower()
            
            # Skip overly verbose debug messages
            if any(skip in message_lower for skip in self.SKIP_PATTERNS):
                return
            
            # Determine importance and route accordingly
            if any(important in message_lower for important in self.IMPORTANT_PATTERNS):
                # Important messages go to info log
                self.downloads_view.log_info(f"yt-dlp: {message.strip()}")
            elif record.levelno >= logging.WARNING:
                # Warnings and errors always shown
                self.downloads_view.log_info(f"yt-dlp: {message.strip()}")
            else:
                # Other debug messages go to debug log
                self.downloads_view.log_debug(f"yt-dlp: {message.strip()}")
                
        except Exception as e:
            # Fallback to prevent logging errors from breaking the application
            print(f"Error in YdlLogHandler.emit: {e}")
    
    def setLevel(self, level: int) -> None:
        """Set the logging level for this handler"""
        super().setLevel(level)


def setup_ydl_logger(downloads_view, level: int = logging.DEBUG) -> tuple[logging.Logger, YdlLogHandler]:
    """Setup and configure yt-dlp logger with specialized handler
    
    Args:
        downloads_view: The downloads view for UI logging
        level: Logging level (default: DEBUG)
        
    Returns:
        Tuple of (logger_instance, handler_instance)
    """
    logger = logging.getLogger("yt_dlp")
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create and add specialized handler
    handler = YdlLogHandler(downloads_view)
    handler.setLevel(level)
    logger.addHandler(handler)
    
    # Prevent propagation to avoid duplicate messages
    logger.propagate = False
    
    return logger, handler


def get_logger(name: str = "audeo", log_dir: Optional[Path] = None) -> logging.Logger:
    """Get a configured logger instance
    
    Args:
        name: Logger name (default: "audeo")
        log_dir: Directory for log files (optional)
        
    Returns:
        Configured logger instance
    """
    audeo_logger = AudeoLogger(name, log_dir)
    return audeo_logger.get_logger()
