from typing import Dict, List, Optional
import pyodbc
import time

class DatabaseError(Exception):
    """Base class for database-related errors"""
    pass

class ConnectionError(DatabaseError):
    """Error establishing database connection"""
    pass

class QueryError(DatabaseError):
    """Error executing database query"""
    pass

class SchemaComparerService:
    def __init__(self, max_retries: int = 3, retry_delay: float = 1.0):
        self.max_retries = max_retries
        self.retry_delay = retry_delay

    def connect(self, server: str, database: str, auth_type: str = "Windows",
               username: Optional[str] = None, password: Optional[str] = None) -> pyodbc.Connection:
        """
        Establish connection to SQL Server with retry logic
        """
        last_error = None
        for attempt in range(self.max_retries):
            try:
                # Build connection string
                if auth_type == "Windows Authentication":
                    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
                else:
                    if not username or not password:
                        raise ConnectionError("Username and password are required for SQL Server Authentication")
                    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
                
                # Test connection with timeout
                conn = pyodbc.connect(conn_str, timeout=5)
                
                # Verify connection is working
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                
                return conn
                
            except pyodbc.OperationalError as e:
                last_error = ConnectionError(f"Failed to connect to server {server}: {str(e)}")
                if "Network-related" in str(e):
                    # Network errors might be temporary, retry
                    if attempt < self.max_retries - 1:
                        time.sleep(self.retry_delay)
                        continue
                break
            except pyodbc.Error as e:
                last_error = ConnectionError(f"Database error on {server}: {str(e)}")
                # Don't retry authentication or configuration errors
                break
            except Exception as e:
                last_error = ConnectionError(f"Unexpected error connecting to {server}: {str(e)}")
                break
                
        raise last_error or ConnectionError(f"Failed to connect to {server} after {self.max_retries} attempts")

    def execute_query(self, connection: pyodbc.Connection, query: str, params: tuple = None) -> List[Dict]:
        """
        Execute a query with error handling
        """
        try:
            cursor = connection.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            
            if cursor.description:
                columns = [column[0] for column in cursor.description]
                return [dict(zip(columns, row)) for row in cursor.fetchall()]
            return []
            
        except pyodbc.Error as e:
            raise QueryError(f"Query execution failed: {str(e)}")
        except Exception as e:
            raise QueryError(f"Unexpected error during query execution: {str(e)}")

    def get_schema_objects(self, connection: pyodbc.Connection) -> List[Dict]:
        """Get stored procedures and tables from database"""
        procedures_query = """
            SELECT 
                SCHEMA_NAME(schema_id) as schema_name,
                name as object_name,
                'Stored Procedure' as object_type,
                OBJECT_ID(SCHEMA_NAME(schema_id) + '.' + name) as object_id
            FROM sys.procedures
            ORDER BY schema_name, name
        """
        
        tables_query = """
            SELECT 
                SCHEMA_NAME(t.schema_id) as schema_name,
                t.name as object_name,
                'Table' as object_type,
                OBJECT_ID(SCHEMA_NAME(t.schema_id) + '.' + t.name) as object_id,
                (SELECT COUNT(*) FROM sys.columns c WHERE c.object_id = t.object_id) as column_count
            FROM sys.tables t
            ORDER BY schema_name, t.name
        """
        
        try:
            procedures = self.execute_query(connection, procedures_query)
            tables = self.execute_query(connection, tables_query)
            return procedures + tables
            
        except QueryError as e:
            raise QueryError(f"Failed to retrieve schema objects: {str(e)}")

    def get_table_columns(self, connection: pyodbc.Connection, table_id: int) -> List[Dict]:
        """Get column details for a table"""
        cursor = connection.cursor()
        columns = cursor.execute("""
            SELECT 
                c.name as column_name,
                t.name as data_type,
                c.max_length,
                c.precision,
                c.scale,
                c.is_nullable,
                c.column_id as ordinal_position
            FROM sys.columns c
            INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
            WHERE c.object_id = ?
            ORDER BY c.column_id
        """, table_id).fetchall()
        
        return [dict(zip(['column_name', 'data_type', 'max_length', 'precision', 
                         'scale', 'is_nullable', 'ordinal_position'], row)) 
                for row in columns]
        
    def get_object_definition(self, connection: pyodbc.Connection, object_id: int) -> str:
        """Get object definition from database"""
        cursor = connection.cursor()
        definition = cursor.execute("SELECT OBJECT_DEFINITION(?)", object_id).fetchval()
        return definition or ""
        
    def compare_schemas(self, source_conn: pyodbc.Connection, target_conn: pyodbc.Connection) -> List[Dict]:
        """Compare schemas between two databases"""
        source_objects = {f"{obj['schema_name']}.{obj['object_name']}": obj 
                         for obj in self.get_schema_objects(source_conn)}
        target_objects = {f"{obj['schema_name']}.{obj['object_name']}": obj 
                         for obj in self.get_schema_objects(target_conn)}
        
        differences = []
        
        # Check objects in source that are missing or different in target
        for name, source_obj in source_objects.items():
            if source_obj['object_type'] not in ['Stored Procedure', 'Table']:
                continue
                
            if name not in target_objects:
                differences.append({
                    "object": name,
                    "type": source_obj['object_type'],
                    "action": "Create",
                    "source_details": None,
                    "target_details": None
                })
            else:
                target_obj = target_objects[name]
                
                if source_obj['object_type'] == 'Stored Procedure':
                    # Compare stored procedure definitions
                    source_def = self.get_object_definition(source_conn, source_obj['object_id'])
                    target_def = self.get_object_definition(target_conn, target_obj['object_id'])
                    
                    if source_def != target_def:
                        differences.append({
                            "object": name,
                            "type": "Stored Procedure",
                            "action": "Different",
                            "source_details": None,
                            "target_details": None
                        })
                elif source_obj['object_type'] == 'Table':
                    # Compare table column counts
                    source_cols = self.get_table_columns(source_conn, source_obj['object_id'])
                    target_cols = self.get_table_columns(target_conn, target_obj['object_id'])
                    
                    if len(target_cols) < len(source_cols):
                        differences.append({
                            "object": name,
                            "type": "Table",
                            "action": "Different",
                            "source_details": source_cols,
                            "target_details": target_cols
                        })
        
        # Only check for tables and stored procedures to drop
        for name, target_obj in target_objects.items():
            if target_obj['object_type'] not in ['Stored Procedure', 'Table']:
                continue
                
            if name not in source_objects:
                differences.append({
                    "object": name,
                    "type": target_obj['object_type'],
                    "action": "Drop",
                    "source_details": None,
                    "target_details": None
                })
        
        return differences
