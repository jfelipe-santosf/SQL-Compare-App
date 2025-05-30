import tkinter as tk

class ScreenNavigationManager:
    def __init__(self, root):
        self.root = root
        self.parameter = None

    def navigate_to_connect_screen(self, parameter):
        """
        Navega para a tela de conexão (ConnectScreen).

        :param parameter: 0 para source, 1 para target
        """
        self.parameter = parameter

        # Importa a classe ConnectScreen
        from test_ui.test_connect_screen import ConnectScreen

        # Inicializa a tela de conexão diretamente
        ConnectScreen(self.root)

    def navigate_to_filter_screen(self):
        """
        Navega para a tela de filtro (FilterScreen).
        """
        # Importa a classe FilterScreen
        from test_ui.test_filter_screen import FilterScreen

        # Inicializa a tela de filtro diretamente
        FilterScreen(self.root)