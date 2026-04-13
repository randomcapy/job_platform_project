"""
run.py — Convenience launcher for the ResumeMatch AI server.

WHY THIS EXISTS:
Instead of memorising the full uvicorn command, developers just run:
    python run.py

It also reads from .env (via config) so host/port can be overridden
without touching source code — useful for deploying on a university server
where port 8000 may already be in use.

Usage:
    python run.py               # default: http://localhost:8000
    PORT=9000 python run.py     # custom port
    HOST=0.0.0.0 python run.py  # expose on all network interfaces
"""

import os
import sys

# Ensure we run from the backend/ directory regardless of where the
# script is called from
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

import uvicorn

if __name__ == "__main__":
    host    = os.getenv("HOST", "127.0.0.1")
    port    = int(os.getenv("PORT", "8000"))
    reload  = os.getenv("RELOAD", "true").lower() == "true"
    workers = int(os.getenv("WORKERS", "1"))

    print(f"""
╔══════════════════════════════════════════════════════╗
║          ResumeMatch AI — Starting Server            ║
╠══════════════════════════════════════════════════════╣
║  URL     : http://{host}:{port:<35}║
║  Docs    : http://{host}:{port}/docs{' ' * 29}║
║  Reload  : {str(reload):<43}║
║  Workers : {workers:<43}║
╚══════════════════════════════════════════════════════╝
    """)

    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        reload=reload,
        workers=workers if not reload else 1,  # reload mode only supports 1 worker
        log_level="info",
    )
