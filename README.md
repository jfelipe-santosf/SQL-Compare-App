# SQL Server Schema Compare

A tool for comparing and synchronizing SQL Server database schemas.

## Features

- Compare schemas between two SQL Server databases
- View differences in tables, views, stored procedures, and functions
- Selectively apply changes to synchronize schemas
- Save and manage database connections
- Windows Authentication and SQL Server Authentication support
- Modern and intuitive user interface using ttkbootstrap

## Requirements

- Python 3.7 or higher
- SQL Server database
- SQL Server drivers (ODBC)

## Installation

```bash
pip install .
```

## Development Setup

```bash
# Clone the repository
git clone <repository-url>
cd sql-server-compare

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

## Testing

```bash
# Run tests with coverage
pytest --cov=sql_compare

# Run specific test file
pytest tests/test_schema_comparer.py
```

## Project Structure

```
sql-server-compare/
├── src/
│   └── sql_compare/
│       ├── core/         # Core business logic
│       ├── ui/          # User interface components
│       └── utils/       # Utility functions and classes
├── tests/              # Test files
└── pyproject.toml     # Project configuration
```

## Contributing

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make changes and add tests
4. Run tests and linting (`pytest` and `pre-commit run --all-files`)
5. Commit changes and push to your fork
6. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
# Install development dependencies
pip install -e ".[dev]"
```

## Usage

```bash
# Run the application
sqlcompare
```

## Project Structure

```
sql_compare/
├── core/
│   ├── __init__.py
│   └── schema_comparer.py    # Core comparison logic
├── ui/
│   ├── __init__.py
│   ├── connection_dialog.py  # Connection dialog window
│   └── main_window.py       # Main application window
├── utils/
│   ├── __init__.py
│   └── connection_manager.py # Connection persistence
└── __init__.py
```

## License

MIT
