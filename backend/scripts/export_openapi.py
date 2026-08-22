import json
import os
import sys
from pathlib import Path

# Add project root to sys.path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.app.main import app


def export_openapi_schema(output_path: Path = project_root / "docs" / "contracts" / "schemas" / "openapi.json") -> Path:
    """
    Exports the FastAPI application's OpenAPI 3.1.0 schema definition to the contract directory.
    Serves as the single source of truth for frontend TypeScript type generation.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate OpenAPI schema dictionary
    openapi_schema = app.openapi()
    
    # Write formatted JSON with deterministic key order
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_schema, f, indent=2, ensure_ascii=False)
        f.write("\n")
        
    num_paths = len(openapi_schema.get("paths", {}))
    print(f"[SUCCESS] Exported OpenAPI schema ({num_paths} paths) to {output_path}")
    return output_path


if __name__ == "__main__":
    export_openapi_schema()
