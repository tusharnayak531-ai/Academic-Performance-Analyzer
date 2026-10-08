
from pathlib import Path
import io
import sqlite3
from datetime import date, datetime

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
)

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "academic_tracker.db"

st.set_page_config(
    page_title="Academic Intelligence Dashboard V2.0",
    page_icon="🎓",
    layout="wide",
)

# ---------------------------------------------------------
# Global styling
# ---------------------------------------------------------
st.markdown(
    """
    <style>
        .block-container {padding-top: 1.5rem; padding-bottom: 2.5rem;}
        .hero {
            padding: 26px 24px;
            border-radius: 24px;
            background: linear-gradient(120deg, rgba(120,80,255,.13), rgba(0,170,220,.10), rgba(0,190,120,.08));
            border: 1px solid rgba(128,128,128,.20);
            margin-bottom: 18px;
            position: relative;
            overflow: hidden;
        }
        .hero h1 {margin: 0; font-size: 2.15rem;}
        .hero p {opacity: .78; margin-top: 8px; margin-bottom: 0;}
        .pulse {
            display:inline-block;
            width:10px;height:10px;border-radius:50%;
            background: currentColor;
            margin-right:8px;
            animation: pulse 1.7s infinite;
        }
        @keyframes pulse {
            0% {transform:scale(.8); opacity:.45;}
            50% {transform:scale(1.25); opacity:1;}
            100% {transform:scale(.8); opacity:.45;}
        }
        .member-wrap {
            display:flex; flex-wrap:wrap; gap:14px; justify-content:center;
            margin: 18px 0 8px 0;
        }
        .member-card {
            min-width: 230px;
            border: 1px solid rgba(128,128,128,.22);
            border-radius: 18px;
            padding: 16px 18px;
            text-align:center;
            background: rgba(255,255,255,.04);
            box-shadow: 0 8px 26px rgba(0,0,0,.06);
            animation: floaty 3.2s ease-in-out infinite;
            transition: transform .25s ease;
        }
        .member-card:nth-child(2) {animation-delay:.35s;}
        .member-card:nth-child(3) {animation-delay:.70s;}
        .member-card:hover {transform: translateY(-6px) scale(1.02);}
        .member-name {font-size:1.03rem; font-weight:800;}
        .member-id {font-size:.84rem; opacity:.68; margin-top:4px;}
        @keyframes floaty {
            0%,100% {transform: translateY(0);}
            50% {transform: translateY(-8px);}
        }
        .soft-card {
            padding: 16px;
            border:1px solid rgba(128,128,128,.18);
            border-radius:18px;
            background:rgba(255,255,255,.03);
        }
        .mini-note {opacity:.72; font-size:.88rem;}
    </style>
    """,
    unsafe_allow_html=True,
)

TEAM = [
    ("TUSHAR NAYAK", "IU2441230774"),
    ("BHARGAV PADMANI", "IU2441230776"),
    ("ARKEY GATRAD", "IU2441230775"),
]

# ---------------------------------------------------------
# Database
# ---------------------------------------------------------
def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_conn()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS marks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester INTEGER NOT NULL,
            subject TEXT NOT NULL,
            credits REAL DEFAULT 3,
            cie REAL DEFAULT 0,
            midsem REAL DEFAULT 0,
            practical REAL DEFAULT 0,
            ese REAL DEFAULT 0,
            max_cie REAL DEFAULT 20,
            max_midsem REAL DEFAULT 20,
            max_practical REAL DEFAULT 50,
            max_ese REAL DEFAULT 40,
            UNIQUE(semester, subject)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS attendance (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semester INTEGER NOT NULL,
            subject TEXT NOT NULL,
            attended INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            UNIQUE(semester, subject)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS assignments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            subject TEXT NOT NULL,
            title TEXT NOT NULL,
            due_date TEXT,
            status TEXT DEFAULT 'Pending'
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            target_value REAL,
            current_value REAL,
            unit TEXT DEFAULT '%'
        )
    """)

    conn.commit()
    conn.close()

def seed_data():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM marks").fetchone()[0]
    if count == 0:
        rows = [
            (1, "Programming Fundamentals", 4, 17, 16, 43, 31, 20, 20, 50, 40),
            (1, "Engineering Mathematics", 4, 15, 14, 0, 29, 20, 20, 0, 40),
            (1, "Engineering Physics", 3, 16, 15, 45, 30, 20, 20, 50, 40),
            (2, "Data Structures", 4, 18, 17, 46, 32, 20, 20, 50, 40),
            (2, "Object Oriented Programming", 4, 17, 18, 44, 31, 20, 20, 50, 40),
            (2, "Discrete Mathematics", 3, 16, 15, 0, 30, 20, 20, 0, 40),
            (3, "Computer Organization", 4, 17, 16, 45, 31, 20, 20, 50, 40),
            (3, "Database Management Systems", 4, 18, 17, 47, 33, 20, 20, 50, 40),
            (3, "Operating Systems", 4, 16, 16, 44, 30, 20, 20, 50, 40),
            (4, "Design and Analysis of Algorithms", 4, 18, 17, 46, 33, 20, 20, 50, 40),
            (4, "Computer Networks", 4, 17, 18, 45, 32, 20, 20, 50, 40),
            (4, "Core Java Programming", 4, 16, 17, 46, 31, 20, 20, 50, 40),
            (5, "CN", 4, 16, 17, 45, 32, 20, 20, 50, 40),
            (5, "DAA", 4, 19, 16, 47, 32, 20, 20, 50, 40),
            (5, "PSC", 4, 17, 17, 48, 26, 20, 20, 50, 40),
            (5, "EEWM", 3, 17, 20, 46, 30, 20, 20, 50, 40),
            (5, "AMP", 4, 15, 20, 45, 32, 20, 20, 50, 40),
            (5, "WT", 4, 16, 8, 0, 25, 20, 20, 0, 40),
        ]
        conn.executemany("""
            INSERT OR IGNORE INTO marks (
                semester, subject, credits, cie, midsem, practical, ese,
                max_cie, max_midsem, max_practical, max_ese
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows)

    if conn.execute("SELECT COUNT(*) FROM attendance").fetchone()[0] == 0:
        conn.executemany("""
            INSERT OR IGNORE INTO attendance (semester, subject, attended, total)
            VALUES (?, ?, ?, ?)
        """, [
            (5, "CN", 31, 38),
            (5, "DAA", 34, 39),
            (5, "PSC", 29, 38),
            (5, "EEWM", 35, 40),
            (5, "AMP", 33, 39),
            (5, "WT", 27, 38),
        ])

    if conn.execute("SELECT COUNT(*) FROM goals").fetchone()[0] == 0:
        conn.execute(
            "INSERT INTO goals (title, target_value, current_value, unit) VALUES (?, ?, ?, ?)",
            ("Semester 5 Percentage", 80, 0, "%")
        )

    conn.commit()
    conn.close()

init_db()
seed_data()

# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------
def load_marks():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM marks ORDER BY semester, subject", conn)
    conn.close()
    return prepare_marks(df)

def prepare_marks(df):
    if df.empty:
        return df

    numeric = [
        "semester", "credits", "cie", "midsem", "practical", "ese",
        "max_cie", "max_midsem", "max_practical", "max_ese"
    ]
    for col in numeric:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)

    df["obtained"] = df[["cie", "midsem", "practical", "ese"]].sum(axis=1)
    df["maximum"] = df[["max_cie", "max_midsem", "max_practical", "max_ese"]].sum(axis=1)
    df["percentage"] = np.where(
        df["maximum"] > 0,
        (df["obtained"] / df["maximum"]) * 100,
        0
    )
    df["percentage"] = df["percentage"].round(2)

    def grade(p):
        if p >= 90: return "A+"
        if p >= 80: return "A"
        if p >= 70: return "B+"
        if p >= 60: return "B"
        if p >= 50: return "C"
        if p >= 40: return "D"
        return "F"

    def gp(p):
        if p >= 90: return 10
        if p >= 80: return 9
        if p >= 70: return 8
        if p >= 60: return 7
        if p >= 50: return 6
        if p >= 40: return 5
        return 0

    df["grade"] = df["percentage"].apply(grade)
    df["grade_point"] = df["percentage"].apply(gp)
    df["status"] = np.where(df["percentage"] >= 40, "Pass", "Fail")
    return df

def semester_summary(df):
    if df.empty:
        return pd.DataFrame(columns=["semester", "average_percentage", "sgpa"])

    avg = df.groupby("semester", as_index=False)["percentage"].mean()
    avg = avg.rename(columns={"percentage": "average_percentage"})

    weighted = df.assign(weighted_gp=df["grade_point"] * df["credits"])
    sgpa = weighted.groupby("semester").agg(
        weighted_gp=("weighted_gp", "sum"),
        credits=("credits", "sum"),
    ).reset_index()
    sgpa["sgpa"] = np.where(sgpa["credits"] > 0, sgpa["weighted_gp"] / sgpa["credits"], 0)

    return avg.merge(sgpa[["semester", "sgpa"]], on="semester", how="left")

def calculate_cgpa(df):
    if df.empty:
        return 0.0
    total_credits = df["credits"].sum()
    if total_credits <= 0:
        return 0.0
    return float((df["grade_point"] * df["credits"]).sum() / total_credits)

def rule_based_insights(df):
    if df.empty:
        return ["Add marks to generate performance insights."]

    insights = []
    by_subject = df.groupby("subject", as_index=False)["percentage"].mean().sort_values("percentage", ascending=False)
    best = by_subject.iloc[0]
    weak = by_subject.iloc[-1]
    insights.append(f"Strongest subject: {best['subject']} at {best['percentage']:.1f}%.")
    insights.append(f"Highest improvement opportunity: {weak['subject']} at {weak['percentage']:.1f}%.")

    sem = semester_summary(df)
    if len(sem) >= 2:
        change = sem.iloc[-1]["average_percentage"] - sem.iloc[-2]["average_percentage"]
        if change >= 0:
            insights.append(f"Latest semester average improved by {change:.1f} percentage points.")
        else:
            insights.append(f"Latest semester average dropped by {abs(change):.1f} percentage points.")

    failures = df[df["status"] == "Fail"]
    if failures.empty:
        insights.append("All recorded subjects are currently above the 40% pass threshold.")
    else:
        insights.append(f"{len(failures)} subject(s) are below the 40% pass threshold.")

    return insights

def next_sem_prediction(df):
    sem = semester_summary(df)
    if len(sem) < 2:
        return None, None
    x = sem["semester"].to_numpy(dtype=float)
    y = sem["average_percentage"].to_numpy(dtype=float)
    slope, intercept = np.polyfit(x, y, 1)
    next_sem = int(x.max()) + 1
    pred = float(np.clip(slope * next_sem + intercept, 0, 100))
    return next_sem, pred

def make_pdf_report(df, attendance_df, goal_df):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=1.4 * cm,
        leftMargin=1.4 * cm,
        topMargin=1.5 * cm,
        bottomMargin=1.5 * cm,
    )

    styles = getSampleStyleSheet()
    story = []
    story.append(Paragraph("Academic Intelligence Dashboard V2.0", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph("Project Team", styles["Heading2"]))

    for name, enrollment in TEAM:
        story.append(Paragraph(f"{name} — {enrollment}", styles["BodyText"]))

    story.append(Spacer(1, 10))
    story.append(Paragraph(f"Generated: {datetime.now().strftime('%d %b %Y, %I:%M %p')}", styles["BodyText"]))
    story.append(Spacer(1, 12))

    if not df.empty:
        cgpa = calculate_cgpa(df)
        sem = semester_summary(df)
        latest_avg = sem.iloc[-1]["average_percentage"] if not sem.empty else 0
        story.append(Paragraph(
            f"Overall CGPA (estimated from configured grade points): {cgpa:.2f}",
            styles["Heading3"]
        ))
        story.append(Paragraph(
            f"Latest semester average: {latest_avg:.2f}%",
            styles["BodyText"]
        ))
        story.append(Spacer(1, 10))

        story.append(Paragraph("Marks Summary", styles["Heading2"]))
        table_data = [["Sem", "Subject", "%", "Grade", "Status"]]
        for _, r in df.iterrows():
            table_data.append([
                int(r["semester"]),
                str(r["subject"])[:30],
                f"{r['percentage']:.1f}",
                r["grade"],
                r["status"],
            ])

        t = Table(table_data, colWidths=[1.2*cm, 8.5*cm, 1.8*cm, 1.8*cm, 2.2*cm])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
            ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.whitesmoke]),
        ]))
        story.append(t)

        story.append(PageBreak())
        story.append(Paragraph("Performance Insights", styles["Heading2"]))
        for text in rule_based_insights(df):
            story.append(Paragraph("• " + text, styles["BodyText"]))
            story.append(Spacer(1, 4))

    if not attendance_df.empty:
        story.append(Spacer(1, 10))
        story.append(Paragraph("Attendance", styles["Heading2"]))
        att_data = [["Sem", "Subject", "Attended", "Total", "%"]]
        temp = attendance_df.copy()
        temp["attendance_pct"] = np.where(
            temp["total"] > 0,
            temp["attended"] / temp["total"] * 100,
            0
        )
        for _, r in temp.iterrows():
            att_data.append([
                int(r["semester"]),
                str(r["subject"])[:30],
                int(r["attended"]),
                int(r["total"]),
                f"{r['attendance_pct']:.1f}",
            ])
        t2 = Table(att_data, colWidths=[1.2*cm, 8.5*cm, 2.1*cm, 2.0*cm, 1.8*cm])
        t2.setStyle(TableStyle([
            ("BACKGROUND", (0,0), (-1,0), colors.lightgrey),
            ("GRID", (0,0), (-1,-1), 0.5, colors.grey),
            ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
            ("FONTSIZE", (0,0), (-1,-1), 8),
        ]))
        story.append(t2)

    if not goal_df.empty:
        story.append(Spacer(1, 12))
        story.append(Paragraph("Goals", styles["Heading2"]))
        for _, g in goal_df.iterrows():
            story.append(Paragraph(
                f"{g['title']}: {g['current_value']:.1f}{g['unit']} / {g['target_value']:.1f}{g['unit']}",
                styles["BodyText"]
            ))

    doc.build(story)
    buffer.seek(0)
    return buffer.getvalue()

# ---------------------------------------------------------
# Login
# ---------------------------------------------------------
def login_screen():
    st.markdown(
        """
        <div class="hero">
            <h1>🎓 Academic Intelligence Dashboard V2.0</h1>
            <p><span class="pulse"></span>Python • Pandas • NumPy • Matplotlib • SQLite • Streamlit</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    cards = '<div class="member-wrap">' + "".join(
        f'<div class="member-card"><div>👨‍💻</div><div class="member-name">{n}</div><div class="member-id">{i}</div></div>'
        for n, i in TEAM
    ) + "</div>"
    st.markdown(cards, unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1, 1.2, 1])
    with c2:
        st.subheader("🔐 Demo Login")
        username = st.text_input("Username", placeholder="student")
        password = st.text_input("Password", type="password", placeholder="project123")
        if st.button("Enter Dashboard", use_container_width=True, type="primary"):
            if username == "student" and password == "project123":
                st.session_state["logged_in"] = True
                st.rerun()
            else:
                st.error("Invalid demo credentials.")

        st.caption("Demo credentials: student / project123")

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_screen()
    st.stop()

# ---------------------------------------------------------
# Header and navigation
# ---------------------------------------------------------
st.markdown(
    """
    <div class="hero">
        <h1>🎓 Academic Intelligence Dashboard V2.0</h1>
        <p><span class="pulse"></span>Live academic analysis, prediction, tracking and report generation.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

cards = '<div class="member-wrap">' + "".join(
    f'<div class="member-card"><div>👨‍💻</div><div class="member-name">{n}</div><div class="member-id">{i}</div></div>'
    for n, i in TEAM
) + "</div>"
st.markdown(cards, unsafe_allow_html=True)

with st.sidebar:
    st.header("Navigation")
    page = st.radio(
        "Go to",
        [
            "Dashboard",
            "Marks Entry",
            "SGPA & CGPA",
            "Target Calculator",
            "Attendance",
            "Assignments",
            "Goals",
            "Report",
            "About",
        ],
        label_visibility="collapsed",
    )
    st.divider()
    if st.button("Logout", use_container_width=True):
        st.session_state["logged_in"] = False
        st.rerun()

marks = load_marks()

# ---------------------------------------------------------
# Dashboard
# ---------------------------------------------------------
if page == "Dashboard":
    st.subheader("📊 Dashboard")

    if marks.empty:
        st.warning("No marks available.")
        st.stop()

    sem = semester_summary(marks)
    cgpa = calculate_cgpa(marks)
    latest_sem = int(marks["semester"].max())
    latest_avg = float(
        marks[marks["semester"] == latest_sem]["percentage"].mean()
    )
    next_sem, prediction = next_sem_prediction(marks)
    best = marks.loc[marks["percentage"].idxmax()]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Latest Semester", f"Sem {latest_sem}")
    c2.metric("Latest Average", f"{latest_avg:.1f}%")
    c3.metric("Estimated CGPA", f"{cgpa:.2f}")
    c4.metric("Best Subject", best["subject"], f"{best['percentage']:.1f}%")

    if prediction is not None:
        st.info(f"📈 Linear-trend prediction for Semester {next_sem}: **{prediction:.1f}%**")

    left, right = st.columns(2)

    with left:
        st.markdown("#### Semester-wise Performance")
        fig, ax = plt.subplots(figsize=(7.5, 4.2))
        ax.plot(sem["semester"], sem["average_percentage"], marker="o")
        ax.set_xlabel("Semester")
        ax.set_ylabel("Average Percentage")
        ax.set_ylim(0, 100)
        ax.set_xticks(sem["semester"])
        ax.grid(alpha=.2)
        st.pyplot(fig, clear_figure=True)

    with right:
        st.markdown("#### Latest Semester Subjects")
        current = marks[marks["semester"] == latest_sem].sort_values("percentage")
        fig, ax = plt.subplots(figsize=(7.5, 4.2))
        ax.barh(current["subject"], current["percentage"])
        ax.set_xlabel("Percentage")
        ax.set_xlim(0, 100)
        ax.grid(axis="x", alpha=.2)
        st.pyplot(fig, clear_figure=True)

    st.markdown("#### Component Comparison")
    latest = marks[marks["semester"] == latest_sem].copy()
    comp = latest.set_index("subject")[["cie", "midsem", "practical", "ese"]]
    st.bar_chart(comp)

    st.markdown("#### 💡 Smart Performance Insights")
    for insight in rule_based_insights(marks):
        st.write("•", insight)

    with st.expander("View full marks table"):
        st.dataframe(
            marks[
                ["semester", "subject", "credits", "cie", "midsem", "practical", "ese",
                 "obtained", "maximum", "percentage", "grade", "status"]
            ],
            use_container_width=True,
            hide_index=True,
        )

    st.download_button(
        "⬇️ Export all marks as CSV",
        data=marks.to_csv(index=False).encode("utf-8"),
        file_name="academic_marks_export.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------
# Marks Entry
# ---------------------------------------------------------
elif page == "Marks Entry":
    st.subheader("✍️ Marks Entry & CSV Import")

    tab1, tab2, tab3 = st.tabs(["Add / Update Subject", "CSV Import", "Delete Record"])

    with tab1:
        with st.form("marks_form"):
            c1, c2, c3 = st.columns(3)
            semester = c1.number_input("Semester", min_value=1, max_value=12, value=5, step=1)
            subject = c2.text_input("Subject", placeholder="Computer Networks")
            credits = c3.number_input("Credits", min_value=0.0, max_value=10.0, value=4.0, step=0.5)

            st.markdown("##### Obtained Marks")
            o1, o2, o3, o4 = st.columns(4)
            cie = o1.number_input("CIE", min_value=0.0, value=0.0)
            midsem = o2.number_input("Mid-Sem", min_value=0.0, value=0.0)
            practical = o3.number_input("Practical", min_value=0.0, value=0.0)
            ese = o4.number_input("ESE", min_value=0.0, value=0.0)

            st.markdown("##### Maximum Marks")
            m1, m2, m3, m4 = st.columns(4)
            max_cie = m1.number_input("Max CIE", min_value=0.0, value=20.0)
            max_midsem = m2.number_input("Max Mid-Sem", min_value=0.0, value=20.0)
            max_practical = m3.number_input("Max Practical", min_value=0.0, value=50.0)
            max_ese = m4.number_input("Max ESE", min_value=0.0, value=40.0)

            save = st.form_submit_button("Save Subject", type="primary", use_container_width=True)

        if save:
            if not subject.strip():
                st.error("Subject name is required.")
            else:
                conn = get_conn()
                conn.execute("""
                    INSERT INTO marks (
                        semester, subject, credits, cie, midsem, practical, ese,
                        max_cie, max_midsem, max_practical, max_ese
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(semester, subject) DO UPDATE SET
                        credits=excluded.credits,
                        cie=excluded.cie,
                        midsem=excluded.midsem,
                        practical=excluded.practical,
                        ese=excluded.ese,
                        max_cie=excluded.max_cie,
                        max_midsem=excluded.max_midsem,
                        max_practical=excluded.max_practical,
                        max_ese=excluded.max_ese
                """, (
                    int(semester), subject.strip(), float(credits),
                    float(cie), float(midsem), float(practical), float(ese),
                    float(max_cie), float(max_midsem), float(max_practical), float(max_ese)
                ))
                conn.commit()
                conn.close()
                st.success("Subject saved.")
                st.rerun()

    with tab2:
        st.caption(
            "CSV columns: semester, subject, credits, cie, midsem, practical, ese, "
            "max_cie, max_midsem, max_practical, max_ese"
        )
        uploaded = st.file_uploader("Upload CSV", type=["csv"])
        if uploaded is not None:
            preview = pd.read_csv(uploaded)
            st.dataframe(preview.head(20), use_container_width=True)
            if st.button("Import CSV into database", type="primary"):
                required = [
                    "semester", "subject", "credits", "cie", "midsem", "practical", "ese",
                    "max_cie", "max_midsem", "max_practical", "max_ese"
                ]
                missing = [c for c in required if c not in preview.columns]
                if missing:
                    st.error("Missing columns: " + ", ".join(missing))
                else:
                    conn = get_conn()
                    for _, r in preview.iterrows():
                        conn.execute("""
                            INSERT INTO marks (
                                semester, subject, credits, cie, midsem, practical, ese,
                                max_cie, max_midsem, max_practical, max_ese
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                            ON CONFLICT(semester, subject) DO UPDATE SET
                                credits=excluded.credits,
                                cie=excluded.cie,
                                midsem=excluded.midsem,
                                practical=excluded.practical,
                                ese=excluded.ese,
                                max_cie=excluded.max_cie,
                                max_midsem=excluded.max_midsem,
                                max_practical=excluded.max_practical,
                                max_ese=excluded.max_ese
                        """, tuple(r[c] for c in required))
                    conn.commit()
                    conn.close()
                    st.success("CSV imported.")
                    st.rerun()

    with tab3:
        options = [
            f"Sem {int(r.semester)} — {r.subject}"
            for _, r in marks.iterrows()
        ]
        selected = st.selectbox("Select record", [""] + options)
        if selected and st.button("Delete selected record", type="primary"):
            idx = options.index(selected)
            record_id = int(marks.iloc[idx]["id"])
            conn = get_conn()
            conn.execute("DELETE FROM marks WHERE id=?", (record_id,))
            conn.commit()
            conn.close()
            st.success("Record deleted.")
            st.rerun()

# ---------------------------------------------------------
# SGPA / CGPA
# ---------------------------------------------------------
elif page == "SGPA & CGPA":
    st.subheader("🧮 SGPA & CGPA Calculator")
    st.caption(
        "Grade points used in this demo: A+=10, A=9, B+=8, B=7, C=6, D=5, F=0."
    )

    sem = semester_summary(marks)
    st.dataframe(
        sem.rename(columns={
            "semester": "Semester",
            "average_percentage": "Average %",
            "sgpa": "SGPA"
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.metric("Overall Estimated CGPA", f"{calculate_cgpa(marks):.2f}")

    fig, ax = plt.subplots(figsize=(9, 4.5))
    ax.plot(sem["semester"], sem["sgpa"], marker="o")
    ax.set_xlabel("Semester")
    ax.set_ylabel("SGPA")
    ax.set_ylim(0, 10)
    ax.set_xticks(sem["semester"])
    ax.grid(alpha=.2)
    st.pyplot(fig, clear_figure=True)

# ---------------------------------------------------------
# Target Calculator
# ---------------------------------------------------------
elif page == "Target Calculator":
    st.subheader("🎯 Target Marks Calculator")

    c1, c2 = st.columns(2)
    with c1:
        current_marks = st.number_input("Marks already obtained", min_value=0.0, value=45.0)
        completed_max = st.number_input("Maximum marks already completed", min_value=0.0, value=60.0)
    with c2:
        remaining_max = st.number_input("Remaining exam maximum marks", min_value=1.0, value=40.0)
        target_pct = st.slider("Target final percentage", min_value=40, max_value=100, value=75)

    total_max = completed_max + remaining_max
    required_total = total_max * target_pct / 100
    required_remaining = required_total - current_marks

    st.markdown("#### Result")
    if required_remaining <= 0:
        st.success(
            f"You have already reached the equivalent of a {target_pct}% target."
        )
    elif required_remaining > remaining_max:
        st.error(
            f"You would need {required_remaining:.1f}/{remaining_max:.1f} in the remaining exam, "
            "so this target is not mathematically possible with the entered marks."
        )
    else:
        st.success(
            f"You need approximately **{required_remaining:.1f}/{remaining_max:.1f}** "
            f"in the remaining exam to finish at **{target_pct}%**."
        )

    max_possible = (current_marks + remaining_max) / total_max * 100 if total_max else 0
    st.metric("Maximum Possible Final Percentage", f"{max_possible:.1f}%")

# ---------------------------------------------------------
# Attendance
# ---------------------------------------------------------
elif page == "Attendance":
    st.subheader("🗓️ Attendance Tracker")

    conn = get_conn()
    att = pd.read_sql_query("SELECT * FROM attendance ORDER BY semester, subject", conn)
    conn.close()

    with st.form("attendance_form"):
        c1, c2, c3, c4 = st.columns(4)
        sem = c1.number_input("Semester", min_value=1, max_value=12, value=5, step=1)
        sub = c2.text_input("Subject")
        attended = c3.number_input("Classes Attended", min_value=0, value=0, step=1)
        total = c4.number_input("Total Classes", min_value=0, value=0, step=1)
        save_att = st.form_submit_button("Save Attendance", type="primary")

    if save_att:
        if not sub.strip():
            st.error("Subject is required.")
        elif attended > total:
            st.error("Attended classes cannot exceed total classes.")
        else:
            conn = get_conn()
            conn.execute("""
                INSERT INTO attendance (semester, subject, attended, total)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(semester, subject) DO UPDATE SET
                    attended=excluded.attended,
                    total=excluded.total
            """, (int(sem), sub.strip(), int(attended), int(total)))
            conn.commit()
            conn.close()
            st.success("Attendance saved.")
            st.rerun()

    if not att.empty:
        att["Attendance %"] = np.where(att["total"] > 0, att["attended"] / att["total"] * 100, 0)
        att["Status"] = np.where(att["Attendance %"] >= 75, "Safe", "Shortage")
        st.dataframe(
            att[["semester", "subject", "attended", "total", "Attendance %", "Status"]],
            use_container_width=True,
            hide_index=True,
        )
        shortage = att[att["Attendance %"] < 75]
        if not shortage.empty:
            st.warning(
                "Attendance shortage: " + ", ".join(shortage["subject"].astype(str).tolist())
            )

# ---------------------------------------------------------
# Assignments
# ---------------------------------------------------------
elif page == "Assignments":
    st.subheader("✅ Assignment Tracker")

    conn = get_conn()
    assignments = pd.read_sql_query("SELECT * FROM assignments ORDER BY due_date", conn)
    conn.close()

    with st.form("assignment_form"):
        a1, a2, a3, a4 = st.columns(4)
        subject = a1.text_input("Subject")
        title = a2.text_input("Assignment")
        due = a3.date_input("Due Date", value=date.today())
        status = a4.selectbox("Status", ["Pending", "In Progress", "Completed"])
        save_assignment = st.form_submit_button("Add Assignment", type="primary")

    if save_assignment:
        if not subject.strip() or not title.strip():
            st.error("Subject and assignment title are required.")
        else:
            conn = get_conn()
            conn.execute(
                "INSERT INTO assignments (subject, title, due_date, status) VALUES (?, ?, ?, ?)",
                (subject.strip(), title.strip(), due.isoformat(), status)
            )
            conn.commit()
            conn.close()
            st.success("Assignment added.")
            st.rerun()

    if not assignments.empty:
        st.dataframe(assignments, use_container_width=True, hide_index=True)
        ids = assignments["id"].tolist()
        selected_id = st.selectbox("Assignment ID to update", [""] + ids)
        if selected_id != "":
            new_status = st.selectbox(
                "New status",
                ["Pending", "In Progress", "Completed"],
                key="assignment_status_update"
            )
            if st.button("Update Assignment Status"):
                conn = get_conn()
                conn.execute(
                    "UPDATE assignments SET status=? WHERE id=?",
                    (new_status, int(selected_id))
                )
                conn.commit()
                conn.close()
                st.success("Assignment updated.")
                st.rerun()

# ---------------------------------------------------------
# Goals
# ---------------------------------------------------------
elif page == "Goals":
    st.subheader("🏁 Academic Goal Tracker")

    conn = get_conn()
    goals = pd.read_sql_query("SELECT * FROM goals ORDER BY id", conn)
    conn.close()

    with st.form("goal_form"):
        g1, g2, g3, g4 = st.columns(4)
        title = g1.text_input("Goal", placeholder="Reach 8.5 CGPA")
        target = g2.number_input("Target", value=80.0)
        current = g3.number_input("Current", value=60.0)
        unit = g4.text_input("Unit", value="%")
        save_goal = st.form_submit_button("Save Goal", type="primary")

    if save_goal:
        if not title.strip():
            st.error("Goal title is required.")
        else:
            conn = get_conn()
            conn.execute(
                "INSERT INTO goals (title, target_value, current_value, unit) VALUES (?, ?, ?, ?)",
                (title.strip(), float(target), float(current), unit.strip() or "%")
            )
            conn.commit()
            conn.close()
            st.success("Goal added.")
            st.rerun()

    if not goals.empty:
        for _, g in goals.iterrows():
            st.markdown(f"**{g['title']}**")
            ratio = 0 if g["target_value"] == 0 else g["current_value"] / g["target_value"]
            st.progress(min(max(float(ratio), 0.0), 1.0))
            st.caption(
                f"{g['current_value']:.1f}{g['unit']} / {g['target_value']:.1f}{g['unit']}"
            )

# ---------------------------------------------------------
# Report
# ---------------------------------------------------------
elif page == "Report":
    st.subheader("📄 Academic Report Generator")

    conn = get_conn()
    attendance_df = pd.read_sql_query("SELECT * FROM attendance ORDER BY semester, subject", conn)
    goals_df = pd.read_sql_query("SELECT * FROM goals ORDER BY id", conn)
    conn.close()

    st.write(
        "Generate a PDF containing the project team, marks summary, performance insights, "
        "attendance and academic goals."
    )

    pdf_bytes = make_pdf_report(marks, attendance_df, goals_df)
    st.download_button(
        "⬇️ Download Academic Report PDF",
        data=pdf_bytes,
        file_name="Academic_Intelligence_Report.pdf",
        mime="application/pdf",
        type="primary",
    )

    st.download_button(
        "⬇️ Download Marks CSV",
        data=marks.to_csv(index=False).encode("utf-8"),
        file_name="Academic_Marks.csv",
        mime="text/csv",
    )

# ---------------------------------------------------------
# About
# ---------------------------------------------------------
elif page == "About":
    st.subheader("ℹ️ About the Project")

    st.markdown("""
    **Academic Intelligence Dashboard V2.0** is a Python-based academic analytics project.

    It demonstrates:
    - Python programming and functions
    - Pandas DataFrames and CSV processing
    - NumPy calculations and linear trend prediction
    - Matplotlib charts
    - Streamlit UI and interactive forms
    - SQLite database storage
    - SGPA / CGPA estimation
    - Marks target calculation
    - Attendance monitoring
    - Assignment and goal tracking
    - Rule-based performance insights
    - PDF report generation using ReportLab
    """)

    st.markdown("### Project Members")
    for name, enrollment in TEAM:
        st.markdown(f"**{name}** — `{enrollment}`")

    st.markdown("### Technology Stack")
    st.code("Python • Pandas • NumPy • Matplotlib • Streamlit • SQLite • ReportLab")

    st.info(
        "The SGPA/CGPA scale and prediction are educational demo calculations. "
        "If your university uses a different official grading formula, edit the grade-point mapping."
    )
