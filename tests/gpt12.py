from PyQt6 import QtWidgets, QtCore, QtGui
import os
import threading
# from app.utils import DatabaseConnectionManager as dcm, SavedConnectionsManager as scm


class ConnectScreen(QtWidgets.QDialog):
    def __init__(self, parent=None, position=None, on_connect_callback=None):
        super().__init__(parent)
        self.on_connect_callback = on_connect_callback
        self.was_cancelled = True

        self.setWindowTitle("Select connection")
        self.setFixedSize(390, 490)
        if position:
            self.move(position['x'], position['y'] + 20)

        self.connections = []

        self._build_ui()
        self.get_saved_connections()
        self.update_authentication()

    def _build_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Treeview (QTreeWidget)
        self.treeview = QtWidgets.QTreeWidget()
        self.treeview.setHeaderLabels(["Server", "Database"])
        self.treeview.setSelectionMode(QtWidgets.QAbstractItemView.SelectionMode.SingleSelection)
        self.treeview.setContextMenuPolicy(QtCore.Qt.ContextMenuPolicy.CustomContextMenu)
        self.treeview.customContextMenuRequested.connect(self.show_context_menu)
        self.treeview.itemSelectionChanged.connect(self.on_treeview_select)
        self.treeview.itemDoubleClicked.connect(self.menu_connect)

        layout.addWidget(self.treeview, stretch=3)

        # Entry frame
        entry_frame = QtWidgets.QFrame()
        entry_frame.setStyleSheet("background-color: #F0F0F0;")
        entry_layout = QtWidgets.QFormLayout(entry_frame)
        entry_layout.setLabelAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        entry_layout.setFormAlignment(QtCore.Qt.AlignmentFlag.AlignLeft | QtCore.Qt.AlignmentFlag.AlignTop)
        entry_layout.setContentsMargins(10, 10, 10, 10)

        # Server Name
        self.entry_server_name = QtWidgets.QLineEdit()
        entry_layout.addRow("Server name:", self.entry_server_name)

        # Authentication Combo
        self.dropdown_authentication = QtWidgets.QComboBox()
        self.dropdown_authentication.addItems(["Windows Authentication", "SQL Authentication"])
        self.dropdown_authentication.currentTextChanged.connect(self.update_authentication)
        entry_layout.addRow("Authentication:", self.dropdown_authentication)

        # User Name
        self.entry_user_name = QtWidgets.QLineEdit()
        entry_layout.addRow("User name:", self.entry_user_name)

        # Password
        self.entry_password = QtWidgets.QLineEdit()
        self.entry_password.setEchoMode(QtWidgets.QLineEdit.EchoMode.Password)
        entry_layout.addRow("Password:", self.entry_password)

        # Database name dropdown
        self.dropdown_database_name = QtWidgets.QComboBox()
        self.dropdown_database_name.setEditable(True)  # Allow typing too
        self.dropdown_database_name.popupAboutToBeShown.connect(self.get_databases_threaded)
        entry_layout.addRow("Database Name:", self.dropdown_database_name)

        # Remember checkbox
        self.check_remember = QtWidgets.QCheckBox("Remember")
        entry_layout.addRow(self.check_remember)

        # Buttons
        buttons_layout = QtWidgets.QHBoxLayout()
        btn_cancel = QtWidgets.QPushButton("Cancel")
        btn_cancel.clicked.connect(self._on_window_close)
        buttons_layout.addWidget(btn_cancel)

        self.btn_connect = QtWidgets.QPushButton("Connect")
        self.btn_connect.clicked.connect(self.on_connect_btn)
        buttons_layout.addWidget(self.btn_connect)

        entry_layout.addRow(buttons_layout)

        layout.addWidget(entry_frame, stretch=2)

    def update_authentication(self):
        auth = self.dropdown_authentication.currentText()
        if auth == "Windows Authentication":
            self.entry_user_name.setText(os.getlogin())
            self.entry_user_name.setEnabled(False)
            self.entry_password.setEnabled(False)
            self.entry_password.clear()
        else:
            self.entry_user_name.setEnabled(True)
            self.entry_user_name.clear()
            self.entry_password.setEnabled(True)
            self.entry_password.clear()

    def get_databases_threaded(self):
        threading.Thread(target=self.get_databases, daemon=True).start()

    def get_databases(self):
        server_name = self.entry_server_name.text().strip()
        if not server_name:
            return

        user_name = self.entry_user_name.text().strip()
        password = self.entry_password.text()
        authentication = self.dropdown_authentication.currentText()

        if authentication == "Windows Authentication":
            user_name = None
            password = None
        else:
            if not user_name or not password:
                return

        # try:
        #     db_conn = dcm(
        #         server=server_name,
        #         username=user_name,
        #         password=password,
        #         authentication=authentication
        #     )
        #     db_conn.connect()
        #     databases = db_conn.get_all_databases()
        #     db_conn.close()

        #     QtCore.QMetaObject.invokeMethod(
        #         self.dropdown_database_name,
        #         "clear",
        #         QtCore.Qt.ConnectionType.QueuedConnection
        #     )
        #     if databases:
        #         QtCore.QMetaObject.invokeMethod(
        #             self.dropdown_database_name,
        #             "addItems",
        #             QtCore.Qt.ConnectionType.QueuedConnection,
        #             QtCore.Q_ARG(list, databases)
        #         )
        #     else:
        #         QtCore.QMetaObject.invokeMethod(
        #             self.dropdown_database_name,
        #             "addItem",
        #             QtCore.Qt.ConnectionType.QueuedConnection,
        #             QtCore.Q_ARG(str, "No databases found")
        #         )

        # except Exception as e:
        #     print(f"Error fetching databases: {e}")

    def get_saved_connections(self):
        # try:
        #     self.connections = scm().get_all_connections()
        #     self.treeview.clear()
        #     for conn in self.connections:
        #         item = QtWidgets.QTreeWidgetItem([conn["server_name"], conn["database_name"]])
        #         item.setData(0, QtCore.Qt.ItemDataRole.UserRole, conn["connection_id"])
        #         self.treeview.addTopLevelItem(item)
        # except Exception as e:
        #     QtWidgets.QMessageBox.critical(self, "Error", f"Failed to load saved connections: {e}")
        self

    def _validate_fields(self):
        if not self.entry_server_name.text().strip():
            QtWidgets.QMessageBox.warning(self, "Warning", "Server name is required.")
            return False

        if self.dropdown_authentication.currentText() == "SQL Authentication":
            if not self.entry_user_name.text().strip() or not self.entry_password.text():
                QtWidgets.QMessageBox.warning(self, "Warning", "User name and password are required for SQL Authentication.")
                return False

        if not self.dropdown_database_name.currentText().strip():
            QtWidgets.QMessageBox.warning(self, "Warning", "Database name is required.")
            return False

        return True

    def on_connect_btn(self):
        if not self._validate_fields():
            return

        connection_data = {
            "server_name": self.entry_server_name.text(),
            "user_name": self.entry_user_name.text() if self.dropdown_authentication.currentText() == "SQL Authentication" else None,
            "password": self.entry_password.text() if self.dropdown_authentication.currentText() == "SQL Authentication" else None,
            "authentication": self.dropdown_authentication.currentText(),
            "database_name": self.dropdown_database_name.currentText()
        }

        # try:
        #     dcm(
        #         server=connection_data["server_name"],
        #         username=connection_data["user_name"],
        #         password=connection_data["password"],
        #         authentication=connection_data["authentication"],
        #         database=connection_data["database_name"]
        #     ).connect()
        # except Exception as e:
        #     QtWidgets.QMessageBox.critical(self, "Connection Error", f"Failed to connect to the database: {e}")
        #     return

        if self.check_remember.isChecked():
            self.save_connection(connection_data)

        self.was_cancelled = False
        if self.on_connect_callback:
            self.on_connect_callback(connection_data)
        self.accept()

    def menu_connect(self):
        selected = self.treeview.selectedItems()
        if not selected:
            return
        iid = selected[0].data(0, QtCore.Qt.ItemDataRole.UserRole)
        connection_data = None

        for connection in self.connections:
            if connection["connection_id"] == iid:
                connection_data = {
                    "server_name": connection["server_name"],
                    "user_name": connection["user_name"] if connection["authentication"] == "SQL Authentication" else None,
                    "password": connection["password"] if connection["authentication"] == "SQL Authentication" else None,
                    "authentication": connection["authentication"],
                    "database_name": connection["database_name"]
                }
                break

        if not connection_data:
            return

        # try:
        #     dcm(
        #         server=connection_data["server_name"],
        #         username=connection_data["user_name"],
        #         password=connection_data["password"],
        #         authentication=connection_data["authentication"],
        #         database=connection_data["database_name"]
        #     ).connect()
        # except Exception as e:
        #     QtWidgets.QMessageBox.critical(self, "Connection Error", f"Failed to connect to the database: {e}")
        #     return

        if self.check_remember.isChecked():
            self.save_connection(connection_data)

        self.was_cancelled = False
        if self.on_connect_callback:
            self.on_connect_callback(connection_data)
        self.accept()

    def on_treeview_select(self):
        selected = self.treeview.selectedItems()
        if not selected:
            return

        iid = selected[0].data(0, QtCore.Qt.ItemDataRole.UserRole)

        for conn in self.connections:
            if conn["connection_id"] == iid:
                self.entry_server_name.setText(conn["server_name"])
                self.dropdown_authentication.setCurrentText(conn["authentication"])

                if conn["authentication"] == "Windows Authentication":
                    self.entry_user_name.setText(os.getlogin())
                    self.entry_user_name.setEnabled(False)
                    self.entry_password.clear()
                    self.entry_password.setEnabled(False)
                else:
                    self.entry_user_name.setEnabled(True)
                    self.entry_user_name.setText(conn["user_name"])
                    self.entry_password.setEnabled(True)
                    self.entry_password.setText(conn["password"])

                self.dropdown_database_name.setCurrentText(conn["database_name"])
                break

    def save_connection(self, connection_data):
        # try:
        #     scm().save_connection(
        #         server_name=connection_data["server_name"],
        #         user_name=connection_data["user_name"],
        #         password=connection_data["password"],
        #         authentication=connection_data["authentication"],
        #         database_name=connection_data["database_name"]
        #     )
        # except Exception as e:
        #     QtWidgets.QMessageBox.warning(self, "Warning", f"Failed to save connection: {e}")
        self

    def show_context_menu(self, pos):
        menu = QtWidgets.QMenu(self)

        selected = self.treeview.selectedItems()
        has_selection = bool(selected)
        has_items = self.treeview.topLevelItemCount() > 0

        refresh_action = menu.addAction("Refresh")
        connect_action = menu.addAction("Connect")
        delete_action = menu.addAction("Delete")
        clear_action = menu.addAction("Clear historic connection")
        exit_action = menu.addAction("Exit")

        connect_action.setEnabled(has_selection)
        delete_action.setEnabled(has_selection)
        clear_action.setEnabled(has_items)

        action = menu.exec(self.treeview.viewport().mapToGlobal(pos))

        if action == refresh_action:
            self.get_saved_connections()
        elif action == connect_action:
            self.menu_connect()
        elif action == delete_action:
            self._delete_selected_connection()
        elif action == clear_action:
            self.clear_historic_connections()
        elif action == exit_action:
            self._on_window_close()

    def _delete_selected_connection(self):
        selected = self.treeview.selectedItems()
        if not selected:
            QtWidgets.QMessageBox.warning(self, "Warning", "No connection selected to delete.")
            return
        iid = selected[0].data(0, QtCore.Qt.ItemDataRole.UserRole)

        conn_data = None
        for conn in self.connections:
            if conn["connection_id"] == iid:
                conn_data = conn
                break

        if not conn_data:
            return

        confirm = QtWidgets.QMessageBox.question(
            self, "Confirm Delete",
            f"Delete connection:\nServer: {conn_data['server_name']}\nDatabase: {conn_data['database_name']}?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )

        if confirm != QtWidgets.QMessageBox.StandardButton.Yes:
            return

        # try:
        #     scm().delete_connection(connection_id=iid)
        #     self.get_saved_connections()
        #     QtWidgets.QMessageBox.information(self, "Success", "Connection deleted successfully.")
        # except Exception as e:
        #     QtWidgets.QMessageBox.critical(self, "Error", f"Failed to delete connection: {e}")

    def clear_historic_connections(self):
        confirm = QtWidgets.QMessageBox.question(
            self,
            "Clear All Connections",
            "This will delete ALL saved connections.\nAre you sure you want to continue?",
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No,
            QtWidgets.QMessageBox.StandardButton.No
        )

        if confirm == QtWidgets.QMessageBox.StandardButton.Yes:
            # try:
            #     scm().delete_all_connections()
            #     self.get_saved_connections()
            #     QtWidgets.QMessageBox.information(self, "Success", "All connections have been deleted.")
            # except Exception as e:
            #     QtWidgets.QMessageBox.critical(self, "Error", f"Failed to clear connections: {str(e)}")
            self

    def _on_window_close(self):
        if self.on_connect_callback:
            self.on_connect_callback(None)
        self.reject()


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    window = ConnectScreen()
    window.exec()
