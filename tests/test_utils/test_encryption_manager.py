from cryptography.fernet import Fernet
from pathlib import Path

class EncryptionManager:
    def __init__(self, key=None):
        try:
            # Define o diretório _internal
            self._internal_dir = Path("_internal")
            self.key_file = self._internal_dir / "encryption.key"

            # Carrega a chave do arquivo se existir, ou gera uma nova
            if key is None and self.key_file.exists():
                with open(self.key_file, "rb") as f:
                    self.key = f.read()
            else:
                self.key = key or Fernet.generate_key()
                # Salva a chave no arquivo
                with open(self.key_file, "wb") as f:
                    f.write(self.key)

            self.cipher = Fernet(self.key)
        except Exception as e:
            raise

    def encrypt(self, password: str) -> str:
        """
        Criptografa a senha fornecida.

        :param password: Senha em texto simples.
        :return: Senha criptografada.
        """
        return self.cipher.encrypt(password.encode()).decode()

    def decrypt(self, encrypted_password: str) -> str:
        """
        Descriptografa a senha fornecida.

        :param encrypted_password: Senha criptografada.
        :return: Senha em texto simples.
        """
        return self.cipher.decrypt(encrypted_password.encode()).decode()