Examples
========

This section provides practical examples of using the fbapi library in different scenarios.

Basic Examples
--------------

Simple Echo Server
~~~~~~~~~~~~~~~~~

A basic server that echoes back received messages:

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem
    import time
    
    def echo_handler(command_data):
        """Echo back the received message with timestamp"""
        message = command_data.get('params', [{}])[0].get('value', 'No message')
        
        return {
            'name': 'echo_response',
            'type': 'string',
            'value': f"Echo: {message} (received at {time.ctime()})"
        }
    
    # Create event system and register handler
    event_system = EventSystem()
    event_system.on('echo', echo_handler)
    
    # Start server
    server = FileBasedAPIServer(
        command_dir="./commands",
        response_dir="./responses",
        event_system=event_system
    )
    
    print("Echo server starting...")
    server.start()

Simple Client
~~~~~~~~~~~~

A client that sends messages to the echo server:

.. code-block:: python

    from fbapi import FileBasedAPIClient
    import time
    
    def response_handler(response_data):
        """Handle server response"""
        if response_data['status'] == 'success':
            result = response_data['response'][0]['value']
            print(f"Server response: {result}")
        else:
            print(f"Error: {response_data.get('error', {}).get('message', 'Unknown error')}")
    
    # Create client
    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses"
    )
    
    # Send messages
    messages = ["Hello", "World", "How are you?"]
    
    for message in messages:
        print(f"Sending: {message}")
        client.call_command('echo', response_handler, value=message)
        time.sleep(1)  # Wait between messages
    
    # Wait for all responses
    client.wait_for_completion(timeout=10.0)
    client.cleanup()

Advanced Examples
----------------

Calculator Service
~~~~~~~~~~~~~~~~~

A more complex server implementing calculator operations:

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem
    import operator
    
    class CalculatorService:
        def __init__(self):
            self.operations = {
                'add': operator.add,
                'subtract': operator.sub,
                'multiply': operator.mul,
                'divide': operator.truediv,
                'power': operator.pow
            }
        
        def calculate_handler(self, command_data):
            """Handle calculator operations"""
            try:
                params = command_data.get('params', [])
                
                # Extract parameters
                operation = None
                operands = []
                
                for param in params:
                    if param['name'] == 'operation':
                        operation = param['value']
                    elif param['name'] in ['a', 'b', 'x', 'y']:
                        operands.append(float(param['value']))
                
                if not operation or len(operands) < 2:
                    raise ValueError("Missing operation or operands")
                
                if operation not in self.operations:
                    raise ValueError(f"Unsupported operation: {operation}")
                
                # Perform calculation
                result = self.operations[operation](operands[0], operands[1])
                
                return {
                    'name': 'calculation_result',
                    'type': 'number',
                    'value': result
                }
                
            except ZeroDivisionError:
                raise ValueError("Division by zero")
            except Exception as e:
                raise ValueError(f"Calculation error: {str(e)}")
    
    # Setup server
    calculator = CalculatorService()
    event_system = EventSystem()
    event_system.on('calculate', calculator.calculate_handler)
    
    server = FileBasedAPIServer(
        command_dir="./commands",
        response_dir="./responses",
        event_system=event_system
    )
    
    print("Calculator server starting...")
    server.start()

Calculator Client
~~~~~~~~~~~~~~~~

Client for the calculator service:

.. code-block:: python

    from fbapi import FileBasedAPIClient
    
    class CalculatorClient:
        def __init__(self):
            self.client = FileBasedAPIClient(
                command_dir="./commands",
                response_dir="./responses"
            )
            self.results = {}
        
        def result_handler(self, response_data):
            """Handle calculation results"""
            request_id = response_data.get('request_id')
            
            if response_data['status'] == 'success':
                result = response_data['response'][0]['value']
                self.results[request_id] = result
                print(f"Result: {result}")
            else:
                error_msg = response_data.get('error', {}).get('message', 'Unknown error')
                self.results[request_id] = f"Error: {error_msg}"
                print(f"Calculation failed: {error_msg}")
        
        def calculate(self, operation, a, b):
            """Perform a calculation"""
            request_id = self.client.call_command(
                'calculate',
                self.result_handler,
                operation=operation,
                a=a,
                b=b
            )
            return request_id
        
        def wait_for_result(self, request_id, timeout=5.0):
            """Wait for a specific calculation result"""
            import time
            start_time = time.time()
            
            while request_id not in self.results:
                if time.time() - start_time > timeout:
                    return "Timeout waiting for result"
                time.sleep(0.1)
            
            return self.results[request_id]
        
        def cleanup(self):
            self.client.cleanup()
    
    # Usage example
    if __name__ == "__main__":
        calc = CalculatorClient()
        
        # Perform calculations
        req1 = calc.calculate('add', 10, 5)
        req2 = calc.calculate('multiply', 7, 8)
        req3 = calc.calculate('divide', 20, 4)
        
        # Wait for results
        print(f"10 + 5 = {calc.wait_for_result(req1)}")
        print(f"7 * 8 = {calc.wait_for_result(req2)}")
        print(f"20 / 4 = {calc.wait_for_result(req3)}")
        
        calc.cleanup()

Configuration-Based Example
---------------------------

Using configuration files for flexible deployment:

**config.yaml:**

.. code-block:: yaml

    directories:
      command_dir: "/tmp/fbapi/commands"
      response_dir: "/tmp/fbapi/responses"
    
    client:
      timeout_seconds: 30.0
      monitoring_strategy: "event"
    
    server:
      monitoring_strategy: "event"
    
    security:
      max_file_size: 2097152  # 2MB
      allowed_extensions: [".json"]
    
    logging:
      level: "INFO"

**Configured Server:**

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem
    from fbapi.config import load_config
    import logging
    
    # Load configuration
    config = load_config('config.yaml')
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, config.get('logging.level', 'INFO')),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    def data_processor(command_data):
        """Process data with configuration-based limits"""
        data = command_data.get('params', [{}])[0].get('value', '')
        
        # Use configured file size limit for processing
        max_size = config.get('security.max_file_size', 1048576)
        if len(data.encode('utf-8')) > max_size:
            raise ValueError(f"Data too large (max: {max_size} bytes)")
        
        # Process the data
        processed = data.upper()  # Simple processing example
        
        return {
            'name': 'processed_data',
            'type': 'string',
            'value': processed
        }
    
    # Create server with configuration
    event_system = EventSystem()
    event_system.on('process', data_processor)
    
    server = FileBasedAPIServer(
        command_dir=config.get('directories.command_dir'),
        response_dir=config.get('directories.response_dir'),
        event_system=event_system,
        monitoring_strategy=config.get('server.monitoring_strategy')
    )
    
    server.start()

Error Handling Example
---------------------

Robust error handling patterns:

.. code-block:: python

    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import SecurityError, ValidationError, TimeoutError
    import logging
    
    class RobustClient:
        def __init__(self):
            self.client = FileBasedAPIClient(
                command_dir="./commands",
                response_dir="./responses"
            )
            self.logger = logging.getLogger(__name__)
        
        def safe_call(self, command, handler, max_retries=3, **params):
            """Make a command call with retry logic and error handling"""
            for attempt in range(max_retries):
                try:
                    request_id = self.client.call_command(command, handler, **params)
                    
                    # Wait for response with timeout
                    self.client.wait_for_completion(timeout=10.0)
                    return request_id
                    
                except SecurityError as e:
                    self.logger.error(f"Security error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                    
                except ValidationError as e:
                    self.logger.error(f"Validation error: {e}")
                    # Don't retry validation errors
                    raise
                    
                except TimeoutError as e:
                    self.logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                    
                except Exception as e:
                    self.logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                    if attempt == max_retries - 1:
                        raise
                
                # Wait before retry
                import time
                time.sleep(2 ** attempt)  # Exponential backoff
        
        def error_handler(self, response_data):
            """Handle responses with proper error checking"""
            if response_data['status'] == 'success':
                result = response_data['response'][0]['value']
                self.logger.info(f"Success: {result}")
                return result
            else:
                error_info = response_data.get('error', {})
                error_code = error_info.get('code', 'unknown')
                error_message = error_info.get('message', 'Unknown error')
                
                self.logger.error(f"Server error {error_code}: {error_message}")
                
                # Handle specific error codes
                if error_code == 400:
                    raise ValidationError(error_message)
                elif error_code == 403:
                    raise SecurityError(error_message)
                elif error_code == 500:
                    raise RuntimeError(f"Server error: {error_message}")
                else:
                    raise Exception(f"API error {error_code}: {error_message}")

Performance Testing Example
--------------------------

Benchmarking your setup:

.. code-block:: python

    import time
    import statistics
    import threading
    from fbapi import FileBasedAPIClient, FileBasedAPIServer, EventSystem
    
    class PerformanceTester:
        def __init__(self):
            self.response_times = []
            self.errors = []
            self.lock = threading.Lock()
        
        def setup_test_server(self):
            """Setup a simple test server"""
            def test_handler(command_data):
                return {
                    'name': 'test_response',
                    'type': 'string',
                    'value': 'OK'
                }
            
            event_system = EventSystem()
            event_system.on('test', test_handler)
            
            server = FileBasedAPIServer(
                command_dir="./test_commands",
                response_dir="./test_responses",
                event_system=event_system
            )
            
            # Start server in background thread
            def start_server():
                server.start()
            
            thread = threading.Thread(target=start_server, daemon=True)
            thread.start()
            time.sleep(1)  # Give server time to start
            
            return server
        
        def test_response_handler(self, response_data):
            """Handle test responses"""
            with self.lock:
                if response_data['status'] != 'success':
                    self.errors.append(response_data)
        
        def run_performance_test(self, num_requests=100, concurrent_clients=1):
            """Run performance test"""
            print(f"Starting performance test: {num_requests} requests, {concurrent_clients} clients")
            
            # Setup server
            server = self.setup_test_server()
            
            def client_worker(client_id, requests_per_client):
                """Worker function for each client"""
                client = FileBasedAPIClient(
                    command_dir="./test_commands",
                    response_dir="./test_responses"
                )
                
                client_times = []
                
                for i in range(requests_per_client):
                    start_time = time.time()
                    
                    client.call_command('test', self.test_response_handler, 
                                      client_id=client_id, request_num=i)
                    client.wait_for_completion(timeout=5.0)
                    
                    response_time = time.time() - start_time
                    client_times.append(response_time)
                
                with self.lock:
                    self.response_times.extend(client_times)
                
                client.cleanup()
            
            # Calculate requests per client
            requests_per_client = num_requests // concurrent_clients
            
            # Start client threads
            threads = []
            start_time = time.time()
            
            for client_id in range(concurrent_clients):
                thread = threading.Thread(
                    target=client_worker,
                    args=(client_id, requests_per_client)
                )
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            total_time = time.time() - start_time
            
            # Calculate statistics
            if self.response_times:
                stats = {
                    'total_requests': len(self.response_times),
                    'total_time': total_time,
                    'requests_per_second': len(self.response_times) / total_time,
                    'mean_response_time': statistics.mean(self.response_times),
                    'median_response_time': statistics.median(self.response_times),
                    'min_response_time': min(self.response_times),
                    'max_response_time': max(self.response_times),
                    'errors': len(self.errors)
                }
                
                if len(self.response_times) >= 20:
                    quantiles = statistics.quantiles(self.response_times, n=20)
                    stats['p95_response_time'] = quantiles[18]  # 95th percentile
                
                return stats
            else:
                return {'error': 'No successful requests'}
    
    # Usage
    if __name__ == "__main__":
        tester = PerformanceTester()
        
        # Test different configurations
        configs = [
            (100, 1),   # 100 requests, 1 client
            (100, 5),   # 100 requests, 5 clients
            (100, 10),  # 100 requests, 10 clients
        ]
        
        for requests, clients in configs:
            tester.response_times.clear()
            tester.errors.clear()
            
            stats = tester.run_performance_test(requests, clients)
            
            print(f"\n=== {requests} requests, {clients} clients ===")
            for key, value in stats.items():
                if 'time' in key:
                    print(f"{key}: {value:.3f}s")
                else:
                    print(f"{key}: {value}")

These examples demonstrate various patterns and use cases for the fbapi library. You can use them as starting points for your own applications.