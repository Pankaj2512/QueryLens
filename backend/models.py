"""SQLAlchemy models for QueryLens."""
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from config import DATABASE_URL

Base = declarative_base()


class UploadedFile(Base):
    """Store information about uploaded CSV files."""
    __tablename__ = "uploaded_files"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), unique=True, nullable=False)
    original_name = Column(String(255), nullable=False)
    table_name = Column(String(255), unique=True, nullable=False)
    columns = Column(Text, nullable=False)  # JSON string of column info
    row_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)


class QueryHistory(Base):
    """Store query history for reference."""
    __tablename__ = "query_history"

    id = Column(Integer, primary_key=True)
    natural_language = Column(Text, nullable=False)
    generated_sql = Column(Text, nullable=False)
    table_name = Column(String(255), nullable=False)
    executed = Column(Integer, default=0)  # 0 or 1 for SQLite
    error = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


# Create engine and tables
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base.metadata.create_all(bind=engine)


def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
