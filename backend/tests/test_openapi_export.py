import json
from pathlib import Path
import pytest

from backend.app.main import app
from backend.scripts.export_openapi import export_openapi_schema


def test_export_openapi_schema(tmp_path: Path):
    """
    Verifies that the export script writes a valid, complete OpenAPI 3.1 schema.
    """
    test_output_file = tmp_path / "openapi.json"
    result_path = export_openapi_schema(test_output_file)

    assert result_path.exists()
    assert result_path.is_file()

    with open(result_path, "r", encoding="utf-8") as f:
        schema = json.load(f)

    assert schema["openapi"].startswith("3.1")
    assert schema["info"]["title"] == "AI-Powered Adaptive Exam Learning Platform"
    assert "/api/v1/health" in schema["paths"]
    assert "/api/v1/healthz" in schema["paths"]

    # Verify schema structure matches app.openapi()
    live_schema = app.openapi()
    assert set(schema["paths"].keys()) == set(live_schema["paths"].keys())
