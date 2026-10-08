"""Academic Intelligence V3 — responsive Streamlit UI, retained V2 features."""
import io
import os
from datetime import date, datetime
from xml.sax.saxutils import escape

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, KeepTogether
from sqlalchemy import select

from v3_core import (
    Assignment, Attendance, Backlog, COMPONENTS, DEFAULT_MAX, Goal, GradeRule,
    Mark, authenticate, cgpa, create_store, delete_owned, durable_storage,
    grade_point, import_marks, marks_frame, owned, plan_target, predict_subjects,
    register, required_marks, rules, save_mark, summary,
)

TEAM = [
    ("TUSHAR NAYAK", "IU2441230774"),
    ("BHARGAV PADMANI", "IU2441230776"),
    ("ARKEY GATRAD", "IU2441230775"),
]
PAGE_NAMES = ["Dashboard", "Marks Entry", "SGPA & CGPA", "9+ SGPA Planner",
              "Target Calculator", "Backlog Tracker", "Attendance",
              "Assignments", "Goals", "Predictions", "Report", "Grading Settings", "About"]
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
:root {color-scheme:dark;--iu-violet:#8b78ff;--iu-blue:#42b7ff;--iu-ink:#080c1b;--iu-border:rgba(161,173,214,.15)}
html,body,[class*="css"],[data-testid="stAppViewContainer"] {font-family:'DM Sans',sans-serif}
.stApp {background:radial-gradient(ellipse at 85% -20%,rgba(85,59,188,.22),transparent 52%),radial-gradient(ellipse at 0% 50%,rgba(24,87,149,.14),transparent 50%),#080c1b;color:#edf1ff}
[data-testid="stSidebar"] {background:linear-gradient(180deg,#11172b,#0b1020);border-right:1px solid var(--iu-border)}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {color:#b9c6e9}
.block-container {max-width:1450px;padding-top:1.1rem;padding-bottom:3rem}
h1,h2,h3 {letter-spacing:-.035em}
div[data-testid="stMetric"] {background:linear-gradient(140deg,rgba(81,84,173,.20),rgba(17,28,57,.86));border:1px solid var(--iu-border);border-radius:20px;padding:20px 20px 16px;box-shadow:0 12px 38px rgba(0,0,0,.13);transition:transform .2s}
div[data-testid="stMetric"]:hover {transform:translateY(-3px)}
div[data-testid="stMetricLabel"] {color:#aab9da}
div[data-testid="stMetricValue"] {color:#f3f5ff}
[data-testid="stForm"],[data-testid="stExpander"],[data-testid="stDataFrame"] {border-radius:16px!important;border-color:var(--iu-border)!important}
.stButton button[kind="primary"],button[data-testid="stBaseButton-primary"] {background:linear-gradient(115deg,#6458d9,#357ebd);border:0;border-radius:12px}
.hero {padding:34px 36px;margin:5px 0 22px;border-radius:25px;overflow:hidden;position:relative;background:linear-gradient(114deg,rgba(82,70,175,.42),rgba(19,51,100,.45),rgba(12,22,44,.95));border:1px solid rgba(155,162,255,.22);box-shadow:0 18px 65px rgba(4,9,27,.25)}
.hero:after {content:"";position:absolute;width:240px;height:240px;border-radius:50%;right:-65px;top:-130px;background:radial-gradient(circle,rgba(80,169,255,.23),transparent 70%)}
.hero .eyebrow {color:#c9beff;font-size:12px;text-transform:uppercase;letter-spacing:.17em;font-weight:800}
.hero h1 {font-size:clamp(1.7rem,3vw,2.5rem);margin:7px 0;line-height:1.15;color:#fff}
.hero p {font-size:1rem;color:#c3ccea;margin:8px 0 0}
.iu-chip {display:inline-block;margin-top:17px;padding:7px 12px;border:1px solid rgba(157,172,255,.25);border-radius:40px;background:rgba(0,0,0,.16);color:#e3e5ff;font-size:12px}
.team {display:flex;gap:10px;flex-wrap:wrap;margin:8px 0 22px}
.member {padding:11px 16px;border:1px solid var(--iu-border);border-radius:13px;background:rgba(24,30,58,.8);color:#c1cbea;animation:fadeup .5s ease both}
.member strong {color:#f4f5ff}
@keyframes fadeup {from{opacity:.2;transform:translateY(9px)}to{opacity:1;transform:translateY(0)}}
[data-testid="stTabs"] button {border-radius:12px 12px 0 0}
@media(max-width:768px){.hero{padding:22px}.block-container{padding-left:1rem;padding-right:1rem}.member{flex:1 1 100%}div[data-testid="stMetric"]{padding:12px}}

/* IU Luxe — elevated glass surfaces and consistent interaction details */
:root {--iu-gold:#e8c88e;--iu-surface:#121b31;--iu-hairline:rgba(192,204,246,.13)}
.stApp {background-image:radial-gradient(circle at 90% 1%,rgba(110,80,225,.24),transparent 34%),radial-gradient(circle at 12% 33%,rgba(16,102,182,.13),transparent 38%),linear-gradient(180deg,#080d1d,#090d18 70%)}
[data-testid="stSidebar"] {background:linear-gradient(170deg,#111b31,#090f20 75%);box-shadow:10px 0 40px rgba(0,0,0,.12)}
[data-testid="stSidebar"] [data-testid="stRadio"] label {border-radius:12px;padding:6px 10px;transition:background .18s,color .18s}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {background:rgba(151,130,255,.12)}
[data-testid="stSidebar"] hr {border-color:rgba(177,197,240,.12)}
.block-container {max-width:1480px;padding-top:1.3rem}
.iu-topbar {display:flex;align-items:center;justify-content:space-between;gap:12px;margin:2px 0 18px;color:#96a7c8;font-size:.75rem;letter-spacing:.10em;text-transform:uppercase;font-weight:700}
.iu-status {display:inline-flex;align-items:center;gap:8px;padding:8px 12px;background:rgba(13,30,46,.85);border:1px solid rgba(120,215,186,.18);border-radius:40px;color:#9ce3cb;letter-spacing:.04em}
.iu-status:before {content:"";display:inline-block;width:7px;height:7px;border-radius:100%;background:#55d8ae;box-shadow:0 0 12px rgba(85,216,174,.7)}
.hero {background:radial-gradient(ellipse at 83% 18%,rgba(160,125,255,.35),transparent 48%),linear-gradient(118deg,#22214f,#182446 51%,#102239);padding:45px 43px;border:1px solid rgba(180,173,255,.24);box-shadow:0 24px 75px rgba(0,0,0,.28),inset 0 1px rgba(255,255,255,.07);min-height:225px}
.hero:before {content:"";position:absolute;right:48px;top:36px;width:120px;height:120px;border:1px solid rgba(232,200,142,.28);border-radius:30px;transform:rotate(18deg);box-shadow:0 0 0 21px rgba(232,200,142,.035),0 0 0 43px rgba(232,200,142,.025)}
.hero:after {right:6%;top:-110px;width:370px;height:370px;background:radial-gradient(circle,rgba(146,124,255,.22),transparent 67%)}
.hero h1 {font-size:clamp(2rem,3.4vw,3.25rem);font-weight:800;max-width:800px;letter-spacing:-.055em}
.hero p {font-size:1.02rem;line-height:1.7;max-width:650px}
.hero .eyebrow {color:#e8cb9a;letter-spacing:.2em;font-size:11px}
.iu-chip {border-color:rgba(232,200,142,.36);color:#f7dfb5;background:rgba(9,10,28,.32)}
.iu-section {padding:15px 0 5px;color:#cbd5f4;font-size:.83rem;letter-spacing:.16em;text-transform:uppercase;font-weight:800}
.iu-intro {margin:14px 0 18px;color:#9daece;font-size:.94rem}
div[data-testid="stMetric"] {border:1px solid rgba(172,174,255,.19);border-radius:22px;padding:23px 23px 18px;background:linear-gradient(138deg,rgba(33,44,82,.91),rgba(16,25,49,.95));box-shadow:0 17px 40px rgba(1,5,16,.23),inset 0 1px rgba(255,255,255,.035)}
div[data-testid="stMetricValue"] {font-size:clamp(1.7rem,2.25vw,2.5rem);font-weight:800;letter-spacing:-.055em}
div[data-testid="stMetricLabel"] {text-transform:uppercase;letter-spacing:.08em;font-size:11px;font-weight:700;color:#b0bddb}
div[data-testid="stMetric"]::before {content:"";display:block;width:34px;height:3px;border-radius:8px;margin-bottom:15px;background:linear-gradient(90deg,#b6a3ff,#55b9fb)}
[data-testid="stVerticalBlockBorderWrapper"] > div:has(> [data-testid="stVerticalBlock"]) {border-radius:20px}
[data-testid="stSelectbox"] [data-baseweb="select"] > div,[data-testid="stMultiSelect"] [data-baseweb="select"] > div,[data-testid="stTextInput"] input {background:rgba(22,32,57,.94)!important;border-color:rgba(156,173,231,.18)!important;border-radius:12px!important}
[data-testid="stExpander"], [data-testid="stForm"] {background:rgba(16,25,48,.5);border:1px solid var(--iu-hairline)!important;border-radius:18px!important}
.stButton button {border-radius:12px;transition:transform .2s,box-shadow .2s}
.stButton button:hover {transform:translateY(-1px);box-shadow:0 8px 24px rgba(84,92,192,.22)}
[data-testid="stTabs"] button {font-weight:700}
@media(max-width:900px){.hero{padding:30px;min-height:unset}.hero:before{display:none}.iu-topbar{letter-spacing:.03em}}
@media(max-width:620px){.hero{padding:24px 20px}.hero h1{font-size:1.95rem}.hero p{font-size:.91rem}.iu-topbar{font-size:.67rem}.iu-status{padding:6px 9px}.block-container{padding-left:.85rem;padding-right:.85rem}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{animation-duration:.01ms!important;transition-duration:.01ms!important}}
</style>
"""


@st.cache_resource
def store():
    return create_store()


def engine_session():
    factory, _ = store()
    return factory()


def header():
    st.markdown(CSS, unsafe_allow_html=True)
    st.markdown('<div class="iu-topbar"><span>IU / ACADEMIC INTELLIGENCE / STUDENT PORTAL</span>'
                '<span class="iu-status">ACADEMIC WORKSPACE</span></div>'
                '<section class="hero"><div class="eyebrow">INDUS UNIVERSITY · PRIVATE STUDENT WORKSPACE</div>'
                '<h1>Your academic future,<br><span style="color:#d7c5ff">beautifully in focus.</span></h1>'
                '<p>Track your performance, plan every semester, and make smarter moves toward your goals.</p>'
                '<span class="iu-chip">✦ IU LUXE EDITION</span></section>',
                unsafe_allow_html=True)


def members():
    st.markdown('<div class="team">' + "".join(
        '<div class="member">👨‍💻 <strong>' + escape(name) + '</strong><br><small>' +
        escape(number) + '</small></div>' for name, number in TEAM) + '</div>',
        unsafe_allow_html=True)


def auth_screen():
    header()
    members()
    if not durable_storage():
        st.warning("Local/demo database mode: records may disappear after a Render restart. "
                   "Connect a persistent PostgreSQL DATABASE_URL before production use.")
    login_tab, register_tab = st.tabs(["🔐 Sign in", "✨ Create account"])
    with login_tab:
        with st.form("login_form"):
            username = st.text_input("Username", key="login_user")
            password = st.text_input("Password", type="password", key="login_password")
            submitted = st.form_submit_button("Sign in", type="primary")
        if submitted:
            failures = st.session_state.get("login_failures", 0)
            if failures >= 8:
                st.error("Too many failed attempts in this session. Refresh to retry.")
            else:
                with engine_session() as db:
                    user = authenticate(db, username, password)
                    if user:
                        st.session_state["user_id"] = int(user.id)
                        st.session_state["username"] = user.username
                        st.session_state["login_failures"] = 0
                        st.rerun()
                    else:
                        st.session_state["login_failures"] = failures + 1
                        st.error("Incorrect username or password.")
    with register_tab:
        if os.getenv("RENDER") and not durable_storage():
            st.error("New accounts are disabled until a persistent database is configured.")
        else:
            with st.form("register_form"):
                username = st.text_input("Choose username", key="new_username")
                password = st.text_input("Choose password (8+ characters)", type="password", key="new_password")
                confirm = st.text_input("Confirm password", type="password")
                submitted = st.form_submit_button("Create private account")
            if submitted:
                if password != confirm:
                    st.error("Passwords do not match.")
                else:
                    try:
                        with engine_session() as db:
                            register(db, username, password)
                        st.success("Account created. Sign in using the first tab.")
                    except ValueError as exc:
                        st.error(str(exc))
                    except Exception:
                        st.error("Account could not be created. Try another username.")


def navigation():
    with st.sidebar:
        st.markdown("### ◈ INDUS UNIVERSITY")
        st.caption("I U  /  PREMIUM STUDENT PORTAL")
        st.caption("Signed in as " + st.session_state["username"])
        page = st.radio("Navigation", PAGE_NAMES, label_visibility="collapsed")
        st.divider()
        if st.button("🚪 Sign out", use_container_width=True):
            for key in ("user_id", "username", "login_failures"):
                st.session_state.pop(key, None)
            st.rerun()
    return page


def get_rows(db, uid):
    thresholds = rules(db, uid)
    marks = marks_frame(owned(db, Mark, uid), thresholds)
    return marks, thresholds


def chart_style(fig):
    fig.update_layout(margin=dict(t=22,b=18,l=8,r=8),
                      legend_title_text="", height=345, template="plotly_dark",
                      paper_bgcolor="rgba(0,0,0,0)",plot_bgcolor="rgba(0,0,0,0)",
                      font=dict(color="#d6ddf6",family="DM Sans"),
                      colorway=["#9686ff","#50b9ff","#4fd7c7","#f3b66d","#ef83bb"])
    fig.update_xaxes(gridcolor="rgba(180,200,255,.10)",zerolinecolor="rgba(180,200,255,.12)")
    fig.update_yaxes(gridcolor="rgba(180,200,255,.10)",zerolinecolor="rgba(180,200,255,.12)")
    return fig


def dashboard(db, uid, marks, thresholds):
    st.markdown('<div class="iu-section">01 / Performance intelligence</div>', unsafe_allow_html=True)
    st.subheader("Your academic overview")
    st.markdown('<div class="iu-intro">A clear view of your progress, strengths and next opportunities.</div>', unsafe_allow_html=True)
    if marks.empty:
        st.info("Your profile has no saved marks yet. Open Marks Entry to add a subject.")
        if st.button("Load sample demo subjects (only into this account)"):
            examples = [
                (5,"CN",4,16,17,45,25,32), (5,"DAA",4,19,16,47,26,32),
                (5,"PSC",4,17,17,48,27,26), (5,"EEWM",3,17,20,46,28,30),
                (5,"AMP",4,15,20,45,30,32), (5,"WT",4,16,8,0,0,25)
            ]
            for sem,subject,credits,cie,midsem,practical,ese_pr,ese in examples:
                data = dict(semester=sem,subject=subject,credits=credits,
                            cie=cie,midsem=midsem,practical=practical,ese_pr=ese_pr,ese=ese)
                for component in COMPONENTS:
                    data["max_"+component] = DEFAULT_MAX[component] if subject != "WT" or component not in ("practical","ese_pr") else 0
                save_mark(db, uid, data)
            st.rerun()
        return
    semesters = summary(marks)
    st.markdown("##### Explore your results")
    selected_semester = st.selectbox("📚 Semester", sorted(marks.semester.unique().tolist(), reverse=True),
                                      help="Explore any saved semester")
    latest = marks[marks.semester == selected_semester]
    selected_subjects = st.multiselect("📖 Focus subjects", sorted(latest.subject.unique().tolist()),
                                       default=sorted(latest.subject.unique().tolist()),
                                       help="Filter the subject comparison charts")
    focus = latest[latest.subject.isin(selected_subjects)]
    pending = sum(b.status != "Cleared" for b in owned(db, Backlog, uid))
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Estimated CGPA", f"{cgpa(marks):.2f}")
    c2.metric("Selected SGPA", f"{semesters[semesters.semester == selected_semester].iloc[0].sgpa:.2f}")
    c3.metric("Selected average", f"{latest.percentage.mean():.1f}%")
    c4.metric("Pending backlogs", pending)
    left,right = st.columns(2)
    with left:
        st.markdown("#### Semester performance")
        st.plotly_chart(chart_style(px.line(semesters, x="semester", y="sgpa",markers=True,
                                             labels={"sgpa":"Estimated SGPA","semester":"Semester"})),
                        use_container_width=True)
    with right:
        st.markdown("#### Latest semester")
        st.plotly_chart(chart_style(px.bar(focus.sort_values("percentage"), x="percentage",y="subject",
                        orientation="h",labels={"percentage":"Percentage","subject":"Subject"},
                        color="percentage",color_continuous_scale="Viridis")),
                        use_container_width=True)
    st.markdown("#### Assessment breakdown")
    st.plotly_chart(chart_style(px.bar(focus, x="subject", y=list(COMPONENTS), barmode="group")),
                    use_container_width=True)
    st.markdown("#### ✨ Performance highlights")
    strong = latest.loc[latest.percentage.idxmax()]
    weak = latest.loc[latest.percentage.idxmin()]
    st.write("**Strongest:**", strong.subject, f"({strong.percentage:.1f}%)")
    st.write("**Needs focus:**", weak.subject, f"({weak.percentage:.1f}%)")
    if len(semesters) > 1:
        delta = semesters.iloc[-1].sgpa - semesters.iloc[-2].sgpa
        st.write("**SGPA change:**", f"{delta:+.2f} from the previous semester.")
    st.caption("SGPA uses your configured grade mapping; it is not an official transcript.")


def marks_entry(db, uid, marks):
    st.subheader("✍️ IU Marks Entry & CSV Import")
    st.caption("Indus University · Semester 1–8 · subject-specific theory and practical components")
    add, upload, delete = st.tabs(["Add / update", "Import CSV", "Delete"])
    with add:
        with st.form("v3_mark_form"):
            a,b,c = st.columns(3)
            semester = a.selectbox("IU Semester", list(range(1, 9)), index=4)
            suggestions = {
                5: ["CN", "DAA", "PSC", "EEWM", "AMP", "WT"],
                4: ["BCPS", "COA", "DSA", "CJP", "MCS", "ROM"],
                3: ["OS", "OOCP", "Mathematics", "Core Java"],
                2: ["PPS", "Engineering Graphics", "Mathematics II"],
                1: ["Engineering Physics", "Mathematics I", "Programming Fundamentals"]
            }
            subject_choice = b.selectbox("IU Subject", ["Custom subject"] + suggestions.get(semester, []),
                                         help="Quick suggestions; confirm against your current syllabus")
            subject = b.text_input("Custom subject name") if subject_choice == "Custom subject" else subject_choice
            credits = c.number_input("Credits", min_value=0.,max_value=20.,value=4.,step=.5)
            st.caption("Enter CIE theory, mid-sem theory, CIE practical, ESE practical and ESE theory individually.")
            vals = {}
            cols = st.columns(5)
            labels = ["CIE theory", "Mid-sem", "CIE practical", "ESE practical", "ESE theory"]
            for i, key in enumerate(COMPONENTS):
                with cols[i]:
                    vals[key] = st.number_input(labels[i], min_value=0., value=0., key="score_"+key)
                    vals["max_"+key] = st.number_input("Out of", min_value=0.,value=float(DEFAULT_MAX[key]),
                                                       key="maximum_"+key)
            submitted = st.form_submit_button("Save subject",type="primary")
        if submitted:
            try:
                save_mark(db,uid,dict(semester=semester,subject=subject.strip(),credits=credits,**vals))
                st.success("Saved to your private academic record.")
                st.rerun()
            except (ValueError, TypeError) as exc:
                db.rollback()
                st.error(str(exc))
    with upload:
        st.caption("V2 CSV imports are supported. V3 adds ese_pr and max_ese_pr.")
        file = st.file_uploader("Import marks CSV", type=["csv"])
        if file is not None:
            try:
                data = pd.read_csv(file)
                for column in ("ese_pr","max_ese_pr"):
                    if column not in data:
                        data[column] = 0
                st.dataframe(data.head(10),use_container_width=True)
                if st.button("Import validated rows",type="primary"):
                    count = import_marks(db,uid,data)
                    st.success(f"Imported {count} subject records.")
                    st.rerun()
            except (ValueError, KeyError, TypeError, pd.errors.ParserError) as exc:
                db.rollback()
                st.error("CSV error: "+str(exc))
        if not marks.empty:
            st.download_button("Export my marks as CSV",marks.to_csv(index=False),file_name="v3_marks.csv")
    with delete:
        if marks.empty:
            st.info("No marks recorded.")
        else:
            options = {f"Sem {r.semester} • {r.subject}":int(r.id) for _,r in marks.iterrows()}
            chosen = st.selectbox("Select saved subject",list(options))
            if st.button("Delete selected subject"):
                delete_owned(db,Mark,uid,options[chosen])
                st.rerun()


def sgpa_page(marks):
    st.subheader("🎓 IU SGPA & CGPA Overview")
    if marks.empty:
        st.info("Add marks to see your results.")
        return
    semesters = summary(marks)
    st.metric("Credit-weighted estimated CGPA",f"{cgpa(marks):.2f}")
    st.dataframe(semesters.rename(columns={"semester":"Semester","percentage":"Average %",
                 "sgpa":"SGPA","credits":"Credits"}),hide_index=True,use_container_width=True)
    st.plotly_chart(chart_style(px.line(semesters,x="semester",y="sgpa",markers=True)),
                    use_container_width=True)
    st.caption("These are configurable estimates, not official Indus University grading decisions.")


def target_page():
    st.subheader("🎯 Required marks calculator")
    a,b = st.columns(2)
    earned = a.number_input("Already obtained",min_value=0.,value=45.)
    completed = a.number_input("Maximum already completed",min_value=0.,value=60.)
    remaining = b.number_input("Remaining exam maximum",min_value=0.,value=40.)
    target = b.slider("Target percentage",0,100,80)
    try:
        res = required_marks(earned,completed,remaining,target)
        if not res["possible"]:
            st.error("Target cannot be reached with the remaining available marks.")
        else:
            st.success(f"Required marks in remaining exams: {res['required']:.1f} / {remaining:.1f}")
        st.metric("Maximum possible final percentage",f"{res['maximum_percentage']:.1f}%")
    except ValueError as exc:
        st.error(str(exc))


def planner_page(marks, thresholds):
    st.subheader("🎯 IU Advanced 9+ SGPA Planner")
    if marks.empty:
        st.info("Add semester marks to create a target plan.")
        return
    a,b = st.columns(2)
    semester = a.selectbox("Semester",sorted(marks.semester.unique(),reverse=True))
    target = b.number_input("Target SGPA",min_value=0.,max_value=10.,value=9.0,step=.1)
    group = marks[marks.semester == semester]
    current = summary(group).iloc[0].sgpa
    st.metric("Current estimate",f"{current:.2f}",f"{current-target:+.2f} vs target")
    st.markdown("#### Grade thresholds and remaining exam requirements")
    st.caption("Plan assumes unentered exams can still contribute marks. Zero marks may mean 'not attempted' "
               "or 'not entered'; check the completed marks before using a target.")
    available = st.number_input("Additional marks still available across all subjects",
                                min_value=0.,value=float(group.maximum.sum()-group.obtained.sum()),step=1.)
    result = plan_target(marks,thresholds,int(semester),target)
    st.dataframe(result,hide_index=True,use_container_width=True)
    st.caption("Subject thresholds are individually useful but do not by themselves guarantee "
               "the selected overall SGPA. Use the credit-weighted simulator below.")
    st.markdown("#### What-if SGPA simulation")
    simulated = []
    for _, row in group.iterrows():
        left,right = st.columns([3,2])
        left.write(str(row.subject))
        with right:
            planned = st.number_input("Additional marks",min_value=0.,
                           max_value=float(max(0.,row.maximum-row.obtained)),value=0.,step=1.,
                           key="planned_"+str(row.id),label_visibility="collapsed")
        percent = 100*(row.obtained+planned)/row.maximum if row.maximum else 0
        simulated.append((grade_point(percent,thresholds),row.credits,planned))
    total = sum(gp * credits for gp,credits,_ in simulated)
    credits = sum(credits for _,credits,_ in simulated)
    simulated_sgpa = total/credits if credits else 0
    st.metric("Predicted SGPA with your planned marks",f"{simulated_sgpa:.2f}")
    if sum(x[2] for x in simulated) > available:
        st.error("Your planned additional marks exceed the remaining marks budget.")
    elif simulated_sgpa >= target:
        st.success("Your plan reaches the selected estimated SGPA.")
    else:
        st.warning("Your current plan does not yet reach the target.")
    st.caption("The grading scale and credit values must match your institution for reliable estimates.")


def backlog_page(db,uid):
    st.subheader("📚 IU Backlog Management")
    with st.form("backlog_form"):
        a,b,c = st.columns(3)
        sem = a.number_input("Semester",1,12,4,key="backlog_sem")
        name = b.text_input("Subject")
        component = c.selectbox("Component",["CIE Theory","ESE Theory","CIE Practical","ESE Practical","Other"])
        d,e = st.columns(2)
        status = d.selectbox("Status",["Pending","Cleared"])
        attempts = e.number_input("Attempts",1,20,1)
        save = st.form_submit_button("Save backlog",type="primary")
    if save:
        if not name.strip():
            st.error("Subject is required.")
        else:
            item = db.scalar(select(Backlog).where(Backlog.user_id==uid,Backlog.semester==sem,
                         Backlog.subject==name.strip(),Backlog.component==component))
            if item is None:
                item = Backlog(user_id=uid,semester=sem,subject=name.strip(),component=component)
                db.add(item)
            item.status, item.attempts = status, attempts
            db.commit()
            st.rerun()
    records = owned(db,Backlog,uid)
    if records:
        df = pd.DataFrame([dict(ID=x.id,Semester=x.semester,Subject=x.subject,Component=x.component,
                    Status=x.status,Attempts=x.attempts) for x in records])
        a,b,c = st.columns(3)
        a.metric("Total components",len(df))
        b.metric("Cleared",int((df.Status=="Cleared").sum()))
        c.metric("Pending",int((df.Status=="Pending").sum()))
        st.dataframe(df,hide_index=True,use_container_width=True)
        choice = st.selectbox("Remove component",list(df.ID))
        if st.button("Remove selected backlog record"):
            delete_owned(db,Backlog,uid,int(choice));st.rerun()
    else:
        st.info("No backlog components recorded.")


def attendance_page(db,uid):
    st.subheader("🗓️ Attendance tracker")
    with st.form("attendance_form_v3"):
        a,b,c,d = st.columns(4)
        sem = a.number_input("Semester",1,12,5,key="att_sem")
        subject = b.text_input("Subject")
        attended = c.number_input("Attended",min_value=0,step=1)
        total = d.number_input("Total classes",min_value=0,step=1)
        submitted = st.form_submit_button("Save attendance",type="primary")
    if submitted:
        if not subject.strip() or attended > total:
            st.error("Enter a subject and attended classes no greater than total.")
        else:
            item = db.scalar(select(Attendance).where(Attendance.user_id==uid,
                    Attendance.semester==sem,Attendance.subject==subject.strip()))
            if item is None:
                item = Attendance(user_id=uid,semester=sem,subject=subject.strip())
                db.add(item)
            item.attended,item.total=attended,total
            db.commit();st.rerun()
    rows = owned(db,Attendance,uid)
    if rows:
        df = pd.DataFrame([{"Semester":x.semester,"Subject":x.subject,"Attended":x.attended,
                "Total":x.total,"Attendance %":round(100*x.attended/x.total,1) if x.total else 0}
                for x in rows])
        df["Status"]=np.where(df["Attendance %"]>=75,"Safe","Shortage")
        st.dataframe(df,hide_index=True,use_container_width=True)
        if (df.Status=="Shortage").any():
            st.warning("Attendance shortage in: "+", ".join(df[df.Status=="Shortage"].Subject))
    else:
        st.info("No attendance recorded.")


def assignment_page(db,uid):
    st.subheader("✅ Assignment tracker")
    with st.form("assignment_form_v3"):
        a,b,c,d=st.columns(4)
        subject=a.text_input("Subject")
        title=b.text_input("Assignment title")
        due=c.date_input("Due date",date.today())
        status=d.selectbox("Status",["Pending","In Progress","Completed"])
        save=st.form_submit_button("Add assignment",type="primary")
    if save:
        if not subject.strip() or not title.strip():
            st.error("Subject and assignment title are required.")
        else:
            db.add(Assignment(user_id=uid,subject=subject.strip(),title=title.strip(),
                              due_date=due,status=status))
            db.commit();st.rerun()
    tasks=owned(db,Assignment,uid)
    if tasks:
        st.dataframe(pd.DataFrame([{"ID":x.id,"Subject":x.subject,"Title":x.title,
                                   "Due":x.due_date,"Status":x.status} for x in tasks]),
                     use_container_width=True,hide_index=True)
        a,b=st.columns(2)
        selected=a.selectbox("Assignment to update",[x.id for x in tasks])
        new=b.selectbox("New status",["Pending","In Progress","Completed"])
        if st.button("Update assignment"):
            item=db.scalar(select(Assignment).where(Assignment.user_id==uid,Assignment.id==selected))
            item.status=new
            db.commit();st.rerun()
        if st.button("Delete assignment"):
            delete_owned(db,Assignment,uid,selected);st.rerun()
    else:
        st.info("No assignments yet.")


def goals_page(db,uid):
    st.subheader("🏁 Academic goals")
    with st.form("goal_form_v3"):
        a,b,c,d=st.columns(4)
        title=a.text_input("Goal",placeholder="Reach 9.0 SGPA")
        target=b.number_input("Target value",value=9.0)
        current=c.number_input("Current value",value=7.0)
        unit=d.text_input("Unit",value="SGPA")
        save=st.form_submit_button("Create goal")
    if save:
        if not title.strip():
            st.error("Goal title required.")
        else:
            db.add(Goal(user_id=uid,title=title.strip(),target_value=target,current_value=current,unit=unit))
            db.commit();st.rerun()
    goals=owned(db,Goal,uid)
    for goal in goals:
        st.write("**"+goal.title+"**")
        st.progress(float(min(max(goal.current_value/goal.target_value if goal.target_value else 0,0),1)))
        st.caption(f"{goal.current_value:g} {goal.unit} / {goal.target_value:g} {goal.unit}")
    if goals:
        chosen=st.selectbox("Delete goal",[g.id for g in goals])
        if st.button("Remove goal"):
            delete_owned(db,Goal,uid,chosen);st.rerun()


def predictions_page(marks):
    st.subheader("🔮 Subject predictions and insights")
    st.caption("Linear trend estimates are experimental, not guaranteed marks.")
    df=predict_subjects(marks)
    if df.empty:
        st.info("Subject-wise prediction requires the same subject recorded in at least two different semesters.")
        return
    st.dataframe(df,hide_index=True,use_container_width=True)
    st.plotly_chart(chart_style(px.bar(df,x="Subject",y=["Latest %","Next estimated %"],barmode="group")),
                    use_container_width=True)
    st.write("Prioritize subjects with the lowest next estimated percentages.")


def grading_page(db,uid,marks,thresholds):
    st.subheader("⚙️ IU Grade Mapping · Configurable")
    st.warning("Default boundaries are DEMONSTRATION values, not verified Indus University rules. "
               "Confirm your official scheme and component-level pass requirements.")
    st.caption("Enter a grade point (0–10) for each minimum overall percentage.")
    editable=pd.DataFrame(thresholds,columns=["Minimum %","Grade point"])
    changed=st.data_editor(editable,hide_index=True,num_rows="fixed",use_container_width=True)
    if st.button("Save grading scheme",type="primary"):
        try:
            mins=list(pd.to_numeric(changed["Minimum %"]).astype(float))
            points=list(pd.to_numeric(changed["Grade point"]).astype(float))
            if len(set(mins))!=len(mins) or any(not 0<=x<=100 for x in mins) or any(not 0<=p<=10 for p in points):
                raise ValueError("Thresholds must be unique, 0–100%; points must be 0–10.")
            if 0 not in mins:
                raise ValueError("Keep a 0% fallback threshold.")
            for item in owned(db,GradeRule,uid):
                db.delete(item)
            db.flush()
            for m,p in zip(mins,points):
                db.add(GradeRule(user_id=uid,minimum=m,point=p))
            db.commit();st.success("Grading scheme saved.");st.rerun()
        except (ValueError,TypeError) as exc:
            db.rollback();st.error(str(exc))
    if not marks.empty:
        st.info(f"Current estimated CGPA under this account's scheme: {cgpa(marks):.2f}")


def make_pdf(db,uid,marks):
    buffer=io.BytesIO()
    document=SimpleDocTemplate(buffer,pagesize=A4,rightMargin=32,leftMargin=32,
                               topMargin=34,bottomMargin=34)
    styles=getSampleStyleSheet()
    story=[Paragraph("Academic Intelligence V3.0",styles["Title"]),
           Spacer(1,10),Paragraph("Student: "+escape(st.session_state["username"]),styles["Normal"]),
           Paragraph("Generated: "+datetime.now().strftime("%d %b %Y"),styles["Normal"]),
           Paragraph("Estimated CGPA: "+f"{cgpa(marks):.2f}",styles["Heading2"]),
           Spacer(1,12)]
    def add_table(title,headers,rows,widths=None):
        story.append(Paragraph(escape(title),styles["Heading2"]))
        if not rows:
            story.append(Paragraph("No records.",styles["Normal"]))
            return
        data=[[Paragraph(escape(str(cell)),styles["BodyText"]) for cell in headers]]
        for row in rows:
            data.append([Paragraph(escape(str(x)),styles["BodyText"]) for x in row])
        table=Table(data,colWidths=widths,repeatRows=1,hAlign="LEFT")
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),colors.HexColor("#e5e8ff")),
            ("GRID",(0,0),(-1,-1),.35,colors.HexColor("#aeb2c2")),
            ("VALIGN",(0,0),(-1,-1),"TOP"),
            ("FONTSIZE",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),7)
        ]))
        story.append(table);story.append(Spacer(1,10))
    semesters=summary(marks)
    add_table("Semester performance",["Semester","Average %","Estimated SGPA"],
              [(int(x.semester),f"{x.percentage:.1f}",f"{x.sgpa:.2f}") for _,x in semesters.iterrows()],
              [120,180,185])
    add_table("Marks",["Sem","Subject","Obtained","Max","%","GP"],
              [(int(x.semester),x.subject,f"{x.obtained:g}",f"{x.maximum:g}",
                f"{x.percentage:.1f}",f"{x.grade_point:g}") for _,x in marks.iterrows()],
              [40,205,60,60,55,65])
    add_table("Backlog components",["Sem","Subject","Component","Status"],
              [(x.semester,x.subject,x.component,x.status) for x in owned(db,Backlog,uid)],
              [52,175,145,113])
    add_table("Attendance",["Subject","Attended","Total"],
              [(x.subject,x.attended,x.total) for x in owned(db,Attendance,uid)],
              [245,120,120])
    add_table("Assignments",["Subject","Task","Status"],
              [(x.subject,x.title,x.status) for x in owned(db,Assignment,uid)],
              [145,240,100])
    add_table("Goals",["Goal","Current","Target"],
              [(x.title,f"{x.current_value:g} {x.unit}",f"{x.target_value:g} {x.unit}")
               for x in owned(db,Goal,uid)],[245,120,120])
    story.append(Paragraph("Grades and predictions are advisory estimates; verify official university rules.",
                           styles["Italic"]))
    document.build(story)
    return buffer.getvalue()


def report_page(db,uid,marks):
    st.subheader("📄 Professional academic report")
    st.caption("Only records belonging to your signed-in account are exported.")
    st.download_button("⬇️ Download PDF report",data=make_pdf(db,uid,marks),
                       file_name="Academic_Intelligence_V3_Report.pdf",mime="application/pdf",type="primary")
    if not marks.empty:
        st.download_button("⬇️ Download marks CSV",data=marks.to_csv(index=False),
                           file_name="Academic_V3_Marks.csv",mime="text/csv")


def about_page():
    st.subheader("ℹ️ Indus University Academic Intelligence V3.0")
    members()
    st.markdown("**Built with:** Streamlit, Python, SQLAlchemy, PostgreSQL/SQLite, "
                "Pandas, NumPy, Plotly and ReportLab.")
    st.write("**Features:** private accounts, subject marks, semester summaries, editable grading, "
             "target planning, backlog components, attendance, tasks, goals, predictions and PDF reports.")
    st.caption("Original V2 application remains available in the repository as app_v2_legacy.py.")


def run():
    st.set_page_config(page_title="Academic Intelligence V3.0",page_icon="🎓",
                       layout="wide",initial_sidebar_state="expanded")
    try:
        store()
    except Exception:
        st.error("Unable to connect to the academic database. Check DATABASE_URL configuration.")
        st.stop()
    if not st.session_state.get("user_id"):
        auth_screen()
        return
    page=navigation()
    header()
    if not durable_storage():
        st.warning("Temporary SQLite mode. Configure a durable PostgreSQL DATABASE_URL for production.")
    with engine_session() as db:
        uid=int(st.session_state["user_id"])
        from v3_core import User
        user=db.scalar(select(User).where(User.id==uid))
        if user is None:
            st.session_state.pop("user_id",None)
            st.rerun()
        marks,thresholds=get_rows(db,uid)
        if page=="Dashboard":dashboard(db,uid,marks,thresholds)
        elif page=="Marks Entry":marks_entry(db,uid,marks)
        elif page=="SGPA & CGPA":sgpa_page(marks)
        elif page=="9+ SGPA Planner":planner_page(marks,thresholds)
        elif page=="Target Calculator":target_page()
        elif page=="Backlog Tracker":backlog_page(db,uid)
        elif page=="Attendance":attendance_page(db,uid)
        elif page=="Assignments":assignment_page(db,uid)
        elif page=="Goals":goals_page(db,uid)
        elif page=="Predictions":predictions_page(marks)
        elif page=="Report":report_page(db,uid,marks)
        elif page=="Grading Settings":grading_page(db,uid,marks,thresholds)
        else:about_page()


if __name__=="__main__":
    run()
