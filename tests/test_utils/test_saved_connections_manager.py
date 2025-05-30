import os
import json
from datetime import datetime
from test_encryption_manager import EncryptionManager

class SavedConnectionsManager:
    def __init__(self, encryption_manager: EncryptionManager, storage_dir="_internal"):
        self.encryption_manager = encryption_manager
        self.storage_dir = storage_dir
        self.storage_file = os.path.join(self.storage_dir, "connections.json")

    def _load_connections(self):
        if not os.path.exists(self.storage_file):
            return []

        with open(self.storage_file, "r") as f:
            connections = json.load(f)

        # Descriptografa as senhas
        for conn in connections:
            try:
                conn["password"] = self.encryption_manager.decrypt(conn["password"])
            except Exception as e:
                conn["password"] = "<Erro ao descriptografar>"

        # Ordena pela data de modificação (do mais recente para o mais antigo)
        connections.sort(key=lambda x: x.get("last_modified", ""), reverse=True)

        return connections

    def _save_connections(self, connections):
        with open(self.storage_file, "w") as f:
            json.dump(connections, f, indent=4)

    def save_connection(self, server_name, user_name, password, authentication, database_name):
        encrypted_password = self.encryption_manager.encrypt(password)
        now = datetime.utcnow().isoformat()

        new_conn = {
            "server_name": server_name,
            "user_name": user_name,
            "password": encrypted_password,
            "authentication": authentication,
            "database_name": database_name,
            "last_modified": now
        }

        connections = self._load_connections()

        # Verifica se já existe e atualiza
        updated = False
        for i, conn in enumerate(connections):
            if conn["server_name"] == server_name and conn["database_name"] == database_name:
                connections[i] = new_conn
                updated = True
                break

        if not updated:
            connections.append(new_conn)

        self._save_connections(connections)

    def get_all_connections(self):
        connections = self._load_connections()
        return sorted(connections, key=lambda x: x["last_modified"], reverse=True)

    def delete_connection(self, server_name, database_name):
        connections = self._load_connections()
        connections = [
            conn for conn in connections
            if not (conn["server_name"] == server_name and conn["database_name"] == database_name)
        ]
        self._save_connections(connections)
