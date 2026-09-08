"""Pydantic schemas for QueryLens table profiling and column statistics."""
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class TopValueEntry(BaseModel):
    """Frequent value distribution entry."""
    value: Any
    count: int
    percentage: float


class ColumnProfile(BaseModel):
    """Detailed statistical profile of an individual column."""
    name: str
    type: str
    total_count: int
    null_count: int
    null_percentage: float
    distinct_count: int
    uniqueness_ratio: float
    min_value: Optional[Any] = None
    max_value: Optional[Any] = None
    mean_value: Optional[float] = None
    median_value: Optional[float] = None
    zero_count: Optional[int] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    avg_length: Optional[float] = None
    top_values: List[TopValueEntry] = Field(default_factory=list)
    quality_flags: List[str] = Field(default_factory=list)


class TableQualitySummary(BaseModel):
    """High-level health and data quality overview for a table."""
    total_rows: int
    total_columns: int
    has_missing_data: bool
    columns_with_nulls: List[str] = Field(default_factory=list)
    primary_key_candidates: List[str] = Field(default_factory=list)
    constant_columns: List[str] = Field(default_factory=list)


class TableProfileResponse(BaseModel):
    """Response payload for table profiling."""
    success: bool = True
    table_name: str
    row_count: int
    column_count: int
    columns: List[ColumnProfile]
    quality_summary: TableQualitySummary
