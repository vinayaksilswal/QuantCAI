"""
Gunicorn configuration for the QuantCAI admin / marketing server.

Gunicorn auto-loads this file from the working directory, so it applies to the
existing Render start command without any dashboard change:

    gunicorn main:app -w 1 -k uvicorn.workers.UvicornWorker

Only settings that need to differ from the defaults are set here; the worker
count and class stay on the command line.
"""

# Application startup connects to PostgreSQL and, if the build step did not
# provision it, downloads the ~20MB Prisma query engine. The default 30s worker
# timeout killed the worker mid-download, which surfaced as a boot loop rather
# than as the actual error.
timeout = 300

# Give in-flight requests room to finish during a deploy.
graceful_timeout = 60

# Render terminates idle upstream connections; keep this above their LB idle
# timeout to avoid spurious 502s between requests.
keepalive = 65

accesslog = "-"
errorlog = "-"
