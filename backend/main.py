"""FastAPI application for QueryLens."""
from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, HTTPException, Request, Response, Query
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pathlib import Path
import json
from typing import Optional, Any, List
import logging
from pydantic import BaseModel, Field, validator
from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from config import FRONTEND_URL, ALLOW_CLIENT_LLM_CONFIG

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Setup rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"],
    storage_uri="memory://"
)
from database import (
    import_csv,
    execute_query,
    get_tables,
    get_table_schema,
    get_sample_data,
    save_query_history,
    export_table_data,
    explain_query_plan,
    DATA_DIR,
    MAX_QUERY_ROWS,
    MAX_HISTORY_LIMIT,
    is_valid_identifier,
)
from llm import generate_sql_from_nl, validate_sql
from models import SessionLocal, UploadedFile, QueryHistory
from health import HealthChecker, get_database_stats
from error_handlers import (
    querylens_exception_handler,
    validation_exception_handler,
    http_exception_handler,
    generic_exception_handler,
    QueryLensException,
)


# Pydantic models for request validation
class ColumnDefinition(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    type: str = Field(..., pattern=r'^(TEXT|INTEGER|REAL|BOOLEAN|DATE)$')

    @validator('name')
    def name_must_be_valid(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Column name can only contain letters, numbers, and underscores')
        return v.lower()


class CreateTableRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    columns: List[ColumnDefinition] = Field(..., min_items=1, max_items=100)

    @validator('name')
    def table_name_must_be_valid(cls, v):
        if not v.replace('_', '').isalnum():
            raise ValueError('Table name can only contain letters, numbers, and underscores')
        if v[0].isdigit():
            raise ValueError('Table name cannot start with a number')
        return v.lower()

    @validator('columns')
    def columns_must_be_unique(cls, v):
        names = [col.name for col in v]
        if len(names) != len(set(names)):
            raise ValueError('Column names must be unique')
        return v


class QueryRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=5000)
    table_name: str = Field(..., min_length=1, max_length=255)
    execute: bool = False
    limit: int = Field(100, ge=1, le=MAX_QUERY_ROWS)
    offset: int = Field(0, ge=0, le=100000)
    gemini_api_key: Optional[str] = Field(
        None,
        max_length=512,
        description="Optional. Requires ALLOW_CLIENT_LLM_CONFIG=true; otherwise ignored.",
    )
    gemini_model: Optional[str] = Field(
        None,
        max_length=128,
        description="Optional. Requires ALLOW_CLIENT_LLM_CONFIG=true; otherwise ignored.",
    )


class ExplainRequest(BaseModel):
    sql: str = Field(..., min_length=1, max_length=5000)
    table_name: str = Field(..., min_length=1, max_length=255)

    @validator('table_name')
    def validate_table_name(cls, v):
        if not is_valid_identifier(v):
            raise ValueError('Invalid table name format')
        return v


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context for startup/shutdown."""
    yield


app = FastAPI(
    title="QueryLens API",
    description="Natural Language SQL Query Builder",
    version="1.0.0",
    lifespan=lifespan
)

# Add rate limiter to app
app.state.limiter = limiter

# Register exception handlers
app.add_exception_handler(RateLimitExceeded, lambda request, exc: JSONResponse(
    status_code=429,
    content={"error": {"code": "RATE_LIMITED", "message": "Rate limit exceeded. Please try again later."}}
))
app.add_exception_handler(QueryLensException, querylens_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(Exception, generic_exception_handler)

# Security headers middleware
@app.middleware("http")
async def add_security_headers(request, call_next):
    """Add security headers to all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["Content-Security-Policy"] = "default-src 'self'"
    return response

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)


@app.get("/")
@app.get("/health")
@limiter.limit("100/minute")
async def health_check(request: Request) -> dict[str, str]:
    """Health check endpoint."""
    return {
        "status": "healthy",
        "message": "QueryLens API running",
        "version": "1.0.0"
    }


@app.post("/upload")
@limiter.limit("10/minute")
async def upload_file(request: Request, file: UploadFile = File(...)) -> dict[str, Any]:
    """Upload and import CSV file."""
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be CSV")
    
    try:
        logger.info(f"Uploading file: {file.filename}")
        
        # Save file temporarily
        file_path = DATA_DIR / file.filename
        with open(file_path, "wb") as f:
            contents = await file.read()
            f.write(contents)
        
        # Generate table name from filename
        table_name = file.filename.replace(".csv", "").replace("-", "_").lower()
        
        # Import into database
        result = import_csv(str(file_path), table_name)
        
        if "error" in result:
            logger.error(f"Import error: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        logger.info(f"Successfully imported {table_name} with {result.get('row_count')} rows")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/create-table")
@limiter.limit("20/minute")
async def create_table(request: Request, payload: CreateTableRequest) -> dict[str, Any]:
    """Create a new table with specified schema."""
    try:
        logger.info(f"Creating table: {payload.name} with {len(payload.columns)} columns")
        
        from database import create_table as db_create_table
        result = db_create_table(payload.name, payload.columns)
        
        if "error" in result:
            logger.error(f"Table creation error: {result['error']}")
            raise HTTPException(status_code=400, detail=result["error"])
        
        # Store metadata in database
        db = SessionLocal()
        try:
            existing = db.query(UploadedFile).filter_by(table_name=payload.name).first()
            if existing:
                existing.columns = json.dumps([{"name": col.name, "type": col.type} for col in payload.columns])
                existing.row_count = 0
            else:
                uploaded_file = UploadedFile(
                    filename=f"{payload.name}_manual.csv",
                    table_name=payload.name,
                    original_name=f"{payload.name}_manual",
                    row_count=0,
                    columns=json.dumps([{"name": col.name, "type": col.type} for col in payload.columns]),
                )
                db.add(uploaded_file)
            db.commit()
        finally:
            db.close()
        
        logger.info(f"Successfully created table {payload.name}")
        return {
            "success": True,
            "table_name": payload.name,
            "columns": [{"name": col.name, "type": col.type} for col in payload.columns],
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create table error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/tables")
async def list_tables():
    """Get list of all available tables."""
    tables = get_tables()
    
    # Get metadata from database
    db = SessionLocal()
    metadata = {}
    for file_record in db.query(UploadedFile).all():
        metadata[file_record.table_name] = {
            "original_name": file_record.original_name,
            "row_count": file_record.row_count,
            "columns": json.loads(file_record.columns),
        }
    db.close()
    
    return {
        "tables": tables,
        "metadata": metadata,
    }


@app.get("/schema/{table_name}")
async def get_schema(table_name: str):
    """Get schema for a specific table."""
    if not is_valid_identifier(table_name):
        raise HTTPException(status_code=400, detail={"code": "INVALID_TABLE", "message": "Invalid table name"})
    
    schema = get_table_schema(table_name)
    
    if "error" in schema:
        raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": schema["error"]})
    
    return schema


@app.post("/query")
@limiter.limit("30/minute")
async def natural_language_query(request: Request, payload: QueryRequest) -> dict[str, Any]:
    """Convert natural language to SQL and optionally execute."""
    nl_query = payload.query.strip()
    table_name = payload.table_name.strip()
    execute = payload.execute
    
    logger.info(f"Processing query: {nl_query[:50]}... for table: {table_name}")
    
    try:
        # Get table schema
        schema = get_table_schema(table_name)
        if "error" in schema:
            raise HTTPException(status_code=404, detail={"code": "NOT_FOUND", "message": "Table not found"})
        
        # Get sample data for context
        sample_data = get_sample_data(table_name)
        
        # Generate SQL (optional per-request Gemini credentials from client)
        sql = generate_sql_from_nl(
            nl_query,
            table_name,
            schema["columns"],
            sample_data,
            api_key=payload.gemini_api_key if ALLOW_CLIENT_LLM_CONFIG else None,
            model=payload.gemini_model if ALLOW_CLIENT_LLM_CONFIG else None,
        )
        
        if sql.startswith("ERROR:"):
            error_msg = sql.replace("ERROR: ", "")
            logger.error(f"LLM error: {error_msg}")
            return {"success": False, "error": f"LLM error: {error_msg}"}
        
        if sql == "INVALID_QUERY":
            logger.warning(f"LLM returned invalid query for: {nl_query[:50]}")
            return {"success": False, "error": "The query cannot be answered with the available data"}
        
        # Validate SQL safety
        is_safe, error = validate_sql(sql, allowed_tables={table_name})
        if not is_safe:
            logger.warning(f"SQL validation failed: {error}")
            return {"success": False, "error": error}
        
        logger.info(f"Generated SQL: {sql[:100]}...")
        
        # Save to history
        save_query_history(nl_query, sql, table_name)
        
        # Execute if requested
        if execute:
            result = execute_query(sql, table_name, limit=payload.limit, offset=payload.offset)
            if "error" in result:
                logger.error(f"Execution error: {result['error']}")
                save_query_history(nl_query, sql, table_name, executed=False, error=result["error"])
                return {
                    "success": False,
                    "sql": sql,
                    "error": f"Execution error: {result['error']}",
                }
            
            logger.info(f"Query executed successfully, returned {result.get('row_count')} rows")
            save_query_history(nl_query, sql, table_name, executed=True)
            return {
                "success": True,
                "sql": sql,
                "results": result,
            }
        
        return {
            "success": True,
            "sql": sql,
            "preview": True,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/history")
async def get_history(table_name: Optional[str] = None, limit: int = 50):
    """Get query history."""
    safe_limit = max(1, min(limit, MAX_HISTORY_LIMIT))
    db = SessionLocal()
    query = db.query(QueryHistory)
    
    if table_name:
        if not is_valid_identifier(table_name):
            raise HTTPException(status_code=400, detail={"code": "INVALID_TABLE", "message": "Invalid table name"})
        query = query.filter(QueryHistory.table_name == table_name)
    
    records = query.order_by(QueryHistory.created_at.desc()).limit(safe_limit).all()
    
    history = [
        {
            "id": r.id,
            "natural_language": r.natural_language,
            "generated_sql": r.generated_sql,
            "table_name": r.table_name,
            "executed": bool(r.executed),
            "error": r.error,
            "created_at": r.created_at.isoformat(),
        }
        for r in records
    ]
    
    db.close()
    return {"history": history, "limit": safe_limit}


@app.get("/health/full")
@limiter.limit("100/minute")
async def full_health_check(request: Request) -> dict:
    """Perform full health check."""
    return HealthChecker.full_health_check()


@app.get("/health/ready")
@limiter.limit("100/minute")
async def readiness_check(request: Request) -> dict:
    """Readiness check - is the service ready to accept traffic."""
    checks = HealthChecker.full_health_check()
    if checks["overall_status"] == "healthy":
        return {"ready": True, "status": "ready"}
    return {"ready": False, "status": checks["overall_status"]}


@app.get("/stats")
@limiter.limit("50/minute")
async def get_stats(request: Request) -> dict:
    """Get database statistics."""
    return {
        "database": get_database_stats(),
    }


@app.get("/export/{table_name}")
@limiter.limit("30/minute")
async def export_table(
    request: Request,
    table_name: str,
    format: str = Query("csv", pattern=r"^(csv|json)$"),
    limit: int = Query(1000, ge=1, le=10000),
    offset: int = Query(0, ge=0)
):
    """Export table data as CSV file download or structured JSON records."""
    if not is_valid_identifier(table_name):
        raise HTTPException(status_code=400, detail="Invalid table name")

    tables = get_tables()
    if table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Table '{table_name}' not found")

    result = export_table_data(table_name, format=format, limit=limit, offset=offset)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    if format == "csv":
        return Response(
            content=result["content"],
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{table_name}.csv"'}
        )
    return JSONResponse(content={
        "table_name": table_name,
        "row_count": result["row_count"],
        "data": result["data"]
    })


@app.post("/explain")
@limiter.limit("30/minute")
async def explain_query(request: Request, payload: ExplainRequest) -> dict[str, Any]:
    """Analyze and explain a SQL query execution plan."""
    tables = get_tables()
    if payload.table_name not in tables:
        raise HTTPException(status_code=404, detail=f"Table '{payload.table_name}' not found")

    is_valid, validation_error = validate_sql(payload.sql, {payload.table_name})
    if not is_valid:
        raise HTTPException(status_code=400, detail=validation_error or "Invalid SQL query")

    result = explain_query_plan(payload.sql, payload.table_name)
    if "error" in result:
        raise HTTPException(status_code=400, detail=result["error"])

    return result


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
