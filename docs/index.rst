fbapi Documentation
==================

.. image:: https://img.shields.io/pypi/v/fbapi.svg
    :target: https://pypi.org/project/fbapi/
    :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/fbapi.svg
    :target: https://pypi.org/project/fbapi/
    :alt: Python versions

.. image:: https://img.shields.io/github/license/jowharshamshiri/fbapi.svg
    :target: https://github.com/jowharshamshiri/fbapi/blob/main/LICENSE
    :alt: License

A Python library for file-based API communication between processes using the filesystem as a communication medium.

Features
--------

* **Event-Driven Architecture**: Real-time file monitoring with automatic fallback to polling
* **Security First**: Path traversal protection, file validation, and content scanning
* **Flexible Configuration**: YAML/JSON config files with environment variable overrides
* **Developer Tools**: CLI for testing, monitoring, and validation
* **Modern Python**: Type hints, async support, and modern packaging standards

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

Table of Contents
-----------------

.. toctree::
   :maxdepth: 2
   :caption: User Guide

   installation
   quickstart
   configuration
   security
   performance
   examples

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/client
   api/server
   api/config
   api/security
   api/monitoring
   api/exceptions
   api/schemas
   api/cli

.. toctree::
   :maxdepth: 1
   :caption: Development

   contributing
   roadmap
   changelog

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`