# Academic Intelligence Dashboard V3.0

This folder contains **V3**. The complete original V2 application remains preserved as app_v2_legacy.py. The deployed V2 demo data has **not** been copied into V3: older marks belong to an unprotected shared SQLite database and must not be assigned to new accounts without owner verification.

## What's new

- Register, sign in and sign out of separate accounts (PBKDF2 salted password hashes).
- SQLAlchemy persistence with PostgreSQL in production and SQLite locally.
- Every academic record is scoped to the signed-in account.
- Configurable percentage-to-grade-point mapping, credit-weighted SGPA / CGPA.
- Separate CIE theory, midsemester, CIE practical, ESE practical and ESE theory marks.
- Target calculator, interactive SGPA what-if simulation and component backlog tracker.
- Plotly charts, subject trend forecasting, attendance, assignments and goals.
- Responsive Streamlit interface and exportable private PDF / CSV reports.
- Isolated per-account sample data.

## Run locally

~~~bash
python -m pip install -r requirements.txt pytest
python -m pytest -q tests/test_v3.py
streamlit run app.py --server.address 0.0.0.0
~~~

SQLite is automatically used for local development; set V3_SQLITE_PATH to choose its database file.

## Production deployment

Use an existing PostgreSQL database and set DATABASE_URL to its **internal** connection URL as a secret on the Render web service. **Never commit a DB URL, password or other secret to GitHub.**

- Root directory: academic_intelligence_dashboard_v2
- Build: pip install -r requirements.txt
- Start: streamlit run app.py --server.port $PORT --server.address 0.0.0.0
- Health check: /_stcore/health

The checked-in entrypoint keeps V2 running **by default**. To switch to V3 safely, set two secret environment variables on the Render web service: `DATABASE_URL` to the database internal connection string and `V3_ENABLED=1`. Setting `V3_ENABLED=1` without `DATABASE_URL` keeps V2 running. Do this only after tests and backups.\n\nOn Render, persistent database configuration is required before enabling public registration. Verify the database is reachable, and back up any important data before upgrading. A Render free PostgreSQL plan has an expiration date and **is not suitable as permanent user-data storage**. Upgrade database service and configure backup/restore before using V3 with real student records.

The V3 schema is intentionally separate (v3_* tables) so it never overwrites legacy V2 data. Do not remove the original app or local database until you've verified migrated records.

### Important limitations

1. **Demo thresholds**: Grade points are configurable but not verified against current Indus University policy. Pass/fail and component minimums may differ.
2. **SGPA planner**: The simulator calculates a credit-weighted SGPA for explicitly entered what-if marks; the per-subject 9 GP column is an illustrative minimum, not a guarantee.
3. **Predictions**: Linear trend extrapolations need at least two records of the same subject in different semesters.
4. **Login**: Basic password hashing and per-user ownership exist; for public production use add email verification, account recovery, external rate limiting, CSRF/cookie security review, audit logs, and retention/deletion policies.
5. **Persistence**: No default free Render local filesystem durability is assumed. Free PostgreSQL is temporary; choose a long-lived managed storage plan with backups.
6. **Data classification**: Academic data can be sensitive. Obtain permission to store and process marks.

## Compatibility

V2's features and code remain available in app_v2_legacy.py. Existing V2 CSV exports are supported in V3 by supplying ese_pr and max_ese_pr as zero if absent. Uploaded/entered marks are validated against component maxima.

## Smoke-test checklist before merging main

1. Run pytest and the Python compile checks in CI.
2. Verify PostgreSQL database connectivity with DATABASE_URL.
3. Create two different accounts and ensure each only sees its own data.
4. Add, edit, delete and export marks. Import a V2 CSV.
5. Validate ESE theory and practical marks and configure the grading scheme.
6. Confirm backlog status, attendance, assignments, goals and PDF download.
7. Check desktop/mobile responsive UI and chart display in a browser.
8. Check Render logs and health endpoint; then approve the merge into main.

Do **not** merge until checks pass.
