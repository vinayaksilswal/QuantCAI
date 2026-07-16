import sys
import subprocess
import os
import glob
import shutil

print("Fetching Prisma engine...")
os.environ["PRISMA_CLIENT_ENGINE_TYPE"] = "binary"
os.environ["PRISMA_CLI_QUERY_ENGINE_TYPE"] = "binary"

subprocess.run([sys.executable, "-m", "prisma", "py", "fetch"], check=True)

# Try Render cache directory first
cache_dir = "/opt/render/.cache/prisma-python/binaries/*/*/"
engines = glob.glob(cache_dir + "node_modules/@prisma/engines/query-engine-*")

# If not on Render, try local user cache (for local development)
if not engines:
    import platform
    home = os.path.expanduser("~")
    if platform.system() == "Windows":
        cache_dir = os.path.join(home, ".cache", "prisma-python", "binaries", "*", "*", "")
    else:
        cache_dir = os.path.join(home, ".cache", "prisma-python", "binaries", "*", "*", "")
    engines = glob.glob(cache_dir + "node_modules/@prisma/engines/query-engine-*")

if engines:
    engine_path = engines[0]
    expected_name = "prisma-" + os.path.basename(engine_path)
    shutil.copy(engine_path, expected_name)
    os.chmod(expected_name, 0o755)
    print(f"Fixed Prisma path bug: Copied {engine_path} to {expected_name}")
else:
    print("Could not find downloaded Prisma engine in cache directory.")
