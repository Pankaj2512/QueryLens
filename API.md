# QueryLens API Documentation

## Overview

QueryLens API is a RESTful API built with FastAPI for converting natural language queries to SQL and executing them safely against uploaded CSV datasets.

## Base URL

```
http://localhost:8000
```

## Endpoints

### Health Check

```http
GET /
```

**Response:**
```json
{
  "status": "healthy",
  "message": "QueryLens API running",
  "version": "1.0.0"
}
```

---

### Upload File

Upload a CSV file to create a queryable table.

```http
POST /upload
Content-Type: multipart/form-data

file: <CSV file>
```

**Parameters:**
- `file` (File, required) - CSV file to upload

**Response (Success):**
```json
{
  "success": true,
  "table_name": "users",
  "columns": [
    {"name": "id", "type": "int64"},
    {"name": "name", "type": "object"},
    {"name": "email", "type": "object"}
  ],
  "row_count": 150
}
```

**Response (Error):**
```json
{
  "detail": "File must be CSV"
}
```

**Status Codes:**
- `200` - File uploaded successfully
- `400` - Invalid file format
- `500` - Server error

---

### List Tables

Get all available tables from uploaded files.

```http
GET /tables
```

**Response:**
```json
{
  "tables": ["users", "products", "orders"],
  "metadata": {
    "users": {
      "original_name": "users.csv",
      "row_count": 150,
      "columns": [
        {"name": "id", "type": "int64"},
        {"name": "name", "type": "object"}
      ]
    },
    "products": {
      "original_name": "products.csv",
      "row_count": 500,
      "columns": [
        {"name": "product_id", "type": "int64"},
        {"name": "title", "type": "object"}
      ]
    }
  }
}
```

**Status Codes:**
- `200` - Tables retrieved successfully

---

### Get Table Schema

Get detailed schema information for a specific table.

```http
GET /schema/{table_name}
```

**Parameters:**
- `table_name` (string, path) - Name of the table

**Response:**
```json
{
  "table_name": "users",
  "columns": [
    {"name": "id", "type": "int64"},
    {"name": "name", "type": "object"},
    {"name": "email", "type": "object"},
    {"name": "created_at", "type": "datetime64[ns]"},
    {"name": "active", "type": "bool"}
  ]
}
```

**Status Codes:**
- `200` - Schema retrieved successfully
- `400` - Invalid table name
- `404` - Table not found

---

### Generate and Execute Query

Convert natural language to SQL and optionally execute it.

```http
POST /query
Content-Type: application/json

{
  "query": "Show me all active users",
  "table_name": "users",
  "execute": true,
  "limit": 100,
  "offset": 0
}
```

**Request Body:**
```json
{
  "query": "string (required)",      // Natural language question
  "table_name": "string (required)", // Table to query
  "execute": "boolean (optional)",   // Whether to execute (default: false)
  "limit": "integer (optional)",     // Page size (max: 200)
  "offset": "integer (optional)"     // Page offset
}
```

**Response (Success with Execution):**
```json
{
  "success": true,
  "sql": "SELECT * FROM users WHERE active = 1",
  "results": {
    "columns": ["id", "name", "email", "active"],
    "data": [
      {"id": 1, "name": "John", "email": "john@example.com", "active": 1},
      {"id": 2, "name": "Jane", "email": "jane@example.com", "active": 1}
    ],
    "row_count": 2,
    "limit": 100,
    "offset": 0,
    "has_more": false
  }
}
```

**Response (Success without Execution):**
```json
{
  "success": true,
  "sql": "SELECT * FROM users WHERE active = 1",
  "preview": true
}
```

**Response (Error):**
```json
{
  "success": false,
  "error": "Query contains dangerous keyword: DELETE"
}
```

**Error Types:**
- `"LLM error: ..."` - Gemini API error
- `"The query cannot be answered..."` - LLM couldn't generate valid query
- `"Query contains dangerous keyword: ..."` - SQL injection detected
- `"Execution error: ..."` - Database execution failed

**Status Codes:**
- `200` - Query processed successfully
- `400` - Invalid request or validation failed
- `404` - Table not found
- `500` - Server error

---

### Query History

Get history of executed queries.

```http
GET /history?table_name=users&limit=50
```

**Query Parameters:**
- `table_name` (string, optional) - Filter by table name
- `limit` (integer, optional) - Maximum results (default: 50)

**Response:**
```json
{
  "history": [
    {
      "id": 1,
      "natural_language": "Show me all active users",
      "generated_sql": "SELECT * FROM users WHERE active = 1",
      "table_name": "users",
      "executed": true,
      "error": null,
      "created_at": "2024-03-29T10:30:00"
    },
    {
      "id": 2,
      "natural_language": "Count users by status",
      "generated_sql": "SELECT status, COUNT(*) FROM users GROUP BY status",
      "table_name": "users",
      "executed": false,
      "error": null,
      "created_at": "2024-03-29T10:25:00"
    }
  ],
  "limit": 50
}
```

**Status Codes:**
- `200` - History retrieved successfully

---

## Data Types

### Column Types (from Pandas)
- `int64` - Integer
- `float64` - Floating point
- `object` - String/Text
- `datetime64[ns]` - Date/Time
- `bool` - Boolean

---

## Error Handling

All errors follow this format:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message describing what went wrong",
    "details": {}
  }
}
```

Common errors:

| Error | Status | Cause |
|-------|--------|-------|
| "File must be CSV" | 400 | Invalid file format |
| "Missing query or table_name" | 400 | Incomplete request |
| "Invalid table name" | 400 | SQL injection attempt |
| "Table not found" | 404 | Table doesn't exist |
| "LLM error: ..." | 200 | Gemini API failure |
| "Query contains dangerous keyword: DELETE" | 200 | Safety validation failed |

---

## Authentication

Currently, the API has no authentication. For production use, add:

```python
from fastapi.security import HTTPBearer
security = HTTPBearer()

@app.get("/tables")
async def list_tables(credentials: HTTPAuthCredentials = Depends(security)):
    # Verify token
    pass
```

---

## Rate Limiting

Built-in rate limiting is enabled with SlowAPI decorators on key endpoints.

```python
from slowapi import Limiter
limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/query")
@limiter.limit("10/minute")
async def natural_language_query(request):
    pass
```

---

## CORS Configuration

By default, CORS is configured for:
- `http://localhost:3000` (frontend)
- `http://localhost:3001` (alternate)

Configure in `backend/config.py`:

```python
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
```

---

## Logging

The API logs important events:

```
INFO: Uploading file: data.csv
INFO: Successfully imported users with 150 rows
INFO: Processing query: Show me all active users... for table: users
INFO: Generated SQL: SELECT * FROM users WHERE active = 1...
INFO: Query executed successfully, returned 2 rows
ERROR: Query processing error: Table 'invalid' not found
```

---

## Interactive API Documentation

Visit `http://localhost:8000/docs` for interactive Swagger UI documentation where you can test all endpoints.

---

## Examples

### Example 1: Upload and Query

```bash
# Step 1: Upload a CSV file
curl -X POST http://localhost:8000/upload \
  -F "file=@data.csv"

# Response:
# {"success": true, "table_name": "data", "row_count": 100, ...}

# Step 2: Query the data
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Show me the top 10 records",
    "table_name": "data",
    "execute": true
  }'
```

### Example 2: Get Schema Before Querying

```bash
# Get table structure
curl http://localhost:8000/schema/users

# Response:
# {"table_name": "users", "columns": [...]}

# Then construct a query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Find users older than 30",
    "table_name": "users",
    "execute": true
  }'
```

### Example 3: Just Generate SQL Without Executing

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What is the total revenue?",
    "table_name": "sales",
    "execute": false
  }'

# Response:
# {"success": true, "sql": "SELECT SUM(revenue) FROM sales", "preview": true}
```

---

## Performance Considerations

- Large CSV uploads (>100MB) may timeout
- Complex queries may take time to generate LLM responses
- Result sets >10,000 rows should be paginated
- Consider adding indexes for frequently filtered columns

---

## Limits

- Maximum CSV file size: 500MB (default)
- Maximum query result rows: 100,000 (no hard limit, memory dependent)
- LLM response timeout: 30 seconds
- Database query timeout: 60 seconds
