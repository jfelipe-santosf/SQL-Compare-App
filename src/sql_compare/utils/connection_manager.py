from typing import Dict, List, Optional
import json
import os
from pathlib import Path

class ConnectionManager:
    DEFAULT_CONFIG_FILE = Path('connections.json')
    
    def __init__(self, config_file: Optional[Path] = None):
        self.config_file = config_file or self.DEFAULT_CONFIG_FILE
        self.recent_connections = self.load_connections()
        
    def load_connections(self) -> List[Dict]:
        """Load saved connections from file"""
        try:
            if self.config_file.exists():
                with open(self.config_file, 'r') as f:
                    return json.load(f)
        except (json.JSONDecodeError, IOError):
            pass
        return []
        
    def save_connections(self, connections: List[Dict]) -> None:
        """Save connections to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(connections, f, indent=2)
        except IOError:
            pass  # Silently fail if we can't save
            
    def add_connection(self, connection: Dict) -> None:
        """Add a new connection to the recent list"""
        # Remove password before saving
        conn_to_save = connection.copy()
        if "password" in conn_to_save:
            del conn_to_save["password"]
            
        # Check if connection already exists
        existing = next((i for i, c in enumerate(self.recent_connections)
                        if c["server"] == conn_to_save["server"] and
                        c["database"] == conn_to_save["database"]), None)
                        
        if existing is not None:
            self.recent_connections.pop(existing)
            
        # Add new connection at the beginning
        self.recent_connections.insert(0, conn_to_save)
        
        # Keep only last 10 connections
        self.recent_connections = self.recent_connections[:10]
        
        # Save to file
        self.save_connections(self.recent_connections)
        
    def get_recent_connections(self) -> List[Dict]:
        """Get list of recent connections"""
        return self.recent_connections.copy()
