import json
from datetime import datetime
import keyring
from typing import List, Dict, Optional
import uuid

class SavedConnectionsManager:
    def __init__(self):
        # Usamos um nome fixo para o serviço no Credential Manager
        self.keyring_service_name = "SQLConnectionsManager"
        # Dicionário em memória para mapeamento de nomes amigáveis para UUIDs
        self.connection_index = {}
        # Carrega o índice ao inicializar
        self._load_index()

    def _load_index(self):
        """Carrega o índice de conexões do Credential Manager"""
        try:
            index_data = keyring.get_password(self.keyring_service_name, "connection_index")
            if index_data:
                self.connection_index = json.loads(index_data)
        except Exception:
            self.connection_index = {}

    def _save_index(self):
        """Salva o índice de conexões no Credential Manager"""
        try:
            keyring.set_password(
                self.keyring_service_name,
                "connection_index",
                json.dumps(self.connection_index)
            )
        except Exception:
            pass

    def _generate_connection_id(self) -> str:
        """Gera um UUID único para a conexão"""
        return str(uuid.uuid4())

    def save_connection(self, server_name: str, user_name: str, password: str,
                       authentication: str, database_name: str) -> str:
        """Armazena todos os dados da conexão em uma única entrada no Credential Manager"""
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
            conn_data = self.get_connection_by_id(cid)
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

    def get_all_connections(self) -> List[Dict]:
        """Recupera todas as conexões armazenadas"""
        connections = []
        for connection_id in self.connection_index.keys():
            conn_data = self.get_connection_by_id(connection_id)
            if conn_data:
                conn_data['connection_id'] = connection_id  # Adiciona o ID aos dados
                connections.append(conn_data)
        
        # Ordena pelo último modificado
        connections.sort(key=lambda x: x["last_modified"], reverse=True)
        
        return connections

    def get_connection_by_id(self, connection_id: str) -> Optional[Dict]:
        """Recupera uma conexão específica pelo seu ID"""
        try:
            connection_str = keyring.get_password(self.keyring_service_name, connection_id)
            if connection_str:
                return json.loads(connection_str)
        except Exception:
            return None
        return None

    def get_connection(self, server_name: str, database_name: str) -> tuple[Optional[Dict], Optional[str]]:
        """Recupera uma conexão específica por servidor e banco de dados
        
        Returns:
            tuple: (connection_data, connection_id) ou (None, None) se não encontrado
        """
        for connection_id, data in self.connection_index.items():
            if (data["server_name"] == server_name and 
                data["database_name"] == database_name):
                return self.get_connection_by_id(connection_id), connection_id
        return None, None
    
    def get_connection_id(self, server_name: str, database_name: str) -> Optional[str]:
        """Recupera apenas o ID de uma conexão específica"""
        for connection_id, data in self.connection_index.items():
            if (data["server_name"] == server_name and 
                data["database_name"] == database_name):
                return connection_id
        return None
    
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