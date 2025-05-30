from test_utils.test_encryption_manager import EncryptionManager
from getpass import getpass

def main():
    # Solicita a senha do usuário
    senha = getpass("Digite sua senha: ")

    # Cria uma instância do gerenciador de criptografia
    manager = EncryptionManager()

    # Criptografa a senha
    senha_criptografada = manager.encrypt(senha)
    print(f"\nSenha criptografada: {senha_criptografada}")

    # Descriptografa a senha
    senha_descriptografada = manager.decrypt(senha_criptografada)
    print(f"Senha descriptografada: {senha_descriptografada}")

if __name__ == "__main__":
    main()
