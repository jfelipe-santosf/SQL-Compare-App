import tkinter as tk

class ScreenNavigationManager:
    def __init__(self, root):
        self.root = root
        self.parameter = None

    def navigate_to_connect_screen(self, parameter, on_connect_callback=None):
        """
        Navega para a tela de conexão (ConnectScreen).

        :param parameter: 0 para source, 1 para target
        """
        self.parameter = parameter
        from app.ui import ConnectScreen
        ConnectScreen(self.root, on_connect_callback)

    def navigate_to_filter_screen(self):
        """
        Navega para a tela de filtro (FilterScreen).
        """
        # Importa a classe FilterScreen
        from app.ui import FilterScreen

        # Inicializa a tela de filtro diretamente
        FilterScreen(self.root)