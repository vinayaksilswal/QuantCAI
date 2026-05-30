import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from main import app
    print("Smoke test passed: FastAPI app imported successfully without breaking syntax or import errors.")
except Exception as e:
    import traceback
    print(f"Smoke test failed:")
    traceback.print_exc()
    sys.exit(1)
