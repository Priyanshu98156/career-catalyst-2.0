import json
import os
import sys
from pathlib import Path

# Ensure workspace root is in sys.path
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from backend.main import app

def generate_openapi_spec():
    """Export FastAPI OpenAPI 3.1 JSON specification for frontend TypeScript codegen (DRY-7)."""
    openapi_spec = app.openapi()
    
    # Path to frontend
    root_dir = Path(__file__).resolve().parent.parent.parent
    output_path = root_dir / "frontend" / "openapi.json"
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(openapi_spec, f, indent=2)
        
    print(f"OpenAPI specification written successfully to: {output_path}")

if __name__ == "__main__":
    generate_openapi_spec()
