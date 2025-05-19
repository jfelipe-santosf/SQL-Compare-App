from sql_compare.core.schema_comparer import SchemaComparerService
import pytest

def test_schema_comparer_initialization():
    service = SchemaComparerService()
    assert service.max_retries == 3  # default value
    assert service.retry_delay == 1.0  # default value

def test_schema_comparer_custom_initialization():
    service = SchemaComparerService(max_retries=5, retry_delay=2.0)
    assert service.max_retries == 5
    assert service.retry_delay == 2.0
