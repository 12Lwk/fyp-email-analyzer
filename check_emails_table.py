import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Database connection parameters
db_params = {
    'dbname': 'email_db',
    'user': 'postgres',
    'password': 'email1234',
    'host': 'localhost',
    'port': '5432'
}

try:
    # Connect to the database
    conn = psycopg2.connect(**db_params)
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    
    # Query to get detailed information about the emails table
    cur.execute("""
        SELECT 
            column_name,
            data_type,
            character_maximum_length,
            column_default,
            is_nullable
        FROM information_schema.columns
        WHERE table_name = 'emails'
        ORDER BY ordinal_position;
    """)
    
    columns = cur.fetchall()
    
    print("\nEmails Table Structure:")
    print("=======================")
    for col in columns:
        col_name, data_type, max_length, default, nullable = col
        type_info = f"{data_type}"
        if max_length:
            type_info += f"({max_length})"
        nullable_info = "NULL" if nullable == "YES" else "NOT NULL"
        default_info = f" DEFAULT {default}" if default else ""
        print(f"- {col_name}: {type_info} {nullable_info}{default_info}")
    
    # Get indexes
    cur.execute("""
        SELECT
            i.relname as index_name,
            a.attname as column_name
        FROM
            pg_class t,
            pg_class i,
            pg_index ix,
            pg_attribute a
        WHERE
            t.oid = ix.indrelid
            and i.oid = ix.indexrelid
            and a.attrelid = t.oid
            and a.attnum = ANY(ix.indkey)
            and t.relkind = 'r'
            and t.relname = 'emails'
        ORDER BY
            i.relname;
    """)
    
    indexes = cur.fetchall()
    if indexes:
        print("\nIndexes:")
        print("========")
        for idx in indexes:
            print(f"- {idx[0]} on column {idx[1]}")
    
except Exception as e:
    print(f"Error: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close() 