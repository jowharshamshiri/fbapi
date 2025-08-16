Monitoring API
==============

The monitoring module provides file system monitoring capabilities with both event-driven and polling strategies.

File Monitors
-------------

.. automodule:: fbapi.monitoring
   :members:
   :undoc-members:
   :show-inheritance:

Classes
-------

.. autoclass:: fbapi.monitoring.FileMonitor
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.monitoring.EventDrivenMonitor
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: fbapi.monitoring.PollingMonitor
   :members:
   :undoc-members:
   :show-inheritance:

Functions
---------

.. autofunction:: fbapi.monitoring.create_monitor

Monitoring Examples
-------------------

Basic File Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.monitoring import create_monitor
    import time

    def file_callback(file_path):
        print(f"File detected: {file_path}")
        # Process the file
        with open(file_path, 'r') as f:
            content = f.read()
            print(f"Content: {content}")

    # Create monitor with auto strategy
    monitor = create_monitor(
        directory="./watch_directory",
        callback=file_callback,
        monitoring_strategy="auto"
    )

    try:
        # Start monitoring
        monitor.start()
        print("Monitoring started. Create files in ./watch_directory")
        
        # Keep running
        time.sleep(60)
        
    finally:
        monitor.stop()
        print("Monitoring stopped")

Event-Driven Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.monitoring import EventDrivenMonitor
    from fbapi.security import SecurityValidator
    import os

    # Setup secure monitoring
    security_validator = SecurityValidator(
        allowed_base_paths=["./secure_watch"],
        max_file_size=1024*1024  # 1MB limit
    )

    def secure_callback(file_path):
        print(f"Secure file detected: {file_path}")
        
        # Additional security check
        if security_validator.validate_file_path(file_path):
            print("File passed security validation")
            # Process file safely
        else:
            print("File failed security validation - skipping")

    # Create event-driven monitor
    monitor = EventDrivenMonitor(
        directory="./secure_watch",
        callback=secure_callback,
        security_validator=security_validator
    )

    try:
        os.makedirs("./secure_watch", exist_ok=True)
        monitor.start()
        
        print("Event-driven monitoring active")
        print("Monitor will detect file changes immediately")
        
        # Simulate file creation
        test_file = "./secure_watch/test.json"
        with open(test_file, 'w') as f:
            f.write('{"test": "data"}')
        
        time.sleep(2)  # Give time for event processing
        
    finally:
        monitor.stop()

Polling-Based Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.monitoring import PollingMonitor
    import time

    def polling_callback(file_path):
        print(f"File found via polling: {file_path}")

    # Create polling monitor with custom interval
    monitor = PollingMonitor(
        directory="./poll_directory",
        callback=polling_callback,
        polling_interval=0.5  # Poll every 500ms
    )

    try:
        os.makedirs("./poll_directory", exist_ok=True)
        monitor.start()
        
        print("Polling monitor started (checking every 0.5 seconds)")
        
        # Create test files
        for i in range(3):
            test_file = f"./poll_directory/file_{i}.json"
            with open(test_file, 'w') as f:
                f.write(f'{{"id": {i}, "data": "test"}}')
            
            time.sleep(1)  # Space out file creation
            
    finally:
        monitor.stop()

Advanced Monitoring Patterns
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.monitoring import create_monitor
    from fbapi.security import SecurityValidator
    import threading
    import queue
    import json

    class FileProcessor:
        def __init__(self, watch_directory):
            self.watch_directory = watch_directory
            self.file_queue = queue.Queue()
            self.processing_thread = None
            self.monitor = None
            self.shutdown_event = threading.Event()
            
            # Setup security
            self.security_validator = SecurityValidator(
                allowed_base_paths=[watch_directory],
                max_file_size=2*1024*1024  # 2MB limit
            )
            
        def start(self):
            # Create monitor
            self.monitor = create_monitor(
                directory=self.watch_directory,
                callback=self._queue_file,
                monitoring_strategy="auto",
                security_validator=self.security_validator
            )
            
            # Start processing thread
            self.processing_thread = threading.Thread(
                target=self._process_files,
                daemon=True
            )
            self.processing_thread.start()
            
            # Start monitoring
            self.monitor.start()
            print(f"File processor started for {self.watch_directory}")
            
        def stop(self):
            # Signal shutdown
            self.shutdown_event.set()
            
            # Stop monitor
            if self.monitor:
                self.monitor.stop()
                
            # Wait for processing thread
            if self.processing_thread and self.processing_thread.is_alive():
                self.processing_thread.join(timeout=5)
                
            print("File processor stopped")
            
        def _queue_file(self, file_path):
            """Queue file for processing."""
            try:
                self.file_queue.put(file_path, timeout=1)
                print(f"Queued file: {file_path}")
            except queue.Full:
                print(f"Queue full - dropping file: {file_path}")
                
        def _process_files(self):
            """Process files from queue."""
            while not self.shutdown_event.is_set():
                try:
                    # Get file from queue with timeout
                    file_path = self.file_queue.get(timeout=1)
                    
                    # Process the file
                    self._process_single_file(file_path)
                    
                    # Mark task as done
                    self.file_queue.task_done()
                    
                except queue.Empty:
                    continue  # Check shutdown event
                except Exception as e:
                    print(f"Error processing file: {e}")
                    
        def _process_single_file(self, file_path):
            """Process a single file."""
            try:
                print(f"Processing: {file_path}")
                
                # Read and validate file
                with open(file_path, 'r') as f:
                    content = f.read()
                    
                # Validate JSON content
                if self.security_validator.validate_json_content(content):
                    data = json.loads(content)
                    
                    # Your processing logic here
                    result = self._business_logic(data)
                    
                    # Write result file
                    result_path = file_path.replace('.json', '_result.json')
                    with open(result_path, 'w') as f:
                        json.dump(result, f, indent=2)
                        
                    print(f"Processed: {file_path} -> {result_path}")
                    
                else:
                    print(f"File failed content validation: {file_path}")
                    
            except Exception as e:
                print(f"Error processing {file_path}: {e}")
                
        def _business_logic(self, data):
            """Your business logic here."""
            return {
                'processed': True,
                'original_data': data,
                'processed_at': time.time()
            }

    # Usage
    processor = FileProcessor("./processing_directory")
    
    try:
        processor.start()
        
        # Simulate file creation
        import os
        os.makedirs("./processing_directory", exist_ok=True)
        
        for i in range(5):
            test_file = f"./processing_directory/task_{i}.json"
            with open(test_file, 'w') as f:
                json.dump({"task_id": i, "data": f"task_data_{i}"}, f)
            
            time.sleep(1)
            
        # Let processing complete
        time.sleep(5)
        
    finally:
        processor.stop()

Performance Monitoring
~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.monitoring import create_monitor
    import time
    import threading
    from collections import defaultdict

    class PerformanceMonitor:
        def __init__(self):
            self.stats = defaultdict(int)
            self.start_time = time.time()
            self.lock = threading.Lock()
            
        def file_callback(self, file_path):
            start = time.time()
            
            try:
                # Process file
                with open(file_path, 'r') as f:
                    content = f.read()
                
                processing_time = time.time() - start
                
                with self.lock:
                    self.stats['files_processed'] += 1
                    self.stats['total_processing_time'] += processing_time
                    self.stats['bytes_processed'] += len(content)
                
                # Log performance
                if self.stats['files_processed'] % 10 == 0:
                    self.print_stats()
                    
            except Exception as e:
                with self.lock:
                    self.stats['errors'] += 1
                print(f"Error processing {file_path}: {e}")
                
        def print_stats(self):
            with self.lock:
                elapsed = time.time() - self.start_time
                files = self.stats['files_processed']
                avg_time = self.stats['total_processing_time'] / max(files, 1)
                
                print(f"Performance Stats:")
                print(f"  Files processed: {files}")
                print(f"  Errors: {self.stats['errors']}")
                print(f"  Elapsed time: {elapsed:.2f}s")
                print(f"  Files per second: {files/elapsed:.2f}")
                print(f"  Average processing time: {avg_time*1000:.2f}ms")
                print(f"  Bytes processed: {self.stats['bytes_processed']}")

    # Usage
    perf_monitor = PerformanceMonitor()
    
    monitor = create_monitor(
        directory="./performance_test",
        callback=perf_monitor.file_callback,
        monitoring_strategy="event"
    )

    try:
        os.makedirs("./performance_test", exist_ok=True)
        monitor.start()
        
        # Generate test files for performance testing
        for i in range(50):
            test_file = f"./performance_test/perf_test_{i}.json"
            with open(test_file, 'w') as f:
                # Create file with varying sizes
                data = {"id": i, "data": "x" * (i * 100)}
                json.dump(data, f)
            
            # Small delay to avoid overwhelming the system
            time.sleep(0.01)
            
        # Wait for processing to complete
        time.sleep(5)
        perf_monitor.print_stats()
        
    finally:
        monitor.stop()

Error Handling and Recovery
~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

    from fbapi.monitoring import create_monitor
    from fbapi.exceptions import FileSystemError
    import os
    import time
    import logging

    # Setup logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    class RobustFileMonitor:
        def __init__(self, watch_directory):
            self.watch_directory = watch_directory
            self.monitor = None
            self.restart_count = 0
            self.max_restarts = 5
            
        def start(self):
            try:
                self.monitor = create_monitor(
                    directory=self.watch_directory,
                    callback=self._safe_callback,
                    monitoring_strategy="auto"
                )
                self.monitor.start()
                logger.info(f"Monitor started for {self.watch_directory}")
                
            except Exception as e:
                logger.error(f"Failed to start monitor: {e}")
                self._attempt_restart()
                
        def stop(self):
            if self.monitor:
                self.monitor.stop()
                logger.info("Monitor stopped")
                
        def _safe_callback(self, file_path):
            """Callback with comprehensive error handling."""
            try:
                # Validate file exists and is accessible
                if not os.path.exists(file_path):
                    logger.warning(f"File no longer exists: {file_path}")
                    return
                    
                if not os.access(file_path, os.R_OK):
                    logger.warning(f"File not readable: {file_path}")
                    return
                
                # Process file
                self._process_file(file_path)
                
            except PermissionError as e:
                logger.error(f"Permission denied: {file_path} - {e}")
            except FileNotFoundError as e:
                logger.warning(f"File disappeared during processing: {file_path}")
            except Exception as e:
                logger.error(f"Unexpected error processing {file_path}: {e}")
                
        def _process_file(self, file_path):
            """Process file with retry logic."""
            max_retries = 3
            retry_delay = 0.1
            
            for attempt in range(max_retries):
                try:
                    with open(file_path, 'r') as f:
                        content = f.read()
                    
                    # Your processing logic here
                    logger.info(f"Successfully processed: {file_path}")
                    return
                    
                except (OSError, IOError) as e:
                    if attempt < max_retries - 1:
                        logger.warning(f"Retry {attempt + 1} for {file_path}: {e}")
                        time.sleep(retry_delay)
                        retry_delay *= 2  # Exponential backoff
                    else:
                        logger.error(f"Failed to process {file_path} after {max_retries} attempts")
                        
        def _attempt_restart(self):
            """Attempt to restart monitor after failure."""
            if self.restart_count < self.max_restarts:
                self.restart_count += 1
                logger.info(f"Attempting restart {self.restart_count}/{self.max_restarts}")
                
                # Wait before restart
                time.sleep(2 ** self.restart_count)  # Exponential backoff
                
                try:
                    self.start()
                except Exception as e:
                    logger.error(f"Restart attempt {self.restart_count} failed: {e}")
                    self._attempt_restart()
            else:
                logger.error(f"Max restarts ({self.max_restarts}) exceeded - giving up")

    # Usage
    robust_monitor = RobustFileMonitor("./robust_watch")
    
    try:
        os.makedirs("./robust_watch", exist_ok=True)
        robust_monitor.start()
        
        # Simulate various conditions
        time.sleep(30)
        
    finally:
        robust_monitor.stop()