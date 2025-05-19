# SQL Server Schema Compare

A tool for comparing and synchronizing SQL Server database schemas.

## Features

- Compare schemas between two SQL Server databases
- View differences in tables, views, stored procedures, and functions
- Selectively apply changes to synchronize schemas
- Save and manage database connections
- Windows Authentication and SQL Server Authentication support

## Installation

```bash
pip install .
```

## Development Setup

```bash
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
