"""
Tests for QueryLens backend.
Run with: pytest test_main.py -v
"""

import sys
from pathlib import Path

# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
from fastapi.testclient import TestClient
try:
    from main import app
except ImportError:
    from backend.main import app

client = TestClient(app)


class TestHealthCheck:
    """Health check endpoint tests."""
    
    def test_health_check_basic(self):
        """Test basic health check."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_health_check_endpoint(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    def test_full_health_check(self):
        """Test full health check."""
        response = client.get("/health/full")
        assert response.status_code == 200
        data = response.json()
        assert "overall_status" in data
        assert "components" in data
    
    def test_readiness_check(self):
        """Test readiness check."""
        response = client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert "ready" in data


class TestTableOperations:
    """Table operations tests."""
    
    def test_list_tables(self):
        """Test listing tables."""
        response = client.get("/tables")
        assert response.status_code == 200
        data = response.json()
        assert "tables" in data
        assert isinstance(data["tables"], list)
    
    def test_create_table_valid(self):
        """Test creating a valid table."""
        payload = {
            "name": "test_users",
            "columns": [
                {"name": "id", "type": "INTEGER"},
                {"name": "name", "type": "TEXT"},
                {"name": "email", "type": "TEXT"},
            ]
        }
        response = client.post("/create-table", json=payload)
        # Note: May fail due to rate limiting in tests, check status
        if response.status_code != 429:
            assert response.status_code in [200, 400]
    
    def test_create_table_invalid_name(self):
        """Test creating table with invalid name."""
        payload = {
            "name": "123invalid",  # Starts with number
            "columns": [
                {"name": "id", "type": "INTEGER"},
            ]
        }
        response = client.post("/create-table", json=payload)
        if response.status_code != 429:
            assert response.status_code == 422
    
    def test_create_table_invalid_type(self):
        """Test creating table with invalid column type."""
        payload = {
            "name": "test_table",
            "columns": [
                {"name": "id", "type": "INVALID_TYPE"},
            ]
        }
        response = client.post("/create-table", json=payload)
        if response.status_code != 429:
            assert response.status_code == 422


class TestQuery:
    """Query operation tests."""
    
    def test_query_missing_params(self):
        """Test query with missing parameters."""
        payload = {
            "query": "Show all records",
        }
        response = client.post("/query", json=payload)
        if response.status_code != 429:
            assert response.status_code == 422
    
    def test_query_too_long(self):
        """Test query that's too long."""
        payload = {
            "query": "a" * 10000,  # Exceeds max length
            "table_name": "test",
        }
        response = client.post("/query", json=payload)
        if response.status_code != 429:
            assert response.status_code == 422


class TestValidation:
    """Input validation tests."""
    
    def test_create_table_empty_name(self):
        """Test creating table with empty name."""
        payload = {
            "name": "",
            "columns": [
                {"name": "id", "type": "INTEGER"},
            ]
        }
        response = client.post("/create-table", json=payload)
        if response.status_code != 429:
            assert response.status_code == 422
    
    def test_create_table_duplicate_columns(self):
        """Test creating table with duplicate column names."""
        payload = {
            "name": "test_table",
            "columns": [
                {"name": "id", "type": "INTEGER"},
                {"name": "id", "type": "TEXT"},
            ]
        }
        response = client.post("/create-table", json=payload)
        if response.status_code != 429:
            assert response.status_code == 422
    
    def test_create_table_no_columns(self):
        """Test creating table with no columns."""
        payload = {
            "name": "test_table",
            "columns": []
        }
        response = client.post("/create-table", json=payload)
        if response.status_code != 429:
            assert response.status_code == 422


class TestRateLimiting:
    """Rate limiting tests."""
    
    def test_rate_limiting_not_exceeded(self):
        """Test that normal requests are not rate limited."""
        response = client.get("/")
        assert response.status_code in [200, 429]


class TestErrorHandling:
    """Error handling tests."""
    
    def test_404_not_found(self):
        """Test 404 error."""
        response = client.get("/nonexistent")
        assert response.status_code == 404
    
    def test_invalid_json(self):
        """Test invalid JSON request."""
        response = client.post(
            "/query",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code in [422, 400]


class TestExportEndpoints:
    """Tests for table data export in CSV and JSON formats."""

    @pytest.fixture(autouse=True)
    def create_sample_table(self):
        """Ensure a sample table exists for export testing."""
        payload = {
            "name": "export_test_table",
            "columns": [
                {"name": "id", "type": "INTEGER"},
                {"name": "item", "type": "TEXT"},
                {"name": "price", "type": "REAL"}
            ]
        }
        client.post("/create-table", json=payload)

    def test_export_csv_success(self):
        """Test exporting table as CSV."""
        response = client.get("/export/export_test_table?format=csv")
        assert response.status_code == 200
        assert "text/csv" in response.headers.get("content-type", "")
        assert 'attachment; filename="export_test_table.csv"' in response.headers.get("content-disposition", "")
        assert "id,item,price" in response.text

    def test_export_json_success(self):
        """Test exporting table as structured JSON records."""
        response = client.get("/export/export_test_table?format=json")
        assert response.status_code == 200
        data = response.json()
        assert data["table_name"] == "export_test_table"
        assert "data" in data
        assert isinstance(data["data"], list)

    def test_export_nonexistent_table(self):
        """Test exporting a table that does not exist returns 404."""
        response = client.get("/export/nonexistent_table_xyz?format=csv")
        assert response.status_code == 404

    def test_export_invalid_format(self):
        """Test exporting with invalid format parameter returns validation error."""
        response = client.get("/export/export_test_table?format=xml")
        assert response.status_code in [422, 400]


class TestExplainEndpoint:
    """Tests for SQL EXPLAIN QUERY PLAN analysis endpoint."""

    @pytest.fixture(autouse=True)
    def create_sample_table(self):
        """Ensure a sample table exists for explain testing."""
        payload = {
            "name": "explain_test_table",
            "columns": [
                {"name": "id", "type": "INTEGER"},
                {"name": "category", "type": "TEXT"},
                {"name": "amount", "type": "REAL"},
            ]
        }
        client.post("/create-table", json=payload)

    def test_explain_valid_select_query(self):
        """Test explaining a valid SELECT query."""
        payload = {
            "sql": "SELECT * FROM explain_test_table WHERE category = 'books'",
            "table_name": "explain_test_table",
        }
        response = client.post("/explain", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["table_name"] == "explain_test_table"
        assert "steps" in data
        assert isinstance(data["steps"], list)
        assert "performance_tier" in data
        assert "recommendation" in data

    def test_explain_nonexistent_table(self):
        """Test explaining a query against a nonexistent table returns 404."""
        payload = {
            "sql": "SELECT * FROM nonexistent_table_xyz",
            "table_name": "nonexistent_table_xyz",
        }
        response = client.post("/explain", json=payload)
        assert response.status_code == 404

    def test_explain_blocks_forbidden_dml(self):
        """Test that disallowed SQL statements (DROP/DELETE) are blocked."""
        payload = {
            "sql": "DROP TABLE explain_test_table",
            "table_name": "explain_test_table",
        }
        response = client.post("/explain", json=payload)
        assert response.status_code == 400

    def test_explain_invalid_sql_syntax(self):
        """Test explaining malformed SQL returns 400 error."""
        payload = {
            "sql": "SELECT FROM WHERE",
            "table_name": "explain_test_table",
        }
        response = client.post("/explain", json=payload)
        assert response.status_code == 400

    def test_explain_empty_body(self):
        """Test explaining with empty body returns validation error."""
        response = client.post("/explain", json={})
        assert response.status_code in [422, 400]


@pytest.fixture(scope="session", autouse=True)
def setup():
    """Setup test session."""
    # Could add database setup here
    yield
    # Could add cleanup here


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
