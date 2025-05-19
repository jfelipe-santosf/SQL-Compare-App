from sql_compare.utils.connection_manager import ConnectionManager
import pytest
import tempfile
from pathlib import Path
import json
import os

@pytest.fixture
def temp_connection_file():
    temp_dir = tempfile.mkdtemp()
    temp_file = Path(temp_dir) / 'connections.json'
    yield temp_file
    try:
        if temp_file.exists():
            os.close(os.open(temp_file, os.O_RDONLY))  # Ensure file is closed
            temp_file.unlink()
        os.rmdir(temp_dir)
    except (PermissionError, OSError):
        pass  # Ignore cleanup errors on Windows    def test_connection_manager_initialization(temp_connection_file):
        manager = ConnectionManager(config_file=temp_connection_file)
        assert isinstance(manager.recent_connections, list)
        assert len(manager.recent_connections) == 0  # Deve estar vazio com o arquivo temporário    def test_connection_manager_save_and_load(temp_connection_file):
        # Initialize first manager with temp file
        manager = ConnectionManager(config_file=temp_connection_file)
        
        test_connections = [
            {"server": "test-server", "database": "test-db", "authentication": "Windows Authentication"}
        ]
        manager.save_connections(test_connections)
        
        # Create new instance to test loading
        new_manager = ConnectionManager(config_file=temp_connection_file)
        loaded_connections = new_manager.load_connections()
        assert loaded_connections == test_connections
