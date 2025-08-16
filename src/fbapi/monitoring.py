"""
File monitoring implementations for fbapi.

This module provides both event-driven and polling-based monitoring
for command and response files.
"""

import os
import time
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Callable, Optional
from threading import Event, Thread

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileCreatedEvent
    WATCHDOG_AVAILABLE = True
except ImportError:
    WATCHDOG_AVAILABLE = False

from .exceptions import ConfigurationError, FileSystemError
from .security import SecurityValidator

logger = logging.getLogger(__name__)


class FileMonitor(ABC):
    """Abstract base class for file monitoring implementations."""
    
    def __init__(self, directory: str, callback: Callable[[str], None], 
                 security_validator: Optional[SecurityValidator] = None):
        self.directory = Path(directory)
        self.callback = callback
        self.security_validator = security_validator or SecurityValidator()
        self._stop_event = Event()
        self._monitor_thread: Optional[Thread] = None
        
        if not self.directory.exists():
            raise FileSystemError(f"Directory does not exist: {directory}")
            
        if not self.directory.is_dir():
            raise FileSystemError(f"Path is not a directory: {directory}")
    
    @abstractmethod
    def start(self) -> None:
        """Start monitoring for file changes."""
        pass
    
    @abstractmethod
    def stop(self) -> None:
        """Stop monitoring for file changes.""" 
        pass
    
    def is_running(self) -> bool:
        """Check if monitoring is currently active."""
        return self._monitor_thread is not None and self._monitor_thread.is_alive()


class EventDrivenMonitor(FileMonitor):
    """Event-driven file monitoring using watchdog library."""
    
    def __init__(self, directory: str, callback: Callable[[str], None],
                 security_validator: Optional[SecurityValidator] = None):
        if not WATCHDOG_AVAILABLE:
            raise ConfigurationError(
                "watchdog library is required for event-driven monitoring. "
                "Install with: pip install watchdog"
            )
        
        super().__init__(directory, callback, security_validator)
        self._observer: Optional[Observer] = None
        self._event_handler = _WatchdogEventHandler(self.callback, self.security_validator)
    
    def start(self) -> None:
        """Start event-driven monitoring."""
        if self.is_running():
            logger.warning("Monitor is already running")
            return
            
        self._observer = Observer()
        self._observer.schedule(
            self._event_handler, 
            str(self.directory), 
            recursive=False
        )
        self._observer.start()
        logger.info(f"Started event-driven monitoring on {self.directory}")
    
    def stop(self) -> None:
        """Stop event-driven monitoring."""
        if self._observer and self._observer.is_alive():
            self._observer.stop()
            self._observer.join(timeout=5.0)
            self._observer = None
            logger.info(f"Stopped event-driven monitoring on {self.directory}")


class PollingMonitor(FileMonitor):
    """Polling-based file monitoring as fallback option."""
    
    def __init__(self, directory: str, callback: Callable[[str], None],
                 polling_interval: float = 1.0,
                 security_validator: Optional[SecurityValidator] = None):
        super().__init__(directory, callback, security_validator)
        self.polling_interval = polling_interval
        self._processed_files = set()
    
    def start(self) -> None:
        """Start polling-based monitoring."""
        if self.is_running():
            logger.warning("Monitor is already running")
            return
            
        self._stop_event.clear()
        self._monitor_thread = Thread(target=self._polling_loop, daemon=True)
        self._monitor_thread.start()
        logger.info(f"Started polling monitoring on {self.directory} "
                   f"(interval: {self.polling_interval}s)")
    
    def stop(self) -> None:
        """Stop polling-based monitoring."""
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._stop_event.set()
            self._monitor_thread.join(timeout=5.0)
            self._monitor_thread = None
            logger.info(f"Stopped polling monitoring on {self.directory}")
    
    def _polling_loop(self) -> None:
        """Main polling loop."""
        while not self._stop_event.is_set():
            try:
                self._scan_directory()
            except Exception as e:
                logger.error(f"Error during directory scan: {e}")
            
            self._stop_event.wait(self.polling_interval)
    
    def _scan_directory(self) -> None:
        """Scan directory for new files."""
        try:
            for file_path in self.directory.iterdir():
                if file_path.is_file() and file_path.suffix == '.json':
                    file_str = str(file_path)
                    if file_str not in self._processed_files:
                        if self.security_validator.validate_file_path(file_str):
                            self._processed_files.add(file_str)
                            self.callback(file_str)
                        else:
                            logger.warning(f"Security validation failed for: {file_str}")
        except OSError as e:
            logger.error(f"Error scanning directory {self.directory}: {e}")


class _WatchdogEventHandler(FileSystemEventHandler):
    """Internal event handler for watchdog events."""
    
    def __init__(self, callback: Callable[[str], None], 
                 security_validator: SecurityValidator):
        self.callback = callback
        self.security_validator = security_validator
    
    def on_created(self, event):
        """Handle file creation events."""
        if isinstance(event, FileCreatedEvent) and event.src_path.endswith('.json'):
            if self.security_validator.validate_file_path(event.src_path):
                # Small delay to ensure file is fully written
                time.sleep(0.1)
                self.callback(event.src_path)
            else:
                logger.warning(f"Security validation failed for: {event.src_path}")


def create_monitor(directory: str, callback: Callable[[str], None],
                   monitoring_strategy: str = "auto",
                   polling_interval: float = 1.0,
                   security_validator: Optional[SecurityValidator] = None) -> FileMonitor:
    """
    Factory function to create appropriate monitor based on strategy.
    
    Args:
        directory: Directory to monitor
        callback: Function to call when files are detected
        monitoring_strategy: "auto", "event", or "polling"
        polling_interval: Interval for polling strategy
        security_validator: Security validator instance
        
    Returns:
        FileMonitor instance
        
    Raises:
        ConfigurationError: If strategy is invalid or requirements not met
    """
    if monitoring_strategy == "auto":
        monitoring_strategy = "event" if WATCHDOG_AVAILABLE else "polling"
    
    if monitoring_strategy == "event":
        if not WATCHDOG_AVAILABLE:
            raise ConfigurationError(
                "Event-driven monitoring requires watchdog library. "
                "Use 'polling' strategy or install watchdog."
            )
        return EventDrivenMonitor(directory, callback, security_validator)
    
    elif monitoring_strategy == "polling":
        return PollingMonitor(directory, callback, polling_interval, security_validator)
    
    else:
        raise ConfigurationError(
            f"Invalid monitoring strategy: {monitoring_strategy}. "
            "Use 'auto', 'event', or 'polling'."
        )