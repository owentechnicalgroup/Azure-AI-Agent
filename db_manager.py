from datetime import datetime, timedelta
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.sql import func
import logging
import pyodbc
from models import ChatMessage, ChatRole, Base

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self, connection_string, application_name):
        """Initialize database manager with connection string and application name."""
        self.engine = create_engine(connection_string)
        self.Session = sessionmaker(bind=self.engine)
        self.application_name = application_name
        
        # Use the same connection string that worked in test_connection.py
        conn_str = (
            "DRIVER={SQL Server};"
            "SERVER=localhost,1433;"
            "DATABASE=azure_ai_chat;"
            "UID=sa;"
            "PWD=YourStrong@Passw0rd;"
            "TrustServerCertificate=yes"
        )
        
        # Create tables using raw SQL to avoid SQLAlchemy's type casting issues
        conn = pyodbc.connect(conn_str)
        cursor = conn.cursor()
        
        try:
            # Create table if it doesn't exist
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
            logger.info("Database initialized successfully")
        finally:
            cursor.close()
            conn.close()

    def log_message(self, message_content, chat_role, sequence):
        """Log a chat message to the database."""
        try:
            conn = pyodbc.connect(self.get_connection_string(database="azure_ai_chat"))
            cursor = conn.cursor()
            
            # Convert ChatRole enum to string
            chat_role_str = chat_role.value if isinstance(chat_role, ChatRole) else str(chat_role)
            
            cursor.execute("""
                INSERT INTO chat_messages (application_name, chat_role, sequence, message_content)
                VALUES (?, ?, ?, ?)
            """, (self.application_name, chat_role_str, sequence, message_content))
            
            conn.commit()
            logger.debug(f"Message logged successfully: {message_content[:50]}...")
            return True
        except Exception as e:
            logger.error(f"Error logging message: {str(e)}")
            return False
        finally:
            cursor.close()
            conn.close()

    def cleanup_old_messages(self):
        """Delete messages older than 7 days."""
        try:
            session = self.Session()
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            deleted = session.query(ChatMessage).filter(
                ChatMessage.timestamp < cutoff_date
            ).delete()
            session.commit()
            logger.info(f"Deleted {deleted} messages older than 7 days")
            return deleted
        except Exception as e:
            logger.error(f"Error cleaning up old messages: {str(e)}")
            session.rollback()
            return 0
        finally:
            session.close()

    def get_message_count(self):
        """Get the total number of messages in the database."""
        try:
            session = self.Session()
            count = session.query(ChatMessage).count()
            return count
        except Exception as e:
            logger.error(f"Error getting message count: {str(e)}")
            return 0
        finally:
            session.close()

    def get_recent_messages(self, limit=100):
        """Get the most recent messages from the database."""
        try:
            session = self.Session()
            messages = session.query(ChatMessage)\
                .order_by(ChatMessage.timestamp.desc())\
                .limit(limit)\
                .all()
            return messages
        except Exception as e:
            logger.error(f"Error getting recent messages: {str(e)}")
            return []
        finally:
            session.close()

    def get_message_count_by_role(self):
        """Get the count of messages for each role."""
        try:
            session = self.Session()
            counts = session.query(ChatMessage.chat_role, func.count(ChatMessage.id))\
                .group_by(ChatMessage.chat_role)\
                .all()
            return dict(counts)
        except Exception as e:
            logger.error(f"Error getting message count by role: {str(e)}")
            return {}
        finally:
            session.close()

    @staticmethod
    def get_connection_string(host="localhost", port=1433, database="master"):
        """Generate a connection string for SQL Server."""
        conn_str = (
            "DRIVER={SQL Server};"  # Using the installed SQL Server driver
            f"SERVER={host},{port};"
            f"DATABASE={database};"
            "UID=sa;"
            "PWD=YourStrong@Passw0rd;"
            "TrustServerCertificate=yes"
        )
        return conn_str
