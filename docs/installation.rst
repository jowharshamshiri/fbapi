Installation
============

This guide covers installing fbapi and its dependencies.

Requirements
------------

- Python 3.8 or higher
- pip package manager

Optional Dependencies
~~~~~~~~~~~~~~~~~~~~

- **watchdog**: For event-driven file monitoring (recommended)
- **PyYAML**: For YAML configuration file support

Quick Install
-------------

Install from PyPI (recommended):

.. code-block:: bash

    pip install fbapi

Install with all optional dependencies:

.. code-block:: bash

    pip install fbapi[dev]

Development Install
-------------------

Install from source for development:

.. code-block:: bash

    git clone https://github.com/jowharshamshiri/fbapi.git
    cd fbapi
    pip install -e .[dev]

Verify Installation
-------------------

Check that fbapi is installed correctly:

.. code-block:: bash

    fbapi version

You should see output like:

.. code-block:: text

    fbapi version 0.1.5044

Platform Support
----------------

fbapi is tested on:

- **Linux**: Ubuntu 20.04+, CentOS 7+, Debian 10+
- **macOS**: 10.15+ (Catalina and later)
- **Windows**: Windows 10, Windows Server 2019+

Dependencies
------------

Core Dependencies
~~~~~~~~~~~~~~~~~

- **jsonschema** (>=4.0.0): JSON schema validation
- **watchdog** (>=2.0.0): Event-driven file monitoring
- **PyYAML** (>=6.0): YAML configuration support

Development Dependencies
~~~~~~~~~~~~~~~~~~~~~~~~

- **pytest** (>=7.0.0): Testing framework
- **pytest-cov** (>=4.0.0): Coverage reporting
- **black** (>=22.0.0): Code formatting
- **isort** (>=5.0.0): Import sorting
- **mypy** (>=1.0.0): Type checking

Troubleshooting
---------------

Common Issues
~~~~~~~~~~~~~

**ImportError: No module named 'watchdog'**

The watchdog library is required for event-driven monitoring:

.. code-block:: bash

    pip install watchdog

**ImportError: No module named 'yaml'**

PyYAML is required for YAML configuration files:

.. code-block:: bash

    pip install PyYAML

**Permission denied errors**

On Unix systems, you may need to use sudo or install in a virtual environment:

.. code-block:: bash

    # Using virtual environment (recommended)
    python -m venv fbapi-env
    source fbapi-env/bin/activate  # On Windows: fbapi-env\Scripts\activate
    pip install fbapi

    # Or using user installation
    pip install --user fbapi

**Windows path issues**

On Windows, ensure paths use forward slashes or double backslashes:

.. code-block:: python

    # Good
    client = FileBasedAPIClient("./commands", "./responses")
    client = FileBasedAPIClient("C:/app/commands", "C:/app/responses")
    client = FileBasedAPIClient("C:\\app\\commands", "C:\\app\\responses")

    # Bad
    client = FileBasedAPIClient("C:\app\commands", "C:\app\responses")

Virtual Environment Setup
--------------------------

Using venv (Python 3.3+):

.. code-block:: bash

    python -m venv fbapi-env
    source fbapi-env/bin/activate  # On Windows: fbapi-env\Scripts\activate
    pip install fbapi

Using conda:

.. code-block:: bash

    conda create -n fbapi-env python=3.9
    conda activate fbapi-env
    pip install fbapi

Docker Installation
-------------------

Use fbapi in a Docker container:

.. code-block:: dockerfile

    FROM python:3.9-slim

    # Install fbapi
    RUN pip install fbapi

    # Set up working directory
    WORKDIR /app

    # Copy configuration
    COPY fbapi_config.yaml .

    # Default command
    CMD ["fbapi", "--config", "fbapi_config.yaml", "test-server"]

Build and run:

.. code-block:: bash

    docker build -t my-fbapi-app .
    docker run -d \
      -v /host/commands:/app/commands \
      -v /host/responses:/app/responses \
      my-fbapi-app