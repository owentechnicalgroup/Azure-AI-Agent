import pyodbc

def verify_database():
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=azure_ai_chat;"
        "UID=sa;"
        "PWD=YourStrong@Passw0rd;"
        "TrustServerCertificate=yes"
    )
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    try:
        # Check tables
        cursor.execute("SELECT TABLE_NAME FROM INFORMATION_SCHEMA.TABLES")
        print("\nTables in database:")
        tables = cursor.fetchall()
        for table in tables:
            print(table[0])
            
        # Check chat_messages table structure
        cursor.execute("""
            SELECT COLUMN_NAME, DATA_TYPE, CHARACTER_MAXIMUM_LENGTH 
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_NAME = 'chat_messages'
        """)
        print("\nColumns in chat_messages table:")
        columns = cursor.fetchall()
        for col in columns:
            max_length = col[2] if col[2] is not None else 'n/a'
            print(f"{col[0]}: {col[1]}({max_length})")
            
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    verify_database()
