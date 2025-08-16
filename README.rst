fbapi - File-Based API Communication Library
============================================

.. image:: https://img.shields.io/pypi/v/fbapi.svg
    :target: https://pypi.org/project/fbapi/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/fbapi.svg
    :target: https://pypi.org/project/fbapi/
    :alt: Python versions

.. image:: https://readthedocs.org/projects/fbapi/badge/?version=latest
    :target: https://fbapi.readthedocs.io/en/latest/?badge=latest
    :alt: Documentation Status

A Python library for file-based API communication between processes using the filesystem as a communication medium.

Features
--------

* **Event-Driven Architecture**: Real-time file monitoring with automatic fallback to polling
* **Security First**: Path traversal protection, file validation, and content scanning  
* **Flexible Configuration**: YAML/JSON config files with environment variable overrides
* **Developer Tools**: CLI for testing, monitoring, and validation
* **Modern Python**: Type hints, comprehensive testing, and modern packaging standards

Quick Start
-----------

Installation
~~~~~~~~~~~~

.. code-block:: bash

    pip install fbapi

Basic Usage
~~~~~~~~~~~

**Server Setup**

.. code-block:: python

    from fbapi import FileBasedAPIServer, EventSystem

    # Create event system and register handlers
    event_system = EventSystem()

    def hello_handler(command_data):
        name = command_data.get('params', [{}])[0].get('value', 'World')
        return {
            'name': 'greeting',
            'type': 'string',
            'value': f'Hello, {name}!'
        }

    event_system.on('hello', hello_handler)

    # Start server
    server = FileBasedAPIServer(
        command_dir="./commands",
        response_dir="./responses",
        event_system=event_system
    )
    server.start()

**Client Usage**

.. code-block:: python

    from fbapi import FileBasedAPIClient

    # Create client
    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./responses"
    )

    # Send command
    def handle_response(response):
        print(f"Response: {response}")

    client.call_command('hello', handle_response, name='Alice')
    client.wait_for_completion()

Documentation
-------------

Full documentation is available at `fbapi.readthedocs.io <https://fbapi.readthedocs.io/>`_.

* `Installation Guide <https://fbapi.readthedocs.io/en/latest/installation.html>`_
* `Quick Start Tutorial <https://fbapi.readthedocs.io/en/latest/quickstart.html>`_
* `API Reference <https://fbapi.readthedocs.io/en/latest/api/client.html>`_
* `Configuration Guide <https://fbapi.readthedocs.io/en/latest/configuration.html>`_
* `Security Guide <https://fbapi.readthedocs.io/en/latest/security.html>`_

Development
-----------

.. code-block:: bash

    # Install development dependencies
    pip install -e .[dev]

    # Run tests
    pytest

    # Run code quality checks
    black src/ tests/
    flake8 src/ tests/
    mypy src/

Contributing
------------

Contributions are welcome! Please see our `Contributing Guide <https://fbapi.readthedocs.io/en/latest/contributing.html>`_ for details.

License
-------

This project is licensed under the MIT License - see the `LICENSE <LICENSE>`_ file for details.

Support
-------

* Documentation: https://fbapi.readthedocs.io/
* Issues: https://github.com/your-username/fbapi/issues
* PyPI: https://pypi.org/project/fbapi/