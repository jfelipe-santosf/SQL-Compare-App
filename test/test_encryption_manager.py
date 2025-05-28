import sys
import os

# Adiciona o diretório principal ao sys.path para permitir importações
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.utils.encryption_manager import EncryptionManager
import unittest

class TestEncryptionManager(unittest.TestCase):

    def setUp(self):
        # Configura uma instância do EncryptionManager para os testes
        self.manager = EncryptionManager()

    def test_encrypt_decrypt(self):
        # Testa se a senha criptografada pode ser descriptografada corretamente
        password = "my_secure_password"
        encrypted = self.manager.encrypt(password)
        decrypted = self.manager.decrypt(encrypted)
        self.assertEqual(password, decrypted)

    def test_encrypt_is_different(self):
        # Testa se a senha criptografada é diferente da senha original
        password = "my_secure_password"
        encrypted = self.manager.encrypt(password)
        self.assertNotEqual(password, encrypted)

if __name__ == "__main__":
    unittest.main(verbosity=2)
