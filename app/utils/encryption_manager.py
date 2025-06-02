from cryptography.fernet import Fernet
from app.config import ENCRYPTION_KEY_PATH

class EncryptionManager:
    def __init__(self):
        try:
            if ENCRYPTION_KEY_PATH.exists():
                with open(ENCRYPTION_KEY_PATH, "rb") as f:
                    self.key = f.read()
            else:
                self.key = Fernet.generate_key()
                with open(ENCRYPTION_KEY_PATH, "wb") as f:
                    f.write(self.key)
            self.cipher = Fernet(self.key)
        except Exception as e:
            raise Exception(f"Encryption initialization failed: {str(e)}") from e

    def encrypt(self, password: str) -> str:
        """
        Encrypts the provided password.
        
        Args:
            password: Plain text password to encrypt
            
        Returns:
            Encrypted password as string
            
        Criptografa a senha fornecida.
        :param password: Senha em texto simples
        :return: Senha criptografada
        """
        return self.cipher.encrypt(password.encode()).decode()

    def decrypt(self, encrypted_password: str) -> str:
        """
        Decrypts the provided encrypted password.
        
        Args:
            encrypted_password: Encrypted password string
            
        Returns:
            Decrypted plain text password
            
        Descriptografa a senha fornecida.
        :param encrypted_password: Senha criptografada
        :return: Senha em texto simples
        """
        return self.cipher.decrypt(encrypted_password.encode()).decode()