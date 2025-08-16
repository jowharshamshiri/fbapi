Performance
===========

This guide covers performance optimization techniques for the fbapi library.

Monitoring Strategies
--------------------

Event-Driven Monitoring (Recommended)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The event-driven approach provides the best performance:

.. code-block:: python

    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses",
        monitoring_strategy="event"  # Default - best performance
    )

**Advantages:**
- Near real-time response (< 10ms typical)
- Low CPU usage
- Minimal file system overhead

**Limitations:**
- Requires ``watchdog`` library
- May not work reliably on some network file systems
- Platform-dependent behavior

Polling Monitoring
~~~~~~~~~~~~~~~~~

Use polling when event monitoring isn't reliable:

.. code-block:: python

    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses",
        monitoring_strategy="polling",
        polling_interval=0.1  # 100ms polling
    )

**Tuning Polling Interval:**

========== =============== ============== =================
Interval   Response Time   CPU Usage      Use Case
========== =============== ============== =================
0.01s      ~5ms           High           Real-time apps
0.1s       ~50ms          Medium         Interactive apps  
0.5s       ~250ms         Low            Background tasks
1.0s       ~500ms         Very Low       Batch processing
========== =============== ============== =================

Performance Benchmarks
----------------------

Typical performance characteristics:

Response Time Comparison
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    Test Environment: MacBook Pro M1, SSD, Python 3.11
    
    Event-Driven Monitoring:
    - Average response time: 8ms
    - 95th percentile: 15ms
    - 99th percentile: 25ms
    
    Polling (100ms interval):
    - Average response time: 55ms
    - 95th percentile: 95ms
    - 99th percentile: 150ms
    
    Polling (1s interval):
    - Average response time: 520ms
    - 95th percentile: 980ms
    - 99th percentile: 1200ms

Throughput Comparison
~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

    Concurrent Operations (10 clients):
    
    Event-Driven:
    - Requests/second: 800-1200
    - CPU usage: 5-10%
    - Memory usage: ~50MB
    
    Polling (100ms):
    - Requests/second: 180-220
    - CPU usage: 15-25%
    - Memory usage: ~45MB
    
    Polling (1s):
    - Requests/second: 18-22
    - CPU usage: 2-5%
    - Memory usage: ~40MB

Optimization Techniques
----------------------

File System Optimization
~~~~~~~~~~~~~~~~~~~~~~~~

Use local file systems when possible:

.. code-block:: python

    # Good: Local SSD
    client = FileBasedAPIClient(
        command_dir="/tmp/fbapi/commands",
        response_dir="/tmp/fbapi/responses"
    )
    
    # Avoid: Network file systems
    # command_dir="/nfs/shared/commands"  # Slower, less reliable

Directory Structure
~~~~~~~~~~~~~~~~~~

Keep communication directories clean:

.. code-block:: python

    import os
    import time
    import glob
    
    def cleanup_old_files(directory, max_age=300):  # 5 minutes
        """Remove files older than max_age seconds"""
        current_time = time.time()
        pattern = os.path.join(directory, "*.json")
        
        for filepath in glob.glob(pattern):
            if current_time - os.path.getctime(filepath) > max_age:
                try:
                    os.remove(filepath)
                except OSError:
                    pass  # File may have been removed by another process

Memory Management
~~~~~~~~~~~~~~~~

For high-throughput applications:

.. code-block:: python

    # Use context managers to ensure cleanup
    with FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses"
    ) as client:
        # Your operations here
        client.call_command('process', handler, data=large_data)
    # Client automatically cleaned up

Connection Pooling
~~~~~~~~~~~~~~~~~

For multiple clients, consider connection pooling:

.. code-block:: python

    class ClientPool:
        def __init__(self, pool_size=5):
            self.pool = []
            self.pool_size = pool_size
            self._create_pool()
        
        def _create_pool(self):
            for _ in range(self.pool_size):
                client = FileBasedAPIClient(
                    command_dir="./commands",
                    response_dir="./responses"
                )
                self.pool.append(client)
        
        def get_client(self):
            if self.pool:
                return self.pool.pop()
            else:
                # Create new client if pool is empty
                return FileBasedAPIClient(
                    command_dir="./commands",
                    response_dir="./responses"
                )
        
        def return_client(self, client):
            if len(self.pool) < self.pool_size:
                self.pool.append(client)
            else:
                client.cleanup()

Batch Processing
~~~~~~~~~~~~~~~

For bulk operations, use batch processing:

.. code-block:: python

    def process_batch(items, batch_size=10):
        """Process items in batches for better performance"""
        results = []
        
        for i in range(0, len(items), batch_size):
            batch = items[i:i + batch_size]
            
            # Process batch
            batch_results = []
            for item in batch:
                result = client.call_command('process', handler, data=item)
                batch_results.append(result)
            
            results.extend(batch_results)
            
            # Brief pause between batches to prevent overwhelming
            time.sleep(0.01)
        
        return results

Monitoring Performance
---------------------

Built-in Metrics
~~~~~~~~~~~~~~~~

Enable performance monitoring:

.. code-block:: python

    import logging
    
    # Enable performance logging
    perf_logger = logging.getLogger('fbapi.performance')
    perf_logger.setLevel(logging.INFO)
    
    # This will log timing information
    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses",
        enable_metrics=True  # Enable built-in metrics
    )

Custom Metrics
~~~~~~~~~~~~~

Add your own performance monitoring:

.. code-block:: python

    import time
    from contextlib import contextmanager
    
    @contextmanager
    def timer(operation_name):
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            print(f"{operation_name}: {duration:.3f}s")
    
    # Usage
    with timer("API call"):
        client.call_command('test', handler, data=test_data)

System Resource Monitoring
~~~~~~~~~~~~~~~~~~~~~~~~~~

Monitor system resources:

.. code-block:: python

    import psutil
    import os
    
    def monitor_resources():
        process = psutil.Process(os.getpid())
        
        return {
            'cpu_percent': process.cpu_percent(),
            'memory_mb': process.memory_info().rss / 1024 / 1024,
            'open_files': len(process.open_files()),
            'threads': process.num_threads()
        }

Troubleshooting Performance Issues
---------------------------------

Common Issues
~~~~~~~~~~~~

**High CPU Usage**
- Check polling interval (increase if too low)
- Monitor for excessive file system activity
- Ensure proper cleanup of old files

**High Memory Usage**
- Check for memory leaks in event handlers
- Ensure clients are properly closed
- Monitor file descriptor usage

**Slow Response Times**
- Verify file system type (local vs network)
- Check directory permissions
- Monitor disk I/O usage

**File System Errors**
- Ensure directories exist and are writable
- Check available disk space
- Monitor for permission issues

Performance Testing
~~~~~~~~~~~~~~~~~~~

Create performance tests:

.. code-block:: python

    import time
    import statistics
    
    def performance_test(num_requests=100):
        response_times = []
        
        def test_handler(response):
            pass  # No-op handler for testing
        
        client = FileBasedAPIClient(
            command_dir="./commands",
            response_dir="./responses"
        )
        
        for i in range(num_requests):
            start_time = time.time()
            client.call_command('test', test_handler, data={'test': i})
            client.wait_for_completion(timeout=5.0)
            response_time = time.time() - start_time
            response_times.append(response_time)
        
        return {
            'mean': statistics.mean(response_times),
            'median': statistics.median(response_times),
            'p95': statistics.quantiles(response_times, n=20)[18],  # 95th percentile
            'p99': statistics.quantiles(response_times, n=100)[98]  # 99th percentile
        }

This will help you establish performance baselines and detect regressions.