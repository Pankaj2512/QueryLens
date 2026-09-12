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
            if isinstance(col, dict):
                col_name = col.get("name", "").lower()
                col_type = str(col.get("type", "TEXT")).upper()
            else:
                col_name = getattr(col, "name", "").lower()
                col_type = str(getattr(col, "type", "TEXT")).upper()
            
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


def explain_query_plan(sql: str, table_name: str) -> dict[str, Any]:
    """Execute EXPLAIN QUERY PLAN on the given SQL and parse performance characteristics."""
    if not is_valid_identifier(table_name):
        return {"error": "Invalid table name"}
    try:
        clean_sql = sql.strip().rstrip(";")
        explain_sql = f"EXPLAIN QUERY PLAN {clean_sql}"
        with engine.connect() as conn:
            result = conn.execute(text(explain_sql))
            rows = result.fetchall()

        steps = []
        has_full_table_scan = False
        uses_index = False
        uses_temp_btree = False

        for row in rows:
            detail = str(row[3]) if len(row) > 3 else str(row[-1])
            step_info = {
                "id": int(row[0]),
                "parent": int(row[1]),
                "detail": detail,
            }
            if "SCAN TABLE" in detail and "USING INDEX" not in detail and "USING COVERING INDEX" not in detail:
                has_full_table_scan = True
                step_info["scan_type"] = "FULL_TABLE_SCAN"
            elif "USING INDEX" in detail or "USING COVERING INDEX" in detail:
                uses_index = True
                step_info["scan_type"] = "INDEX_SCAN"
            elif "USE TEMP B-TREE" in detail:
                uses_temp_btree = True
                step_info["scan_type"] = "TEMP_BTREE"
            else:
                step_info["scan_type"] = "SEARCH"
            steps.append(step_info)

        if has_full_table_scan:
            recommendation = "Full table scan detected. Consider creating an index on filtered or joined columns to optimize query performance."
            performance_tier = "MODERATE"
        elif uses_index:
            recommendation = "Optimal query execution using index lookups."
            performance_tier = "OPTIMAL"
        else:
            recommendation = "Standard table search without excessive scan overhead."
            performance_tier = "STANDARD"

        return {
            "success": True,
            "table_name": table_name,
            "sql": clean_sql,
            "steps": steps,
            "has_full_table_scan": has_full_table_scan,
            "uses_index": uses_index,
            "uses_temp_btree": uses_temp_btree,
            "performance_tier": performance_tier,
            "recommendation": recommendation,
        }
    except Exception as e:
        return {"error": str(e)}


def get_table_profile(table_name: str) -> dict[str, Any]:
    """Compute comprehensive statistical profile and data quality metrics for a table."""
    if not is_valid_identifier(table_name):
        return {"error": "Invalid table name"}
    try:
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        if table_name not in tables:
            return {"error": f"Table '{table_name}' not found"}

        columns = inspector.get_columns(table_name)
        if not columns:
            return {"error": f"Table '{table_name}' has no columns"}

        with engine.connect() as conn:
            total_rows_res = conn.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
            total_rows = int(total_rows_res.scalar() or 0)

            column_profiles = []
            columns_with_nulls = []
            primary_key_candidates = []
            constant_columns = []

            for col in columns:
                col_name = col["name"]
                col_type_str = str(col["type"]).upper()
                is_numeric = any(t in col_type_str for t in ("INT", "REAL", "FLOAT", "NUMERIC", "DOUBLE"))

                if total_rows == 0:
                    profile = {
                        "name": col_name,
                        "type": col_type_str,
                        "total_count": 0,
                        "null_count": 0,
                        "null_percentage": 0.0,
                        "distinct_count": 0,
                        "uniqueness_ratio": 0.0,
                        "min_value": None,
                        "max_value": None,
                        "mean_value": None,
                        "median_value": None,
                        "zero_count": 0 if is_numeric else None,
                        "min_length": None,
                        "max_length": None,
                        "avg_length": None,
                        "top_values": [],
                        "quality_flags": ["EMPTY_TABLE"],
                    }
                    column_profiles.append(profile)
                    continue

                # Basic counts
                cnt_res = conn.execute(text(f'SELECT COUNT("{col_name}"), COUNT(DISTINCT "{col_name}") FROM "{table_name}"'))
                non_null_count, distinct_count = cnt_res.fetchone()
                non_null_count = int(non_null_count or 0)
                distinct_count = int(distinct_count or 0)
                null_count = total_rows - non_null_count
                null_pct = round((null_count / total_rows) * 100.0, 2)
                uniqueness = round(distinct_count / total_rows, 4) if total_rows > 0 else 0.0

                min_val = None
                max_val = None
                mean_val = None
                median_val = None
                zero_count = None
                min_len = None
                max_len = None
                avg_len = None

                if is_numeric and non_null_count > 0:
                    num_query = f'SELECT MIN("{col_name}"), MAX("{col_name}"), AVG("{col_name}"), SUM(CASE WHEN "{col_name}" = 0 THEN 1 ELSE 0 END) FROM "{table_name}" WHERE "{col_name}" IS NOT NULL'
                    min_v, max_v, avg_v, zeros = conn.execute(text(num_query)).fetchone()
                    min_val = min_v
                    max_val = max_v
                    mean_val = round(float(avg_v), 4) if avg_v is not None else None
                    zero_count = int(zeros or 0)

                    # Median
                    offset = max(0, (non_null_count - 1) // 2)
                    med_query = f'SELECT "{col_name}" FROM "{table_name}" WHERE "{col_name}" IS NOT NULL ORDER BY "{col_name}" ASC LIMIT 1 OFFSET {offset}'
                    med_res = conn.execute(text(med_query)).scalar()
                    median_val = float(med_res) if med_res is not None else None

                elif any(t in col_type_str for t in ("TEXT", "CHAR", "VARCHAR", "STRING")) and non_null_count > 0:
                    len_query = f'SELECT MIN(LENGTH("{col_name}")), MAX(LENGTH("{col_name}")), AVG(LENGTH("{col_name}")) FROM "{table_name}" WHERE "{col_name}" IS NOT NULL'
                    min_l, max_l, avg_l = conn.execute(text(len_query)).fetchone()
                    min_len = int(min_l) if min_l is not None else None
                    max_len = int(max_l) if max_l is not None else None
                    avg_len = round(float(avg_l), 2) if avg_l is not None else None

                # Top values
                top_query = f'SELECT "{col_name}", COUNT(*) as cnt FROM "{table_name}" WHERE "{col_name}" IS NOT NULL GROUP BY "{col_name}" ORDER BY cnt DESC LIMIT 5'
                top_rows = conn.execute(text(top_query)).fetchall()
                top_values = [
                    {
                        "value": r[0],
                        "count": int(r[1]),
                        "percentage": round((int(r[1]) / total_rows) * 100.0, 2),
                    }
                    for r in top_rows
                ]

                # Quality flags
                flags = []
                if distinct_count == total_rows and null_count == 0 and total_rows > 0:
                    flags.append("PRIMARY_KEY_CANDIDATE")
                    primary_key_candidates.append(col_name)
                if null_pct >= 50.0 and null_count < total_rows:
                    flags.append("HIGH_NULLS")
                elif null_count == total_rows:
                    flags.append("ALL_NULLS")
                if distinct_count == 1 and null_count == 0:
                    flags.append("CONSTANT")
                    constant_columns.append(col_name)
                elif uniqueness >= 0.90 and distinct_count < total_rows:
                    flags.append("HIGH_CARDINALITY")

                if null_count > 0:
                    columns_with_nulls.append(col_name)

                column_profiles.append({
                    "name": col_name,
                    "type": col_type_str,
                    "total_count": total_rows,
                    "null_count": null_count,
                    "null_percentage": null_pct,
                    "distinct_count": distinct_count,
                    "uniqueness_ratio": uniqueness,
                    "min_value": min_val,
                    "max_value": max_val,
                    "mean_value": mean_val,
                    "median_value": median_val,
                    "zero_count": zero_count,
                    "min_length": min_len,
                    "max_length": max_len,
                    "avg_length": avg_len,
                    "top_values": top_values,
                    "quality_flags": flags,
                })

            quality_summary = {
                "total_rows": total_rows,
                "total_columns": len(columns),
                "has_missing_data": len(columns_with_nulls) > 0,
                "columns_with_nulls": columns_with_nulls,
                "primary_key_candidates": primary_key_candidates,
                "constant_columns": constant_columns,
            }

            return {
                "success": True,
                "table_name": table_name,
                "row_count": total_rows,
                "column_count": len(columns),
                "columns": column_profiles,
                "quality_summary": quality_summary,
            }
    except Exception as e:
        return {"error": str(e)}


def get_schema_relationships() -> dict[str, Any]:
    """Discover explicit foreign keys and infer semantic join relationships across tables."""
    try:
        inspector = inspect(engine)
        table_names = inspector.get_table_names()
        relationships: list[dict[str, Any]] = []
        seen_pairs: set[tuple[str, str, str, str]] = set()

        table_columns: dict[str, list[dict[str, Any]]] = {}
        for t in table_names:
            table_columns[t] = inspector.get_columns(t)

        # 1. Inspect explicit foreign keys
        for tbl in table_names:
            fks = inspector.get_foreign_keys(tbl)
            for fk in fks:
                referred_table = fk.get("referred_table")
                constrained_cols = fk.get("constrained_columns", [])
                referred_cols = fk.get("referred_columns", [])
                if referred_table and constrained_cols and referred_cols:
                    pair_key = (tbl, constrained_cols[0], referred_table, referred_cols[0])
                    if pair_key not in seen_pairs:
                        seen_pairs.add(pair_key)
                        relationships.append({
                            "source_table": tbl,
                            "source_column": constrained_cols[0],
                            "target_table": referred_table,
                            "target_column": referred_cols[0],
                            "relationship_type": "many-to-one",
                            "confidence": 1.0,
                            "source": "explicit_fk",
                        })

        # 2. Heuristic inference across naming conventions
        for source_tbl, s_cols in table_columns.items():
            for s_col in s_cols:
                s_name = s_col["name"].lower()

                for target_tbl, t_cols in table_columns.items():
                    if source_tbl == target_tbl:
                        continue

                    t_col_names = [c["name"].lower() for c in t_cols]
                    target_singular = target_tbl.rstrip("s").lower()

                    # Check pattern 1: source has `<target_singular>_id` or `<target_table>_id`
                    matches_target_pk = (
                        (s_name == f"{target_singular}_id" or s_name == f"{target_tbl.lower()}_id")
                        and ("id" in t_col_names or s_name in t_col_names)
                    )

                    target_col = "id" if "id" in t_col_names else s_name

                    if matches_target_pk and target_col in t_col_names:
                        pair_key = (source_tbl, s_col["name"], target_tbl, target_col)
                        if pair_key not in seen_pairs:
                            seen_pairs.add(pair_key)
                            relationships.append({
                                "source_table": source_tbl,
                                "source_column": s_col["name"],
                                "target_table": target_tbl,
                                "target_column": target_col,
                                "relationship_type": "many-to-one",
                                "confidence": 0.85,
                                "source": "inferred_name_convention",
                            })

        return {
            "success": True,
            "tables_inspected": table_names,
            "relationship_count": len(relationships),
            "relationships": relationships,
        }
    except Exception as e:
        return {"error": str(e)}

