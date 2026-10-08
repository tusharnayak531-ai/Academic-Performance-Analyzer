"""Academic Intelligence safe entrypoint.

Roll out V3 only after persistent database configuration and explicit activation.
Each Streamlit rerun must execute the legacy app afresh while V3 is disabled.
"""
import os
import runpy
from pathlib import Path

if os.getenv("V3_ENABLED", "") == "1" and os.getenv("DATABASE_URL", "").strip():
    from v3_dashboard import run
    run()
else:
    runpy.run_path(str(Path(__file__).with_name("app_v2_legacy.py")), run_name="__main__")
