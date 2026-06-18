import os
import sys
import json

# Add the parent directory to Python path to import app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.openapi.utils import get_openapi
from main import app

def generate_sdk_specs():
    print("Extracting OpenAPI 3.0 specification from FastAPI...")
    
    # Generate schema
    openapi_schema = get_openapi(
        title=app.title,
        version=app.version,
        openapi_version=app.openapi_version,
        description=app.description,
        routes=app.routes,
    )
    
    # Save openapi.json
    output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "openapi.json"))
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
        
    print(f"OpenAPI schema successfully written to: {output_path}")
    print("\n" + "="*80)
    print("HOW TO GENERATE CLIENT SDK PACKAGES USING OPENAPI GENERATOR CLI:")
    print("="*80)
    print("Ensure you have Docker or openapi-generator-cli installed. Then run:\n")
    print("1. FOR PYTHON SDK:")
    print("   npx @openapitools/openapi-generator-cli generate \\")
    print(f"     -i openapi.json \\")
    print("     -g python \\")
    print("     -o ./sdk/python \\")
    print("     --additional-properties=packageName=quantcai\n")
    print("2. FOR JAVASCRIPT/TYPESCRIPT SDK:")
    print("   npx @openapitools/openapi-generator-cli generate \\")
    print(f"     -i openapi.json \\")
    print("     -g typescript-axios \\")
    print("     -o ./sdk/typescript\n")
    print("="*80)

if __name__ == "__main__":
    generate_sdk_specs()
