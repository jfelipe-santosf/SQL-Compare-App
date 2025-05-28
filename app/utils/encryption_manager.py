from cryptography.fernet import Fernet

class EncryptionManager:
    def __init__(self, key=None):
        # Gera uma chave se nenhuma for fornecida
        self.key = key or Fernet.generate_key()
        self.cipher = Fernet(self.key)

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