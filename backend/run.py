import os
import uvicorn
from core.config import settings

if __name__ == "__main__":
    workers = int(os.cpu_count() * 2 + 1)
    
    # Platform safety check for uvloop (not supported on Windows)
    try:
        import uvloop
        loop_config = "uvloop"
    except ImportError:
        loop_config = "auto"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", 8000)),
        workers=workers,
        loop=loop_config,
        http="httptools",
        log_level=settings.LOG_LEVEL.lower(),
        proxy_headers=True,
        forwarded_allow_ips="*"
    )
