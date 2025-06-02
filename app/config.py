# config.py
from pathlib import Path

# Caminhos absolutos
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "_internal" / "connectiondata"
ENCRYPTION_KEY_PATH = DATA_DIR / "encryption.key"
CONNECTIONS_FILE = DATA_DIR / "connections.json"

# Garante que os diretórios existam
DATA_DIR.mkdir(parents=True, exist_ok=True)