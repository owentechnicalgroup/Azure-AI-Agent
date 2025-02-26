import pyodbc
from db_manager import DatabaseManager

def init_database():
    # Get the connection string
    conn_str = DatabaseManager.get_connection_string()
    
    # Connect to SQL Server
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    
    try:
        # Create database if it doesn't exist
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'azure_ai_chat')
        BEGIN
            CREATE DATABASE azure_ai_chat
        END
        """)
        conn.commit()
        
        # Switch to azure_ai_chat database
        conn.close()
        conn_str = conn_str.replace("DATABASE=master;", "DATABASE=azure_ai_chat;")
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        # Create chat_messages table if it doesn't exist
        cursor.execute("""
        IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'chat_messages')
        BEGIN
            CREATE TABLE chat_messages (
                id INT IDENTITY(1,1) PRIMARY KEY,
                application_name NVARCHAR(100) NOT NULL,
                chat_role NVARCHAR(20) NOT NULL,
                sequence INT NOT NULL,
                timestamp DATETIME NOT NULL DEFAULT GETDATE(),
                message_content NVARCHAR(4000) NOT NULL
            )
        END
        """)
        conn.commit()
        print("Database and tables created successfully!")
        
    except Exception as e:
        print(f"Error: {str(e)}")
        raise
    finally:
        cursor.close()
        conn.close()

if __name__ == "__main__":
    init_database()
