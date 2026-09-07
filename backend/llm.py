"""LLM integration for natural language to SQL conversion (Google Gemini)."""
from typing import Optional

from google import genai
from google.genai import types
from sqlglot import exp, parse_one
from sqlglot.errors import ParseError

from config import GEMINI_API_KEY, GEMINI_MODEL


def generate_sql_from_nl(
    natural_language: str,
    table_name: str,
    columns: list[dict],
    sample_data: Optional[str] = None,
    *,
    api_key: Optional[str] = None,
    model: Optional[str] = None,
) -> str:
    """Convert natural language to SQL using Gemini."""

    key = (api_key or "").strip() or GEMINI_API_KEY
    model_name = (model or "").strip() or GEMINI_MODEL
    if not key:
        return "ERROR: No API key. Enter your Gemini API key in the app or set GEMINI_API_KEY on the server."

    schema_desc = f"Table '{table_name}' has columns:\n"
    for col in columns:
        schema_desc += f"- {col['name']} ({col['type']})\n"

    if sample_data:
        schema_desc += f"\nSample data:\n{sample_data}"

    prompt = f"""You are a SQL expert. Convert the following natural language query into a valid SQL SELECT statement.

{schema_desc}

Natural Language Query: {natural_language}

Requirements:
- Only generate SELECT queries (no INSERT, UPDATE, DELETE, DROP)
- Return ONLY the SQL query, no explanations
- Use proper SQL syntax
- The query must work with SQLite
- If the query is impossible with the given schema, return: "INVALID_QUERY"

SQL Query:"""

    try:
        client = genai.Client(api_key=key)
        response = client.models.generate_content(
            model=model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0,
                max_output_tokens=500,
            ),
        )
        text = (response.text or "").strip()
        if not text:
            return "ERROR: Empty response from Gemini"
        return text
    except Exception as e:
        return f"ERROR: {str(e)}"


def validate_sql(sql: str, allowed_tables: Optional[set[str]] = None) -> tuple[bool, Optional[str]]:
    """Validate that SQL is read-only and restricted to known tables."""
    raw = sql.strip().rstrip(";")
    if not raw:
        return False, "Query is empty"

    try:
        parsed = parse_one(raw, read="sqlite")
    except ParseError:
        return False, "Generated SQL is invalid"

    if not isinstance(parsed, exp.Select):
        return False, "Query must be a single SELECT statement"

    disallowed_nodes = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Drop,
        exp.Create,
        exp.Alter,
        exp.Command,
    )
    if any(parsed.find(node_type) for node_type in disallowed_nodes):
        return False, "Query contains disallowed SQL operations"

    if allowed_tables:
        referenced_tables = {t.name.lower() for t in parsed.find_all(exp.Table) if t.name}
        unknown_tables = sorted(referenced_tables - {name.lower() for name in allowed_tables})
        if unknown_tables:
            return False, f"Query references unknown tables: {', '.join(unknown_tables)}"

    return True, None
