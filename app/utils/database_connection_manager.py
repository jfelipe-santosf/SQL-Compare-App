import pyodbc

class DatabaseConnectionManager:
    def __init__(self, server, username=None, password=None, database=None, authentication="Windows Authentication"):
        self.server = server
        self.username = username
        self.password = password
        self.database = database
        self.authentication = authentication
        self.connection = None
        print(f'connecting to {self.server}')

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
            raise Exception(f"Error connecting to the database: {e}")

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

    def get_procedures_schema(self):
        print(f"Fetching procedures schema for database: {self.database}")
        if not self.connection:
            raise Exception("Not connected to the database")

        cursor = None
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"""
                SELECT
                    p.name AS [procedure_name],
                    p.modify_date  AS [last_modified_date],
                    OBJECT_DEFINITION(p.object_id) AS [procedure_body]
                FROM 
                    sys.procedures p
                WHERE 
                    p.is_ms_shipped = 0
                ORDER BY
                    [procedure_name]
            """)
            procedures = [
                {
                    "procedure_name": row[0],
                    "last_modified_date": row[1],
                    "procedure_body": row[2]
                }
                for row in cursor.fetchall()
            ]
            return procedures
        except pyodbc.Error as e:
            raise Exception(f"Error fetching procedures schema: {e}")
        finally:
            if cursor:
                cursor.close()