
# Academic Intelligence Dashboard V2.0

A complete Streamlit + Python academic analytics project.

## Project Members

| Name | Enrollment Number |
|---|---|
| TUSHAR NAYAK | IU2441230774 |
| BHARGAV PADMANI | IU2441230776 |
| ARKEY GATRAD | IU2441230775 |

## Main Features

- Animated landing page and animated project-member cards
- Demo login screen
- SQLite database storage
- Marks entry and editing
- CSV import and export
- Semester-wise marks analysis
- Subject comparison charts
- SGPA and CGPA estimation
- NumPy linear-trend prediction
- Rule-based smart performance insights
- Target marks calculator
- Attendance tracker with shortage warning
- Assignment tracker
- Academic goal tracker
- PDF academic report generator
- Responsive Streamlit dashboard
- About / project technology page

## Demo Login

```text
Username: student
Password: project123
```

This login is only for a college-project demonstration. It is not intended as production authentication.

## Run Locally

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Render Start Command

```bash
streamlit run app.py --server.port $PORT --server.address 0.0.0.0
```

## CSV Format

```text
semester,subject,credits,cie,midsem,practical,ese,max_cie,max_midsem,max_practical,max_ese
```

Use `0` for any component that does not apply to a subject.

## Technology Stack

- Python
- Streamlit
- Pandas
- NumPy
- Matplotlib
- SQLite
- ReportLab

## Notes

The SGPA/CGPA mapping in this project is a demo scale:

- A+ = 10
- A = 9
- B+ = 8
- B = 7
- C = 6
- D = 5
- F = 0

Change the grade mapping in `app.py` if your university has a different official formula.

SQLite saves data to `academic_tracker.db` in the project folder. On some free cloud deployment platforms, local disk data may reset after redeployment or service restart.
