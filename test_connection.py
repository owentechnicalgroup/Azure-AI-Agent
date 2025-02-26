import pyodbc

def test_connection():
    conn_str = (
        "DRIVER={SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=azure_ai_chat;"
        "UID=sa;"
        "PWD=YourStrong@Passw0rd;"
        "TrustServerCertificate=yes"
    )
    
    try:
        print("Attempting to connect...")
        conn = pyodbc.connect(conn_str)
        print("Connection successful!")
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        row = cursor.fetchone()
        print(f"SQL Server version: {row[0]}")
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_connection()
