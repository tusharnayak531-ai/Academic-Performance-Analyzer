"""Academic Intelligence entrypoint: preserve V2 until durable V3 storage is configured.

V3 uses independent v3_* tables and requires DATABASE_URL in Render.
Without DATABASE_URL, maintain current V2 behavior to avoid temporary account storage.
"""
import os

if os.getenv("DATABASE_URL", "").strip():
    from v3_dashboard import run
    run()
else:
    from app_v2_legacy import *  # noqa: F401,F403
