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
                # Build connection string with timeout
                if auth_type == "Windows Authentication":
                    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};Trusted_Connection=yes;Connection Timeout=30;'
                else:
                    if not username or not password:
                        raise ConnectionError("Username and password are required for SQL Server Authentication")
                    conn_str = f'DRIVER={{SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password};Connection Timeout=30;'
                
                conn = pyodbc.connect(conn_str)
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                return conn
                
            except pyodbc.OperationalError as e:
                last_error = ConnectionError(f"Failed to connect to server {server}: {str(e)}")
                if "Network-related" in str(e) and attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay)
                    continue
                break
            except pyodbc.Error as e:
                last_error = ConnectionError(f"Database error on {server}: {str(e)}")
                break
            except Exception as e:
                last_error = ConnectionError(f"Unexpected error connecting to {server}: {str(e)}")
                break
                
        raise last_error or ConnectionError(f"Failed to connect to {server} after {self.max_retries} attempts")

    def execute_query(self, connection: pyodbc.Connection, query: str, params: tuple = None) -> List[Dict]:
        """Execute a query with error handling"""
        try:
            connection.timeout = 30
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
        finally:
            if 'cursor' in locals():
                cursor.close()

    def get_schema_objects(self, connection: pyodbc.Connection) -> List[Dict]:
        """Get database objects following DACFx model"""
        objects_query = """
        SELECT 
            SCHEMA_NAME(o.schema_id) as schema_name,
            o.name as object_name,
            CASE o.type
                WHEN 'P' THEN 'Stored Procedure'
                WHEN 'U' THEN 'Table'
                WHEN 'V' THEN 'View'
                WHEN 'FN' THEN 'Function'
                WHEN 'TR' THEN 'Trigger'
                WHEN 'IF' THEN 'Function'
                WHEN 'TF' THEN 'Function'
                WHEN 'UQ' THEN 'Unique Constraint'
                WHEN 'F' THEN 'Foreign Key'
                WHEN 'PK' THEN 'Primary Key'
                WHEN 'D' THEN 'Default Constraint'
                ELSE o.type_desc
            END as object_type,
            o.type as type_code,
            o.object_id,
            o.create_date,
            o.modify_date,
            OBJECTPROPERTY(o.object_id, 'ExecIsAnsiNullsOn') as is_ansi_nulls_on,
            OBJECTPROPERTY(o.object_id, 'ExecIsQuotedIdentOn') as is_quoted_identifier_on
        FROM sys.objects o
        WHERE o.type IN ('P', 'U', 'V', 'FN', 'TR', 'IF', 'TF', 'UQ', 'F', 'PK', 'D')
          AND o.is_ms_shipped = 0
        ORDER BY 
            CASE o.type 
                WHEN 'U' THEN 1  -- Tables first
                WHEN 'PK' THEN 2 -- Then primary keys
                WHEN 'F' THEN 3  -- Then foreign keys
                WHEN 'UQ' THEN 4 -- Then unique constraints
                WHEN 'D' THEN 5  -- Then defaults
                WHEN 'TR' THEN 6 -- Then triggers
                ELSE 10         -- Then everything else
            END,
            SCHEMA_NAME(o.schema_id),
            o.name
        """
        return self.execute_query(connection, objects_query)

    def get_table_columns(self, connection: pyodbc.Connection, table_id: int) -> List[Dict]:
        """Get detailed column information following DACFx model"""
        columns_query = """
        SELECT 
            c.name as column_name,
            t.name as data_type,
            c.max_length,
            c.precision,
            c.scale,
            c.is_nullable,
            c.is_identity,
            c.is_computed,
            c.is_rowguidcol,
            c.column_id as ordinal_position,
            c.collation_name,
            cc.definition as computed_definition,
            dc.definition as default_definition,
            COLUMNPROPERTY(c.object_id, c.name, 'IsIdentity') as is_identity,
            COLUMNPROPERTY(c.object_id, c.name, 'IsComputed') as is_computed,
            ic.seed_value as identity_seed,
            ic.increment_value as identity_increment,
            t.is_user_defined
        FROM sys.columns c
        INNER JOIN sys.types t ON c.user_type_id = t.user_type_id
        LEFT JOIN sys.computed_columns cc ON c.object_id = cc.object_id AND c.column_id = cc.column_id
        LEFT JOIN sys.default_constraints dc ON c.object_id = dc.parent_object_id AND c.column_id = dc.parent_column_id
        LEFT JOIN sys.identity_columns ic ON c.object_id = ic.object_id AND c.column_id = ic.column_id
        WHERE c.object_id = ?
        ORDER BY c.column_id
        """
        return self.execute_query(connection, columns_query, (table_id,))

    def get_table_indexes(self, connection: pyodbc.Connection, table_id: int) -> List[Dict]:
        """Get table indexes following DACFx model"""
        indexes_query = """
        SELECT 
            i.name as index_name,
            i.type_desc as index_type,
            i.is_unique,
            i.is_primary_key,
            i.is_unique_constraint,
            i.fill_factor,
            i.is_padded,
            i.allow_row_locks,
            i.allow_page_locks,
            i.has_filter,
            i.filter_definition,
            STRING_AGG(c.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) as columns
        FROM sys.indexes i
        INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
        INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
        WHERE i.object_id = ?
        GROUP BY 
            i.name, i.type_desc, i.is_unique, i.is_primary_key, i.is_unique_constraint,
            i.fill_factor, i.is_padded, i.allow_row_locks, i.allow_page_locks, 
            i.has_filter, i.filter_definition
        """
        return self.execute_query(connection, indexes_query, (table_id,))

    def get_foreign_keys(self, connection: pyodbc.Connection, table_id: int) -> List[Dict]:
        """Get foreign keys following DACFx model"""
        fk_query = """
        SELECT 
            fk.name as constraint_name,
            OBJECT_SCHEMA_NAME(fk.referenced_object_id) as referenced_schema,
            OBJECT_NAME(fk.referenced_object_id) as referenced_table,
            STRING_AGG(pc.name, ', ') WITHIN GROUP (ORDER BY fkc.constraint_column_id) as parent_columns,
            STRING_AGG(rc.name, ', ') WITHIN GROUP (ORDER BY fkc.constraint_column_id) as referenced_columns,
            fk.delete_referential_action_desc as on_delete,
            fk.update_referential_action_desc as on_update,
            fk.is_disabled
        FROM sys.foreign_keys fk
        INNER JOIN sys.foreign_key_columns fkc ON fk.object_id = fkc.constraint_object_id
        INNER JOIN sys.columns pc ON fkc.parent_object_id = pc.object_id AND fkc.parent_column_id = pc.column_id
        INNER JOIN sys.columns rc ON fkc.referenced_object_id = rc.object_id AND fkc.referenced_column_id = rc.column_id
        WHERE fk.parent_object_id = ?
        GROUP BY 
            fk.name, fk.referenced_object_id, fk.delete_referential_action_desc,
            fk.update_referential_action_desc, fk.is_disabled
        """
        return self.execute_query(connection, fk_query, (table_id,))

    def get_object_definition(self, connection: pyodbc.Connection, object_id: int) -> str:
        """Get object definition with additional properties"""
        def_query = """
        SELECT 
            OBJECT_DEFINITION(?) as definition,
            OBJECTPROPERTY(?, 'ExecIsAnsiNullsOn') as is_ansi_nulls_on,
            OBJECTPROPERTY(?, 'ExecIsQuotedIdentOn') as is_quoted_identifier_on
        """
        result = self.execute_query(connection, def_query, (object_id, object_id, object_id))
        if result:
            props = []
            if result[0]['is_ansi_nulls_on']:
                props.append('SET ANSI_NULLS ON')
            if result[0]['is_quoted_identifier_on']:
                props.append('SET QUOTED_IDENTIFIER ON')
            
            definition = result[0]['definition']
            if props and definition:
                return '\n'.join(props) + '\nGO\n\n' + definition
            return definition or ""
        return ""

    def compare_schemas(self, source_conn: pyodbc.Connection, target_conn: pyodbc.Connection) -> List[Dict]:
        """Compare schemas between databases following DACFx model"""
        source_objects = {f"{obj['schema_name']}.{obj['object_name']}": obj 
                         for obj in self.get_schema_objects(source_conn)}
        target_objects = {f"{obj['schema_name']}.{obj['object_name']}": obj 
                         for obj in self.get_schema_objects(target_conn)}
        
        differences = []
        
        # Compare all objects
        for name, source_obj in source_objects.items():
            if name not in target_objects:
                differences.append({
                    "object": name,
                    "type": source_obj['object_type'],
                    "action": "Create",
                    "source_details": source_obj,
                    "target_details": None
                })
            else:
                target_obj = target_objects[name]
                if source_obj['type_code'] != target_obj['type_code']:
                    differences.append({
                        "object": name,
                        "type": source_obj['object_type'],
                        "action": "Different",
                        "difference": "Object types do not match",
                        "source_details": source_obj,
                        "target_details": target_obj
                    })
                    continue

                # Compare based on object type
                if source_obj['object_type'] == 'Table':
                    source_cols = self.get_table_columns(source_conn, source_obj['object_id'])
                    target_cols = self.get_table_columns(target_conn, target_obj['object_id'])
                    source_idx = self.get_table_indexes(source_conn, source_obj['object_id'])
                    target_idx = self.get_table_indexes(target_conn, target_obj['object_id'])
                    source_fks = self.get_foreign_keys(source_conn, source_obj['object_id'])
                    target_fks = self.get_foreign_keys(target_conn, target_obj['object_id'])
                    
                    # Compare columns
                    if self._compare_columns(source_cols, target_cols):
                        differences.append({
                            "object": name,
                            "type": "Table",
                            "action": "Different",
                            "difference": "Columns are different",
                            "source_details": source_cols,
                            "target_details": target_cols
                        })
                    
                    # Compare indexes
                    if self._compare_indexes(source_idx, target_idx):
                        differences.append({
                            "object": name,
                            "type": "Table",
                            "action": "Different",
                            "difference": "Indexes are different",
                            "source_details": source_idx,
                            "target_details": target_idx
                        })
                    
                    # Compare foreign keys
                    if self._compare_foreign_keys(source_fks, target_fks):
                        differences.append({
                            "object": name,
                            "type": "Table",
                            "action": "Different",
                            "difference": "Foreign keys are different",
                            "source_details": source_fks,
                            "target_details": target_fks
                        })
                
                else:
                    # Compare other objects by definition
                    source_def = self.get_object_definition(source_conn, source_obj['object_id'])
                    target_def = self.get_object_definition(target_conn, target_obj['object_id'])
                    
                    if source_def != target_def:
                        differences.append({
                            "object": name,
                            "type": source_obj['object_type'],
                            "action": "Different",
                            "difference": "Definitions are different",
                            "source_details": source_def,
                            "target_details": target_def
                        })
        
        # Find objects that exist only in target
        for name, target_obj in target_objects.items():
            if name not in source_objects:
                differences.append({
                    "object": name,
                    "type": target_obj['object_type'],
                    "action": "Drop",
                    "source_details": None,
                    "target_details": target_obj
                })
        
        return differences

    def _compare_columns(self, source_cols: List[Dict], target_cols: List[Dict]) -> bool:
        """Compare columns and their properties"""
        if len(source_cols) != len(target_cols):
            return True
            
        source_dict = {col['column_name']: col for col in source_cols}
        target_dict = {col['column_name']: col for col in target_cols}
        
        if source_dict.keys() != target_dict.keys():
            return True
            
        for name, source_col in source_dict.items():
            target_col = target_dict[name]
            
            # Compare all relevant properties
            compare_props = ['data_type', 'max_length', 'precision', 'scale', 'is_nullable',
                           'is_identity', 'is_computed', 'is_rowguidcol', 'ordinal_position',
                           'computed_definition', 'default_definition', 'identity_seed',
                           'identity_increment']
                           
            for prop in compare_props:
                if source_col.get(prop) != target_col.get(prop):
                    return True
                    
        return False

    def _compare_indexes(self, source_idx: List[Dict], target_idx: List[Dict]) -> bool:
        """Compare indexes and their properties"""
        if len(source_idx) != len(target_idx):
            return True
            
        source_dict = {idx['index_name']: idx for idx in source_idx}
        target_dict = {idx['index_name']: idx for idx in target_idx}
        
        if source_dict.keys() != target_dict.keys():
            return True
            
        for name, source_index in source_dict.items():
            target_index = target_dict[name]
            
            compare_props = ['index_type', 'is_unique', 'is_primary_key', 'is_unique_constraint',
                           'fill_factor', 'is_padded', 'allow_row_locks', 'allow_page_locks',
                           'has_filter', 'filter_definition', 'columns']
                           
            for prop in compare_props:
                if source_index.get(prop) != target_index.get(prop):
                    return True
                    
        return False

    def _compare_foreign_keys(self, source_fks: List[Dict], target_fks: List[Dict]) -> bool:
        """Compare foreign keys and their properties"""
        if len(source_fks) != len(target_fks):
            return True
            
        source_dict = {fk['constraint_name']: fk for fk in source_fks}
        target_dict = {fk['constraint_name']: fk for fk in target_fks}
        
        if source_dict.keys() != target_dict.keys():
            return True
            
        for name, source_fk in source_dict.items():
            target_fk = target_dict[name]
            
            compare_props = ['referenced_schema', 'referenced_table', 'parent_columns',
                           'referenced_columns', 'on_delete', 'on_update', 'is_disabled']
                           
            for prop in compare_props:
                if source_fk.get(prop) != target_fk.get(prop):
                    return True
                    
        return False
