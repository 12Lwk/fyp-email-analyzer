import psycopg2

# Database configuration
DB_CONFIG = {
    'dbname': 'email_db',
    'user': 'postgres',
    'password': 'email1234',  # Updated with correct password
    'host': 'localhost',
    'port': '5432'
}

def test_connection():
    """Test connection to the database"""
    conn = None
    cursor = None
    try:
        print("Connecting to database...")
        conn = psycopg2.connect(**DB_CONFIG)
        cursor = conn.cursor()
        
        # Test query
        cursor.execute("SELECT COUNT(*) FROM emails")
        count = cursor.fetchone()[0]
        print(f"\nFound {count} emails in the database")
        
        # Check table structure
        cursor.execute("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'emails'
            ORDER BY ordinal_position;
        """)
        
        print("\nTable structure:")
        for column in cursor.fetchall():
            print(f"{column[0]}: {column[1]}")
            
    except psycopg2.OperationalError as e:
        print(f"Database connection error: {str(e)}")
        print("\nPlease check your database configuration:")
        print(f"Host: {DB_CONFIG['host']}")
        print(f"Port: {DB_CONFIG['port']}")
        print(f"Database: {DB_CONFIG['dbname']}")
        print(f"User: {DB_CONFIG['user']}")
        print("\nCommon issues:")
        print("1. PostgreSQL service might not be running")
        print("2. Incorrect password")
        print("3. Database or user doesn't exist")
        print("4. Connection settings (host/port) are incorrect")
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

if __name__ == "__main__":
    test_connection() 