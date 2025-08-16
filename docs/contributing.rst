Contributing
============

We welcome contributions to the fbapi library! This document outlines how to contribute effectively.

Getting Started
---------------

Development Setup
~~~~~~~~~~~~~~~~

1. **Fork and clone the repository:**

   .. code-block:: bash

       git clone https://github.com/your-username/fbapi.git
       cd fbapi

2. **Create a virtual environment:**

   .. code-block:: bash

       python -m venv venv
       source venv/bin/activate  # On Windows: venv\Scripts\activate

3. **Install development dependencies:**

   .. code-block:: bash

       pip install -e .[dev]

4. **Verify the installation:**

   .. code-block:: bash

       python -m pytest tests/
       python -m flake8 src/
       python -m mypy src/

Development Workflow
-------------------

Code Style
~~~~~~~~~~

We use several tools to maintain code quality:

- **Black** for code formatting
- **isort** for import sorting  
- **flake8** for linting
- **mypy** for type checking

Run these before committing:

.. code-block:: bash

    # Format code
    python -m black src/ tests/
    python -m isort src/ tests/
    
    # Check style and types
    python -m flake8 src/ tests/
    python -m mypy src/

Testing
~~~~~~~

All contributions must include tests:

.. code-block:: bash

    # Run all tests
    python -m pytest tests/
    
    # Run with coverage
    python -m pytest tests/ --cov=fbapi --cov-report=html
    
    # Run specific test categories
    python -m pytest tests/ -m unit
    python -m pytest tests/ -m integration

**Test Categories:**

- ``unit`` - Unit tests for individual components
- ``integration`` - Tests that involve multiple components
- ``performance`` - Performance and benchmark tests
- ``slow`` - Tests that take longer to run

Writing Tests
~~~~~~~~~~~~

Follow these guidelines for writing tests:

.. code-block:: python

    import pytest
    from fbapi import FileBasedAPIClient
    from fbapi.exceptions import ValidationError
    
    class TestFileBasedAPIClient:
        """Test the FileBasedAPIClient class"""
        
        def test_client_initialization(self):
            """Test client initializes with correct defaults"""
            client = FileBasedAPIClient(
                command_dir="./commands",
                response_dir="./responses"
            )
            
            assert client.command_dir == "./commands"
            assert client.response_dir == "./responses"
            assert client.timeout_seconds == 30.0
        
        def test_invalid_directory_raises_error(self):
            """Test that invalid directories raise appropriate errors"""
            with pytest.raises(ValidationError):
                FileBasedAPIClient(
                    command_dir="",
                    response_dir="./responses"
                )
        
        @pytest.mark.integration
        def test_client_server_communication(self):
            """Test basic client-server communication"""
            # Integration test implementation
            pass

Making Changes
--------------

Branch Naming
~~~~~~~~~~~~

Use descriptive branch names:

- ``feature/add-async-support`` - New features
- ``fix/timeout-handling`` - Bug fixes  
- ``docs/api-reference`` - Documentation updates
- ``refactor/client-structure`` - Refactoring

Commit Messages
~~~~~~~~~~~~~~

Write clear, descriptive commit messages:

.. code-block:: text

    Add async support for client operations
    
    - Implement async versions of call_command and wait_for_completion
    - Add AsyncFileBasedAPIClient class
    - Update documentation with async examples
    - Add tests for async functionality
    
    Closes #123

Pull Request Process
-------------------

1. **Create a feature branch:**

   .. code-block:: bash

       git checkout -b feature/your-feature-name

2. **Make your changes with tests**

3. **Ensure all checks pass:**

   .. code-block:: bash

       python -m pytest tests/
       python -m flake8 src/ tests/
       python -m mypy src/

4. **Update documentation if needed**

5. **Create a pull request**

Pull Request Checklist
~~~~~~~~~~~~~~~~~~~~~~

- [ ] Code follows style guidelines (black, isort, flake8)
- [ ] Type hints are included (mypy passes)
- [ ] Tests are included and pass
- [ ] Documentation is updated
- [ ] CHANGELOG.md is updated (for user-facing changes)
- [ ] Commit messages are descriptive

Code Review
~~~~~~~~~~~

All contributions are reviewed before merging:

- **Functionality** - Does the code work as intended?
- **Tests** - Are there adequate tests?
- **Documentation** - Is documentation clear and complete?
- **Style** - Does code follow project conventions?
- **Performance** - Are there any performance implications?

Types of Contributions
---------------------

Bug Reports
~~~~~~~~~~

When reporting bugs, include:

- **Environment details** (Python version, OS, fbapi version)
- **Minimal reproduction case**
- **Expected vs actual behavior**
- **Error messages and stack traces**

Example bug report:

.. code-block:: text

    **Environment:**
    - Python 3.11.2
    - fbapi 0.1.5
    - macOS 13.2
    
    **Bug Description:**
    Client hangs when response directory doesn't exist
    
    **Reproduction:**
    ```python
    client = FileBasedAPIClient(
        command_dir="./commands",
        response_dir="./nonexistent"
    )
    client.call_command('test', handler)  # Hangs here
    ```
    
    **Expected:** Should raise ValidationError
    **Actual:** Client hangs indefinitely

Feature Requests
~~~~~~~~~~~~~~~

For feature requests, provide:

- **Use case description**
- **Proposed API design**
- **Alternative solutions considered**
- **Implementation willingness**

Documentation
~~~~~~~~~~~~

Documentation improvements are always welcome:

- **API documentation** - Docstring improvements
- **User guides** - Usage examples and tutorials
- **Developer docs** - Architecture and design docs

Code Contributions
~~~~~~~~~~~~~~~~~

Areas where contributions are especially valuable:

**Core Features:**
- Async/await support
- Connection pooling
- Advanced security features
- Performance optimizations

**Integrations:**
- Framework integrations (FastAPI, Flask, etc.)
- Message queue backends
- Serialization formats beyond JSON

**Developer Experience:**
- Better error messages
- Development tools
- IDE integrations

Release Process
--------------

For maintainers, the release process is:

1. **Update version numbers**
2. **Update CHANGELOG.md**
3. **Create and test release candidate**
4. **Create GitHub release**
5. **Publish to PyPI**

Versioning follows `Semantic Versioning <https://semver.org/>`_:

- **MAJOR** - Incompatible API changes
- **MINOR** - New functionality (backward compatible)
- **PATCH** - Bug fixes (backward compatible)

Community Guidelines
-------------------

Code of Conduct
~~~~~~~~~~~~~~

- **Be respectful** - Treat all contributors with respect
- **Be inclusive** - Welcome developers of all skill levels
- **Be constructive** - Provide helpful feedback
- **Be patient** - Remember that everyone is learning

Communication
~~~~~~~~~~~~

- **GitHub Issues** - Bug reports and feature requests
- **Pull Requests** - Code contributions and reviews
- **Discussions** - General questions and ideas

Getting Help
-----------

If you need help contributing:

- **Check existing issues** - Your question might already be answered
- **Ask in discussions** - For general questions
- **Join development chat** - For real-time help (if available)

Thank you for contributing to fbapi! 🎉