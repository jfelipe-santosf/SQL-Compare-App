import json
from datetime import datetime
import keyring
from typing import List, Dict, Optional
import uuid

class SavedConnectionsManager:
    def __init__(self):
        self.keyring_service_name = "SQLConnectionsManager" # Nome do serviço no Credential Manager
        self.connection_index = {} # Índice de conexões armazenadas
        self._load_index() # Carrega o índice de conexões ao inicializar

    
    def get_all_connections(self) -> List[Dict]:
        """Retrieves all stored connections
        Returns:
            List[Dict]: List of dictionaries with data for each connection
        """
        connections = []
        for connection_id in self.connection_index.keys():
            conn_data = self._get_connection_by_id(connection_id)
            if conn_data:
                conn_data['connection_id'] = connection_id  # Adiciona o ID aos dados
                connections.append(conn_data)
        
        # Ordena pelo último modificado
        connections.sort(key=lambda x: x["last_modified"], reverse=True)
        
        return connections

    def save_connection(self, server_name: str, user_name: str, password: str,
                       authentication: str, database_name: str) -> str:
        """Stores all connection data in Credential Manager"""
        # Cria um objeto com todos os dados da conexão
        connection_data = {
            "server_name": server_name,
            "user_name": user_name,
            "password": password,
            "authentication": authentication,
            "database_name": database_name,
            "last_modified": datetime.utcnow().isoformat()
        }

        # Verifica se já existe uma conexão com esses parâmetros
        connection_id = None
        for cid in self.connection_index:
            conn_data = self._get_connection_by_id(cid)
            if (conn_data["server_name"] == server_name and 
                conn_data["database_name"] == database_name and
                conn_data["authentication"] == authentication):
                connection_id = cid
                break

        # Se não existir, gera um novo ID
        if not connection_id:
            connection_id = self._generate_connection_id()

        # Armazena os dados no Credential Manager
        keyring.set_password(
            self.keyring_service_name,
            connection_id,
            json.dumps(connection_data))

        # Atualiza o índice
        self.connection_index[connection_id] = {
            "server_name": server_name,
            "database_name": database_name,
            "display_name": f"{server_name}/{database_name}",
            "last_modified": connection_data["last_modified"],
            "authentication": authentication
        }
        self._save_index()

        return connection_id

    def delete_connection(self, connection_id: str) -> bool:
        """Remove uma conexão específica"""

        try:
            # Remove do Credential Manager
            keyring.delete_password(self.keyring_service_name, connection_id)
            # Remove do índice
            del self.connection_index[connection_id]
            self._save_index()
            return True
        except Exception:
            pass
        return False

    def delete_all_connections(self) -> None:
        """Remove todas as conexões armazenadas"""
        for connection_id in list(self.connection_index.keys()):
            try:
                keyring.delete_password(self.keyring_service_name, connection_id)
            except Exception:
                continue
        self.connection_index = {}
        self._save_index()
        
    def _load_index(self):
        """Load the Credential Manager Connection Index"""
        try:
            index_data = keyring.get_password(self.keyring_service_name, "connection_index")
            if index_data:
                self.connection_index = json.loads(index_data)
        except Exception:
            self.connection_index = {}

    def _save_index(self):
        """Saves the connection index in Credential Manager"""
        try:
            keyring.set_password(
                self.keyring_service_name,
                "connection_index",
                json.dumps(self.connection_index)
            )
        except Exception:
            pass

    def _generate_connection_id(self) -> str:
        """Generates a unique UUID for the connection"""
        return str(uuid.uuid4())

    def _get_connection_by_id(self, connection_id: str) -> Optional[Dict]:
        """Retrieves a specific connection by its ID"""
        try:
            connection_str = keyring.get_password(self.keyring_service_name, connection_id)
            if connection_str:
                return json.loads(connection_str)
        except Exception:
            return None
        return None