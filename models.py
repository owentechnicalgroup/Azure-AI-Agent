from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Enum, create_engine, MetaData
from sqlalchemy.dialects.mssql import NVARCHAR
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

# Configure the MetaData with naming convention
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=naming_convention)
Base = declarative_base(metadata=metadata)

class ChatRole(enum.Enum):
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    application_name = Column(NVARCHAR(100), nullable=False)
    chat_role = Column(String(20), nullable=False)
    sequence = Column(Integer, nullable=False)
    timestamp = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    message_content = Column(NVARCHAR(4000), nullable=False)

    def __repr__(self):
        return f"<ChatMessage(id={self.id}, role={self.chat_role}, sequence={self.sequence})>"

def init_db(connection_string):
    """Initialize the database and create tables."""
    engine = create_engine(connection_string)
    Base.metadata.create_all(engine)
    return engine
