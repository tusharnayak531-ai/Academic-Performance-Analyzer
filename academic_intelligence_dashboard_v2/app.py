"""Academic Intelligence entrypoint.

V3 requires both durable database configuration and explicit rollout activation.
V2 stays live until V3_ENABLED=1 and DATABASE_URL are both configured on Render.
"""
import os

if os.getenv("V3_ENABLED", "") == "1" and os.getenv("DATABASE_URL", "").strip():
    from v3_dashboard import run
    run()
else:
    from app_v2_legacy import *  # noqa: F401,F403
