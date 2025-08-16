"""
Unit tests for file monitoring functionality.
"""

import pytest
import time
import threading
from pathlib import Path
from unittest.mock import Mock, patch

from fbapi.monitoring import (
    EventDrivenMonitor, PollingMonitor, create_monitor,
    FileMonitor, WATCHDOG_AVAILABLE
)
from fbapi.security import SecurityValidator
from fbapi.exceptions import ConfigurationError, FileSystemError


class TestFileMonitorBase:
    """Test base FileMonitor functionality."""
    
    def test_abstract_class_cannot_be_instantiated(self):
        """Test that FileMonitor cannot be instantiated directly."""
        with pytest.raises(TypeError):
            FileMonitor("/tmp", lambda x: None)


class TestPollingMonitor:
    """Test polling-based file monitoring."""
    
    def test_init_with_valid_directory(self, temp_dir):
        """Test initialization with valid directory."""
        callback = Mock()
        monitor = PollingMonitor(str(temp_dir), callback)
        
        assert monitor.directory == temp_dir
        assert monitor.callback == callback
        assert monitor.polling_interval == 1.0
        assert not monitor.is_running()
    
    def test_init_with_custom_polling_interval(self, temp_dir):
        """Test initialization with custom polling interval."""
        callback = Mock()
        monitor = PollingMonitor(str(temp_dir), callback, polling_interval=0.5)
        
        assert monitor.polling_interval == 0.5
    
    def test_init_with_nonexistent_directory(self):
        """Test initialization with non-existent directory raises error."""
        callback = Mock()
        with pytest.raises(FileSystemError, match="Directory does not exist"):
            PollingMonitor("/nonexistent", callback)
    
    def test_init_with_file_path(self, temp_dir):
        """Test initialization with file path instead of directory raises error."""
        test_file = temp_dir / "test.txt"
        test_file.touch()
        
        callback = Mock()
        with pytest.raises(FileSystemError, match="Path is not a directory"):
            PollingMonitor(str(test_file), callback)
    
    def test_start_and_stop_monitoring(self, temp_dir):
        """Test starting and stopping monitoring."""
        callback = Mock()
        monitor = PollingMonitor(str(temp_dir), callback, polling_interval=0.1)
        
        # Start monitoring
        monitor.start()
        assert monitor.is_running()
        
        # Give it a moment to start
        time.sleep(0.05)
        
        # Stop monitoring
        monitor.stop()
        time.sleep(0.2)  # Wait for thread to stop
        assert not monitor.is_running()
    
    def test_file_detection(self, temp_dir):
        """Test that new JSON files are detected."""
        callback = Mock()
        security_validator = SecurityValidator(allowed_base_paths=[str(temp_dir)])
        monitor = PollingMonitor(str(temp_dir), callback, 
                                polling_interval=0.1, 
                                security_validator=security_validator)
        
        # Start monitoring
        monitor.start()
        
        # Create a JSON file
        test_file = temp_dir / "test.json"
        test_file.write_text('{"test": "data"}')
        
        # Wait for detection
        time.sleep(0.3)
        
        # Stop monitoring
        monitor.stop()
        
        # Verify callback was called
        assert callback.called
        callback.assert_called_with(str(test_file))
    
    def test_non_json_files_ignored(self, temp_dir):
        """Test that non-JSON files are ignored."""
        callback = Mock()
        monitor = PollingMonitor(str(temp_dir), callback, polling_interval=0.1)
        
        # Start monitoring
        monitor.start()
        
        # Create a non-JSON file
        test_file = temp_dir / "test.txt"
        test_file.write_text('not json')
        
        # Wait
        time.sleep(0.3)
        
        # Stop monitoring
        monitor.stop()
        
        # Verify callback was not called
        assert not callback.called
    
    def test_same_file_processed_once(self, temp_dir):
        """Test that the same file is only processed once."""
        callback = Mock()
        security_validator = SecurityValidator(allowed_base_paths=[str(temp_dir)])
        monitor = PollingMonitor(str(temp_dir), callback, 
                                polling_interval=0.1,
                                security_validator=security_validator)
        
        # Create file before starting monitoring
        test_file = temp_dir / "existing.json"
        test_file.write_text('{"test": "data"}')
        
        # Start monitoring
        monitor.start()
        
        # Wait for multiple polling cycles
        time.sleep(0.5)
        
        # Stop monitoring
        monitor.stop()
        
        # Verify callback was called exactly once
        assert callback.call_count == 1
    
    def test_security_validation_failure(self, temp_dir):
        """Test that files failing security validation are ignored."""
        callback = Mock()
        
        # Create security validator that rejects all files
        security_validator = Mock()
        security_validator.validate_file_path.return_value = False
        
        monitor = PollingMonitor(str(temp_dir), callback, 
                                polling_interval=0.1,
                                security_validator=security_validator)
        
        # Start monitoring
        monitor.start()
        
        # Create a JSON file
        test_file = temp_dir / "test.json"
        test_file.write_text('{"test": "data"}')
        
        # Wait
        time.sleep(0.3)
        
        # Stop monitoring
        monitor.stop()
        
        # Verify callback was not called due to security validation failure
        assert not callback.called
        security_validator.validate_file_path.assert_called()


@pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not available")
class TestEventDrivenMonitor:
    """Test event-driven file monitoring (requires watchdog)."""
    
    def test_init_with_valid_directory(self, temp_dir):
        """Test initialization with valid directory."""
        callback = Mock()
        monitor = EventDrivenMonitor(str(temp_dir), callback)
        
        assert monitor.directory == temp_dir
        assert monitor.callback == callback
        assert not monitor.is_running()
    
    def test_start_and_stop_monitoring(self, temp_dir):
        """Test starting and stopping event-driven monitoring."""
        callback = Mock()
        monitor = EventDrivenMonitor(str(temp_dir), callback)
        
        # Start monitoring
        monitor.start()
        assert monitor.is_running()
        
        # Stop monitoring
        monitor.stop()
        time.sleep(0.1)  # Give time for observer to stop
        assert not monitor.is_running()
    
    def test_file_creation_detection(self, temp_dir):
        """Test that file creation events are detected."""
        callback = Mock()
        security_validator = SecurityValidator(allowed_base_paths=[str(temp_dir)])
        monitor = EventDrivenMonitor(str(temp_dir), callback, security_validator)
        
        # Start monitoring
        monitor.start()
        
        # Small delay to ensure monitoring is active
        time.sleep(0.1)
        
        # Create a JSON file
        test_file = temp_dir / "event_test.json"
        test_file.write_text('{"event": "test"}')
        
        # Wait for event processing
        time.sleep(0.5)
        
        # Stop monitoring
        monitor.stop()
        
        # Verify callback was called
        assert callback.called
        # Check that callback was called with the correct file (accounting for symlinks)
        actual_path = Path(callback.call_args[0][0]).resolve()
        expected_path = test_file.resolve()
        assert actual_path == expected_path


class TestEventDrivenMonitorWithoutWatchdog:
    """Test event-driven monitor when watchdog is not available."""
    
    @patch('fbapi.monitoring.WATCHDOG_AVAILABLE', False)
    def test_init_without_watchdog_raises_error(self, temp_dir):
        """Test that EventDrivenMonitor raises error when watchdog unavailable."""
        callback = Mock()
        
        with pytest.raises(ConfigurationError, match="watchdog library is required"):
            EventDrivenMonitor(str(temp_dir), callback)


class TestMonitorFactory:
    """Test monitor factory function."""
    
    def test_create_monitor_auto_strategy(self, temp_dir):
        """Test create_monitor with auto strategy."""
        callback = Mock()
        monitor = create_monitor(str(temp_dir), callback, monitoring_strategy="auto")
        
        # Should create EventDrivenMonitor if watchdog available, else PollingMonitor
        if WATCHDOG_AVAILABLE:
            assert isinstance(monitor, EventDrivenMonitor)
        else:
            assert isinstance(monitor, PollingMonitor)
    
    def test_create_monitor_polling_strategy(self, temp_dir):
        """Test create_monitor with polling strategy."""
        callback = Mock()
        monitor = create_monitor(str(temp_dir), callback, monitoring_strategy="polling")
        
        assert isinstance(monitor, PollingMonitor)
    
    @pytest.mark.skipif(not WATCHDOG_AVAILABLE, reason="watchdog not available")
    def test_create_monitor_event_strategy(self, temp_dir):
        """Test create_monitor with event strategy."""
        callback = Mock()
        monitor = create_monitor(str(temp_dir), callback, monitoring_strategy="event")
        
        assert isinstance(monitor, EventDrivenMonitor)
    
    @patch('fbapi.monitoring.WATCHDOG_AVAILABLE', False)
    def test_create_monitor_event_strategy_without_watchdog(self, temp_dir):
        """Test create_monitor with event strategy when watchdog unavailable."""
        callback = Mock()
        
        with pytest.raises(ConfigurationError, match="Event-driven monitoring requires watchdog"):
            create_monitor(str(temp_dir), callback, monitoring_strategy="event")
    
    def test_create_monitor_invalid_strategy(self, temp_dir):
        """Test create_monitor with invalid strategy."""
        callback = Mock()
        
        with pytest.raises(ConfigurationError, match="Invalid monitoring strategy"):
            create_monitor(str(temp_dir), callback, monitoring_strategy="invalid")
    
    def test_create_monitor_with_custom_polling_interval(self, temp_dir):
        """Test create_monitor with custom polling interval."""
        callback = Mock()
        monitor = create_monitor(str(temp_dir), callback, 
                               monitoring_strategy="polling", 
                               polling_interval=0.5)
        
        assert isinstance(monitor, PollingMonitor)
        assert monitor.polling_interval == 0.5
    
    def test_create_monitor_with_security_validator(self, temp_dir):
        """Test create_monitor with custom security validator."""
        callback = Mock()
        security_validator = SecurityValidator()
        
        monitor = create_monitor(str(temp_dir), callback, 
                               monitoring_strategy="polling",
                               security_validator=security_validator)
        
        assert monitor.security_validator == security_validator