from getpass import getpass
from test_utils.test_encryption_manager import EncryptionManager
from test_utils.test_saved_connections_manager import SavedConnectionsManager

def main():
    # Cria instâncias
    encryption_manager = EncryptionManager()
    connections_manager = SavedConnectionsManager(encryption_manager)

    print("\n--- Gerenciador de Conexões ---")
    print("1. Salvar nova conexão")
    print("2. Listar conexões")
    print("3. Excluir conexão")
    escolha = input("Escolha uma opção (1/2/3): ")

    if escolha == "1":
        server = input("Servidor: ")
        user = input("Usuário: ")
        password = getpass("Senha: ")
        auth = input("Autenticação: ")
        database = input("Banco de dados: ")

        connections_manager.save_connection(
            server_name=server,
            user_name=user,
            password=password,
            authentication=auth,
            database_name=database
        )
        print("\n✅ Conexão salva com sucesso.")

    elif escolha == "2":
        connections = connections_manager.get_all_connections()
        if not connections:
            print("\nNenhuma conexão salva.")
        else:
            print("\n🔗 Conexões salvas:")
            for conn in connections:
                print(f"- {conn['server_name']} / {conn['database_name']} (modificado em {conn['last_modified']} / {conn['password']})")

    elif escolha == "3":
        server = input("Servidor: ")
        database = input("Banco de dados: ")

        connections_manager.delete_connection(server, database)
        print("\n🗑️ Conexão excluída (se existia).")

    else:
        print("❌ Opção inválida.")

if __name__ == "__main__":
    main()
