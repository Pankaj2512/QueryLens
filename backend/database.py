"""Database utilities for CSV import and query execution."""
import json
import re
from pathlib import Path
from typing import Any, List
import pandas as pd
from sqlalchemy import inspect, text, MetaData, Table, Column, String, Integer, Float, Boolean, Date
from models import engine, SessionLocal, UploadedFile, QueryHistory
from config import DB_PATH

# Data directory for uploaded CSV files
DATA_DIR = Path(__file__).parent.parent / "data" / "uploads"
DATA_DIR.mkdir(parents=True, exist_ok=True)

MAX_QUERY_ROWS = 200
MAX_HISTORY_LIMIT = 200
_IDENTIFIER_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def is_valid_identifier(value: str) -> bool:
    """Return True when identifier is safe for SQL object names."""
    return bool(_IDENTIFIER_RE.match(value))


def create_table(table_name: str, columns: List[dict]) -> dict[str, Any]:
    """Create a new table with specified schema."""
    try:
        # Type mapping
        type_map = {
            "TEXT": String,
            "INTEGER": Integer,
            "REAL": Float,
            "BOOLEAN": Boolean,
            "DATE": Date,
        }
        
        # Create column definitions
        col_definitions = []
        for col in columns:
            col_name = col.get("name", "").lower()
            col_type = col.get("type", "TEXT").upper()
            
            if col_type not in type_map:
                return {"error": f"Invalid type: {col_type}"}
            
            col_definitions.append(
                Column(col_name, type_map[col_type], nullable=True)
            )
        
        # Create table
        metadata = MetaData()
        table = Table(table_name, metadata, *col_definitions)
        metadata.create_all(engine)
        
        return {
            "success": True,
            "table_name": table_name,
            "columns": columns,
        }
    except Exception as e:
        return {"error": str(e)}


def import_csv(filepath: str, table_name: str) -> dict[str, Any]:
    """Import CSV file into database."""
    try:
        df = pd.read_csv(filepath)
        
        # Validate table name
        if not table_name.replace("_", "").isalnum():
            return {"error": "Invalid table name"}
        
        # Store in database
        df.to_sql(table_name, engine, if_exists="replace", index=False)
        
        # Get column info
        columns = [
            {"name": col, "type": str(df[col].dtype)}
            for col in df.columns
        ]
        
        # Save metadata
        db = SessionLocal()
        file_record = UploadedFile(
            filename=Path(filepath).name,
            original_name=Path(filepath).name,
            table_name=table_name,
            columns=json.dumps(columns),
            row_count=len(df),
        )
        db.add(file_record)
        db.commit()
        db.refresh(file_record)
        db.close()
        
        return {
            "success": True,
            "table_name": table_name,
            "columns": columns,
            "row_count": len(df),
        }
    except Exception as e:
        return {"error": str(e)}


def execute_query(sql: str, table_name: str, limit: int = MAX_QUERY_ROWS, offset: int = 0) -> dict[str, Any]:
    """Execute SQL query and return results."""
    try:
        effective_limit = max(1, min(limit, MAX_QUERY_ROWS))
        effective_offset = max(0, offset)
        paginated_sql = f"""
SELECT * FROM (
{sql.strip().rstrip(';')}
) AS querylens_subquery
LIMIT {effective_limit} OFFSET {effective_offset}
"""
        with engine.connect() as conn:
            result = conn.execute(text(paginated_sql))
            rows = result.fetchall()
            columns = result.keys()
            
            # Convert to list of dicts
            data = [dict(zip(columns, row)) for row in rows]
            
            return {
                "success": True,
                "data": data,
                "columns": list(columns),
                "row_count": len(data),
                "limit": effective_limit,
                "offset": effective_offset,
                "has_more": len(data) == effective_limit,
            }
    except Exception as e:
        return {"error": str(e)}


def get_tables() -> list[str]:
    """Get list of all tables in database."""
    try:
        inspector = inspect(engine)
        return inspector.get_table_names()
    except Exception:
        return []


def get_table_schema(table_name: str) -> dict[str, Any]:
    """Get schema info for a table."""
    try:
        inspector = inspect(engine)
        columns = inspector.get_columns(table_name)
        
        return {
            "table_name": table_name,
            "columns": [
                {"name": col["name"], "type": str(col["type"])}
                for col in columns
            ],
        }
    except Exception as e:
        return {"error": str(e)}


def get_sample_data(table_name: str, limit: int = 5) -> str:
    """Get sample data from a table as formatted string."""
    try:
        if not is_valid_identifier(table_name):
            return ""
        capped_limit = max(1, min(limit, 20))
        df = pd.read_sql(text(f"SELECT * FROM {table_name} LIMIT :limit"), engine, params={"limit": capped_limit})
        return df.to_string(index=False)
    except Exception:
        return ""


def save_query_history(
    natural_language: str,
    generated_sql: str,
    table_name: str,
    executed: bool = False,
    error: str = None,
):
    """Save query to history."""
    db = SessionLocal()
    history = QueryHistory(
        natural_language=natural_language,
        generated_sql=generated_sql,
        table_name=table_name,
        executed=1 if executed else 0,
        error=error,
    )
    db.add(history)
    db.commit()
    db.close()


def export_table_data(
    table_name: str,
    format: str = "csv",
    limit: int = 1000,
    offset: int = 0
) -> dict[str, Any]:
    """Export table data as CSV string or structured JSON records."""
    if not is_valid_identifier(table_name):
        return {"error": "Invalid table name"}
    try:
        effective_limit = max(1, min(limit, 10000))
        effective_offset = max(0, offset)
        df = pd.read_sql(
            text(f"SELECT * FROM {table_name} LIMIT :limit OFFSET :offset"),
            engine,
            params={"limit": effective_limit, "offset": effective_offset}
        )
        if format.lower() == "csv":
            content = df.to_csv(index=False)
            return {"success": True, "format": "csv", "content": content, "row_count": len(df)}
        elif format.lower() == "json":
            content = df.to_dict(orient="records")
            return {"success": True, "format": "json", "data": content, "row_count": len(df)}
        else:
            return {"error": f"Unsupported format '{format}'. Supported formats: 'csv', 'json'"}
    except Exception as e:
        return {"error": str(e)}
