import pyodbc

class SchemaComparer:
    def __init__(self):
        self.source_conn = None
        self.target_conn = None
        
    def connect(self, server, database, auth_type="Windows"):
        """
        Establish connection to SQL Server
        """
        if auth_type == "Windows":
            conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;'
        else:
            # For SQL Server authentication, username and password would be needed
            pass
            
        return pyodbc.connect(conn_str)
        
    def get_schema_objects(self, connection):
        """
        Get schema objects from database
        """
        cursor = connection.cursor()
        
        # Get tables
        tables = cursor.execute("""
            SELECT 
                SCHEMA_NAME(schema_id) as schema_name,
                name as object_name,
                'Table' as object_type
            FROM sys.tables
            ORDER BY schema_name, name
        """).fetchall()
        
        # Get views
        views = cursor.execute("""
            SELECT 
                SCHEMA_NAME(schema_id) as schema_name,
                name as object_name,
                'View' as object_type
            FROM sys.views
            ORDER BY schema_name, name
        """).fetchall()
        
        # Get stored procedures
        procedures = cursor.execute("""
            SELECT 
                SCHEMA_NAME(schema_id) as schema_name,
                name as object_name,
                'Stored Procedure' as object_type
            FROM sys.procedures
            ORDER BY schema_name, name
        """).fetchall()
        
        # Get functions
        functions = cursor.execute("""
            SELECT 
                SCHEMA_NAME(schema_id) as schema_name,
                name as object_name,
                'Function' as object_type
            FROM sys.objects
            WHERE type_desc LIKE '%FUNCTION%'
            ORDER BY schema_name, name
        """).fetchall()
        
        return tables + views + procedures + functions
        
    def get_object_definition(self, connection, schema_name, object_name):
        """
        Get the definition of a database object
        """
        cursor = connection.cursor()
        
        definition = cursor.execute("""
            SELECT OBJECT_DEFINITION(OBJECT_ID(@schema_name + '.' + @object_name))
        """, {'schema_name': schema_name, 'object_name': object_name}).fetchval()
        
        return definition
        
    def compare_schemas(self, source_conn, target_conn):
        """
        Compare schemas between source and target databases
        """
        source_objects = self.get_schema_objects(source_conn)
        target_objects = self.get_schema_objects(target_conn)
        
        differences = []
        
        # Convert target objects to dictionary for faster lookup
        target_dict = {
            f"{obj.schema_name}.{obj.object_name}": obj 
            for obj in target_objects
        }
        
        for source_obj in source_objects:
            full_name = f"{source_obj.schema_name}.{source_obj.object_name}"
            
            if full_name not in target_dict:
                # Object exists in source but not in target
                differences.append({
                    'object': full_name,
                    'type': source_obj.object_type,
                    'action': 'Create',
                    'source': self.get_object_definition(source_conn, source_obj.schema_name, source_obj.object_name),
                    'target': ''
                })
            else:
                # Object exists in both, compare definitions
                source_def = self.get_object_definition(source_conn, source_obj.schema_name, source_obj.object_name)
                target_def = self.get_object_definition(target_conn, source_obj.schema_name, source_obj.object_name)
                
                if source_def != target_def:
                    differences.append({
                        'object': full_name,
                        'type': source_obj.object_type,
                        'action': 'Alter',
                        'source': source_def,
                        'target': target_def
                    })
                    
        # Check for objects that exist in target but not in source
        source_dict = {
            f"{obj.schema_name}.{obj.object_name}": obj 
            for obj in source_objects
        }
        
        for target_obj in target_objects:
            full_name = f"{target_obj.schema_name}.{target_obj.object_name}"
            
            if full_name not in source_dict:
                differences.append({
                    'object': full_name,
                    'type': target_obj.object_type,
                    'action': 'Drop',
                    'source': '',
                    'target': self.get_object_definition(target_conn, target_obj.schema_name, target_obj.object_name)
                })
                
        return differences
