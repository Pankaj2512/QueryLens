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

### Export Table Data

Export data from an uploaded or created dataset in either `csv` (file download) or `json` (structured array) format.

```http
GET /export/{table_name}?format=csv&limit=1000&offset=0
```

**Path Parameters:**
- `table_name` (string, required) - Valid database table identifier

**Query Parameters:**
- `format` (string, optional, default: `"csv"`) - Output format: `csv` or `json`
- `limit` (integer, optional, default: `1000`, range: `1..10000`) - Row limit
- `offset` (integer, optional, default: `0`) - Row offset for pagination

**Response (CSV):**
- Content-Type: `text/csv`
- Header: `Content-Disposition: attachment; filename="{table_name}.csv"`
- Body: Comma-separated values stream

**Response (JSON):**
```json
{
  "table_name": "users",
  "row_count": 2,
  "data": [
    { "id": 1, "name": "Alice", "role": "admin" },
    { "id": 2, "name": "Bob", "role": "user" }
  ]
}
```

**Status Codes:**
- `200` - Export generated successfully
- `400` - Invalid table name or format parameter
- `404` - Table not found
- `429` - Rate limit exceeded (30 requests/minute)

---

### Explain Query Plan

Inspect and analyze the execution plan of a SQL query using SQLite's query planner. Detects full table scans, index lookups, temporary B-trees, and returns actionable performance recommendations.

```http
POST /explain
Content-Type: application/json

{
  "sql": "SELECT * FROM users WHERE active = 1",
  "table_name": "users"
}
```

**Request Body:**
- `sql` (string, required) - Valid SELECT statement to analyze
- `table_name` (string, required) - Target table identifier (must match query scope)

**Response:**
```json
{
  "success": true,
  "table_name": "users",
  "sql": "SELECT * FROM users WHERE active = 1",
  "steps": [
    {
      "id": 2,
      "parent": 0,
      "detail": "SCAN TABLE users",
      "scan_type": "FULL_TABLE_SCAN"
    }
  ],
  "has_full_table_scan": true,
  "uses_index": false,
  "uses_temp_btree": false,
  "performance_tier": "MODERATE",
  "recommendation": "Full table scan detected. Consider creating an index on filtered or joined columns to optimize query performance."
}
```

**Status Codes:**
- `200` - Query plan analyzed successfully
- `400` - Invalid SQL syntax, disallowed DDL/DML, or table mismatch
- `404` - Table not found
- `429` - Rate limit exceeded (30 requests/minute)

---

### Profile Table & Column Statistics

Compute comprehensive statistical distributions, missingness metrics, cardinality ratios, and automated data quality indicators for any table.

```http
GET /profile/{table_name}
```

**Parameters:**
- `table_name` (path, required) - Target table name to profile

**Response:**
```json
{
  "success": true,
  "table_name": "users",
  "row_count": 1500,
  "column_count": 5,
  "columns": [
    {
      "name": "id",
      "type": "INTEGER",
      "total_count": 1500,
      "null_count": 0,
      "null_percentage": 0.0,
      "distinct_count": 1500,
      "uniqueness_ratio": 1.0,
      "min_value": 1,
      "max_value": 1500,
      "mean_value": 750.5,
      "median_value": 750.0,
      "zero_count": 0,
      "min_length": null,
      "max_length": null,
      "avg_length": null,
      "top_values": [],
      "quality_flags": [
        "PRIMARY_KEY_CANDIDATE"
      ]
    },
    {
      "name": "email",
      "type": "TEXT",
      "total_count": 1500,
      "null_count": 15,
      "null_percentage": 1.0,
      "distinct_count": 1485,
      "uniqueness_ratio": 0.99,
      "min_value": null,
      "max_value": null,
      "mean_value": null,
      "median_value": null,
      "zero_count": null,
      "min_length": 11,
      "max_length": 42,
      "avg_length": 22.4,
      "top_values": [
        {
          "value": "user@example.com",
          "count": 3,
          "percentage": 0.2
        }
      ],
      "quality_flags": [
        "HIGH_CARDINALITY"
      ]
    }
  ],
  "quality_summary": {
    "total_rows": 1500,
    "total_columns": 5,
    "has_missing_data": true,
    "columns_with_nulls": ["email"],
    "primary_key_candidates": ["id"],
    "constant_columns": []
  }
}
```

**Quality Flags:**
- `PRIMARY_KEY_CANDIDATE` - 100% unique, zero null values
- `HIGH_NULLS` - More than 50% missing values
- `ALL_NULLS` - 100% missing values across all rows
- `CONSTANT` - Single distinct value across all rows (zero variance)
- `HIGH_CARDINALITY` - Over 90% distinct ratio on non-unique columns

**Status Codes:**
- `200` - Table profiled successfully
- `400` - Invalid table name format
- `404` - Table not found
- `429` - Rate limit exceeded (30 requests/minute)

---

### Get Schema Relationships (Foreign Keys & Joins)

Discover explicit database foreign keys and infer semantic join relationships across tables based on naming conventions and primary key mappings.

**Endpoint:** `GET /relationships`  
**Alias:** `GET /schema/relationships`  
**Rate Limit:** 60 requests/minute

**Response (200 OK):**

```json
{
  "success": true,
  "tables_inspected": ["customers", "orders", "products"],
  "relationship_count": 2,
  "relationships": [
    {
      "source_table": "orders",
      "source_column": "customer_id",
      "target_table": "customers",
      "target_column": "id",
      "relationship_type": "many-to-one",
      "confidence": 1.0,
      "source": "explicit_fk"
    },
    {
      "source_table": "order_items",
      "source_column": "product_id",
      "target_table": "products",
      "target_column": "id",
      "relationship_type": "many-to-one",
      "confidence": 0.85,
      "source": "inferred_name_convention"
    }
  ]
}
```

**Status Codes:**
- `200` - Relationships discovered successfully
- `500` - Database inspection error
- `429` - Rate limit exceeded (60 requests/minute)

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
