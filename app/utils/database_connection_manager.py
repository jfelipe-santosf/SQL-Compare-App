import pyodbc

class DatabaseConnectionManager:
    def __init__(self, server, username=None, password=None, database=None, authentication="Windows Authentication"):
        self.server = server
        self.username = username
        self.password = password
        self.database = database
        self.authentication = authentication
        self.connection = None

    def connect(self):
        try:
            if self.authentication == "Windows Authentication":
                self.connection = pyodbc.connect(
                    f'DRIVER={{SQL Server}};SERVER={self.server};Trusted_Connection=yes;DATABASE={self.database or "master"}'
                )
            else:
                self.connection = pyodbc.connect(
                    f'DRIVER={{SQL Server}};SERVER={self.server};UID={self.username};PWD={self.password};DATABASE={self.database or "master"}'
                )
            print("Connection successful")
        except pyodbc.Error as e:
            print(f"Error connecting to database: {e}")

    def get_all_databases(self):
        print("Fetching all databases...")
        if not self.connection:
            raise Exception("Not connected to the database")

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute("SELECT name FROM sys.databases ORDER BY name ASC")
            databases = [row[0] for row in cursor.fetchall()]
            return databases
        except pyodbc.Error as e:
            print(f"Error fetching databases: {e}")
            return []
        finally:
            if cursor:
                cursor.close()

    def close(self):
        if self.connection:
            self.connection.close()
            print("Connection closed")