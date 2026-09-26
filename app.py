import os
import json
import pandas as pd
import streamlit as st
from datetime import datetime

# Import modular application components
from modules.database import (
    init_db,
    authenticate_user,
    create_user,
    save_analysis_record,
    get_user_analysis_history,
    get_all_analyses,
    get_analysis_by_id,
    add_company_doc,
    get_company_docs,
    delete_company_doc,
    DB_TYPE,
    DB_STATUS_MSG
)
from modules.extractor import extract_document_text, inspect_ats_formatting, clean_text
from modules.keyword_analyzer import analyze_ats_keywords
from modules.llm_engine import (
    analyze_resume_llm,
    rewrite_resume_section_llm,
    generate_skill_gap_roadmap_llm,
    generate_job_recommendations_llm,
    interview_chatbot_turn,
    generate_mock_analysis
)
from modules.pdf_report import generate_ats_pdf_report
from modules.rag_engine import CompanyRAGEngine
from modules.visualizations import (
    create_ats_gauge,
    create_skill_radar,
    create_comparison_barchart,
    create_missing_skills_barchart,
    create_score_distribution_chart
)

# ============================================================
# INITIALIZATION & STREAMLIT CONFIG
# ============================================================
st.set_page_config(
    page_title="AI Resume Analyzer Pro | ATS & Recruitment Intelligence",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Database
init_db()

# Initialize Session State
if "user" not in st.session_state:
    st.session_state["user"] = {
        "id": 1,
        "username": "candidate",
        "email": "candidate@resumepro.ai",
        "role": "candidate",
        "full_name": "Alex Morgan"
    }

if "current_analysis" not in st.session_state:
    st.session_state["current_analysis"] = None

if "current_resume_text" not in st.session_state:
    st.session_state["current_resume_text"] = ""

if "current_filename" not in st.session_state:
    st.session_state["current_filename"] = ""

if "interview_messages" not in st.session_state:
    st.session_state["interview_messages"] = [
        {"role": "assistant", "content": "Hello! I am your AI Technical Interviewer today. Whenever you are ready, please introduce yourself and highlight a project you are particularly proud of."}
    ]

# Initialize RAG Engine
if "rag_engine" not in st.session_state:
    rag = CompanyRAGEngine()
    docs = get_company_docs()
    rag.build_index(docs)
    st.session_state["rag_engine"] = rag

# ============================================================
# CUSTOM CSS STYLING (Rich Aesthetics & Premium UI)
# ============================================================
st.markdown("""
<style>
    /* Main container refinements */
    .main {
        background-color: #F8FAFC;
    }
    
    /* Hero Title Banner */
    .hero-banner {
        background: linear-gradient(135deg, #1E1B4B 0%, #312E81 50%, #4338CA 100%);
        padding: 26px 32px;
        border-radius: 16px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 10px 25px -5px rgba(49, 46, 129, 0.2);
    }
    .hero-title {
        font-size: 30px;
        font-weight: 800;
        letter-spacing: -0.5px;
        margin-bottom: 6px;
        color: #FFFFFF;
    }
    .hero-subtitle {
        font-size: 15px;
        color: #C7D2FE;
        font-weight: 400;
    }

    /* Badges & Pills */
    .badge-pill {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px 4px;
    }
    .badge-green {
        background-color: #DCFCE7;
        color: #166534;
        border: 1px solid #BBF7D0;
    }
    .badge-red {
        background-color: #FEE2E2;
        color: #991B1B;
        border: 1px solid #FECACA;
    }
    .badge-amber {
        background-color: #FEF3C7;
        color: #92400E;
        border: 1px solid #FDE68A;
    }
    .badge-blue {
        background-color: #DBEAFE;
        color: #1E40AF;
        border: 1px solid #BFDBFE;
    }

    /* Feature card container */
    .custom-card {
        background: #FFFFFF;
        border-radius: 12px;
        padding: 20px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
        margin-bottom: 16px;
    }

    /* Score callout */
    .metric-value {
        font-size: 32px;
        font-weight: 800;
        color: #1E293B;
    }
    .metric-label {
        font-size: 13px;
        color: #64748B;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
</style>
""", unsafe_allow_html=True)


# ============================================================
# SIDEBAR: AUTH, API KEY & NAVIGATION
# ============================================================
with st.sidebar:
    st.markdown("### 🚀 AI Resume Analyzer Pro")
    st.caption("Enterprise ATS & Recruitment Platform")
    
    # Database Indicator Badge
    if DB_TYPE == "MySQL":
        st.success(f"🟢 **Storage**: {DB_STATUS_MSG}")
    else:
        st.info(f"💾 **Storage**: {DB_TYPE} (Local Auto-Fallback)")

    st.divider()

    # User Profile / Auth Section
    user = st.session_state.get("user")
    if user:
        st.markdown(f"👤 **Logged in as:** {user.get('full_name') or user.get('username')}")
        role_label = "👑 Recruiter / Admin" if user.get("role") == "recruiter_admin" else "💼 Job Seeker / Candidate"
        st.caption(f"Role: **{role_label}**")

        col_acc1, col_acc2 = st.columns(2)
        with col_acc1:
            if user.get("role") == "candidate":
                if st.button("Switch to Recruiter", use_container_width=True):
                    st.session_state["user"] = {
                        "id": 2, "username": "admin", "email": "admin@resumepro.ai",
                        "role": "recruiter_admin", "full_name": "Talent Admin"
                    }
                    st.rerun()
            else:
                if st.button("Switch to Candidate", use_container_width=True):
                    st.session_state["user"] = {
                        "id": 1, "username": "candidate", "email": "candidate@resumepro.ai",
                        "role": "candidate", "full_name": "Alex Morgan"
                    }
                    st.rerun()
        with col_acc2:
            if st.button("Log Out", use_container_width=True):
                st.session_state["user"] = None
                st.rerun()
    else:
        with st.expander("🔐 Login / Register", expanded=True):
            tab_login, tab_register = st.tabs(["Login", "Sign Up"])
            with tab_login:
                login_id = st.text_input("Username or Email", key="login_id", value="candidate")
                login_pwd = st.text_input("Password", type="password", key="login_pwd", value="Candidate@123")
                if st.button("Sign In", type="primary", use_container_width=True):
                    auth_user, msg = authenticate_user(login_id, login_pwd)
                    if auth_user:
                        st.session_state["user"] = auth_user
                        st.success("Signed in successfully!")
                        st.rerun()
                    else:
                        st.error(msg)
            with tab_register:
                reg_name = st.text_input("Full Name", key="reg_name")
                reg_user = st.text_input("Username", key="reg_user")
                reg_email = st.text_input("Email", key="reg_email")
                reg_pwd = st.text_input("Password", type="password", key="reg_pwd")
                reg_role = st.selectbox("Role", ["candidate", "recruiter_admin"], format_func=lambda x: "Candidate (Job Seeker)" if x == "candidate" else "Recruiter / Admin")
                if st.button("Create Account", use_container_width=True):
                    if reg_user and reg_email and reg_pwd:
                        new_u, reg_msg = create_user(reg_user, reg_email, reg_pwd, reg_role, reg_name)
                        if new_u:
                            st.success("Account created! Please sign in.")
                        else:
                            st.error(reg_msg)
                    else:
                        st.warning("Please fill in all fields.")

    st.divider()

    # Groq API Key Configuration
    env_key = os.getenv("GROQ_API_KEY", "")
    if not env_key:
        try:
            env_key = st.secrets.get("GROQ_API_KEY", "")
        except Exception:
            pass
    groq_api_key = st.text_input(
        "Groq API Key",
        value=env_key,
        type="password",
        help="Enter your Groq API Key from console.groq.com. If left blank, the app will use high-fidelity demo analysis mode."
    )
    if groq_api_key:
        os.environ["GROQ_API_KEY"] = groq_api_key
        st.caption("✅ Groq key active")
    else:
        st.caption("ℹ️ Demo Mode active (Smart Fallback)")

    st.divider()

    # Navigation Menu
    nav_options = [
        "📄 Single Resume Analyzer",
        "👥 Multi-Resume Comparison & Ranking",
        "✍️ AI Resume Rewriter",
        "🗺️ Skill-Gap & Learning Roadmap",
        "💼 AI Job Recommendations",
        "🔍 ATS Keyword & Format Audit",
        "🤖 Mock Interview Chatbot",
        "🏢 Company RAG & Culture Fit",
        "📜 Analysis History",
        "📊 Admin Analytics Dashboard"
    ]
    selected_page = st.radio("Navigate Features", nav_options, index=0)


# ============================================================
# PAGE 1: SINGLE RESUME ANALYZER (PDF + DOCX SUPPORT)
# ============================================================
if selected_page == "📄 Single Resume Analyzer":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">📄 AI Resume ATS Analyzer & Matcher</div>
        <div class="hero-subtitle">Upload your resume in PDF or DOCX format to receive an in-depth ATS evaluation, skill gap diagnostics, and executive PDF report.</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1], gap="medium")

    with col1:
        st.subheader("1. Upload Resume")
        uploaded_file = st.file_uploader(
            "Choose a Resume (PDF or DOCX)",
            type=["pdf", "docx"],
            help="Supports standard PDF resumes as well as Microsoft Word DOCX formats."
        )

        sample_btn = st.button("📂 Load Sample Trainee Resume", help="Load sample data to test instantly without uploading")

    with col2:
        st.subheader("2. Target Job Description")
        default_jd = """Trainee Software Engineer
We are seeking a Trainee Software Engineer with solid programming foundations.
Key Requirements:
- Python & Java fundamentals
- Object-Oriented Programming (OOP)
- Relational Databases: SQL and MySQL
- Data Structures and Algorithms (DSA)
- Git and version control
- Building RESTful APIs
- Problem solving & good communication

Good to Have:
- Docker containerization
- FastAPI or Spring Boot
- AWS cloud fundamentals"""
        job_description = st.text_area(
            "Job Description",
            value=default_jd,
            height=230,
            placeholder="Paste complete job description requirements here..."
        )

    target_role = st.text_input("Target Job Title (Optional)", value="Trainee Software Engineer")

    # Sample data loader trigger
    if sample_btn:
        st.session_state["current_resume_text"] = """Alex Morgan | Email: alex.morgan@example.com | Phone: (555) 234-5678 | GitHub: github.com/alexmorgan
EDUCATION:
B.S. in Computer Science, State University, 2024. GPA: 3.8/4.0
TECHNICAL SKILLS:
- Languages: Python, Java, SQL, C++
- Web & APIs: RESTful APIs, Flask, HTML5, CSS3, JSON
- Databases: MySQL, SQLite, PostgreSQL
- Developer Tools: Git, GitHub, VS Code, Linux, Postman
PROJECTS:
1. E-Commerce REST API Engine:
   - Designed and built a modular REST API using Python and Flask with MySQL database.
   - Implemented relational database schemas with normalization and foreign keys.
   - Built JWT-based authentication and tested endpoints using Postman.
2. Algorithm Visualizer:
   - Developed an interactive tool visualising sorting algorithms and tree traversals.
EXPERIENCE:
Software Engineering Intern, TechCorp (Summer 2023):
- Collaborated in a team of 4 to refactor database queries, reducing latency by 20%.
- Participated in weekly agile standups, code reviews, and Git feature branches."""
        st.session_state["current_filename"] = "sample_alex_morgan_resume.pdf"
        st.info("Loaded sample resume for Alex Morgan!")

    analyze_btn = st.button("🚀 Analyze Resume & Match ATS", type="primary", use_container_width=True)

    if analyze_btn:
        resume_text = ""
        filename = "resume.pdf"

        if uploaded_file is not None:
            filename = uploaded_file.name
            with st.spinner(f"Extracting text from '{filename}'..."):
                try:
                    resume_text = extract_document_text(uploaded_file, filename)
                except Exception as e:
                    st.error(f"Error reading file: {e}")
                    st.stop()
        elif st.session_state.get("current_resume_text"):
            resume_text = st.session_state["current_resume_text"]
            filename = st.session_state.get("current_filename", "sample_resume.pdf")
        else:
            st.warning("Please upload a resume file (PDF/DOCX) or load sample data.")
            st.stop()

        if not job_description.strip():
            st.warning("Please enter a target job description.")
            st.stop()

        if len(resume_text.split()) < 30:
            st.error("The uploaded resume contains very little readable text. Please ensure it is a text-based PDF or DOCX file.")
            st.stop()

        st.session_state["current_resume_text"] = resume_text
        st.session_state["current_filename"] = filename

        with st.spinner("Analyzing candidate profile against job description with AI..."):
            analysis_result = analyze_resume_llm(resume_text, job_description, groq_api_key)
            formatting_result = inspect_ats_formatting(resume_text, filename)

            st.session_state["current_analysis"] = analysis_result
            st.session_state["current_formatting"] = formatting_result

            # Save record to Database
            user_id = user["id"] if user else None
            candidate_name = formatting_result["contact_info"].get("detected_name") or "Candidate"
            candidate_email = formatting_result["contact_info"].get("email") or ""
            file_type = "docx" if filename.lower().endswith(".docx") else "pdf"

            record_id = save_analysis_record(
                user_id=user_id,
                candidate_name=candidate_name,
                candidate_email=candidate_email,
                file_name=filename,
                file_type=file_type,
                job_title=target_role,
                job_description=job_description,
                analysis_data=analysis_result
            )
            st.session_state["last_record_id"] = record_id
            st.success("✅ Analysis completed and saved to database successfully!")

    # DISPLAY ANALYSIS RESULTS
    if st.session_state.get("current_analysis"):
        res = st.session_state["current_analysis"]
        fmt = st.session_state.get("current_formatting", {})
        score = res.get("ats_score", 0)

        st.divider()
        st.header("📊 ATS Evaluation & Match Report")

        # Top Metric Cards & Gauge
        g_col1, g_col2 = st.columns([1.2, 1.8])
        with g_col1:
            gauge_fig = create_ats_gauge(score)
            st.plotly_chart(gauge_fig, use_container_width=True)

        with g_col2:
            radar_fig = create_skill_radar(res.get("category_scores", {}))
            st.plotly_chart(radar_fig, use_container_width=True)

        # Download PDF Action Button
        cand_name = fmt.get("contact_info", {}).get("detected_name") or "Candidate"
        pdf_bytes = generate_ats_pdf_report(
            candidate_name=cand_name,
            job_title=target_role,
            analysis_data=res,
            formatting_data=fmt
        )
        st.download_button(
            label="📥 Download Executive ATS Evaluation PDF Report",
            data=pdf_bytes,
            file_name=f"ATS_Report_{cand_name.replace(' ', '_')}.pdf",
            mime="application/pdf",
            type="primary",
            use_container_width=True
        )

        st.divider()

        # Detailed Breakdown Tabs
        tab_summary, tab_skills, tab_sw, tab_questions, tab_actions = st.tabs([
            "📋 Candidate Summary",
            "🎯 Skills Breakdown",
            "⚖️ Strengths & Weaknesses",
            "❓ Interview Prep",
            "🚀 Action Items"
        ])

        with tab_summary:
            st.subheader("Executive Candidate Overview")
            st.write(res.get("candidate_summary", "No summary available."))

            st.markdown("#### Domain Alignment Analysis")
            col_exp, col_edu, col_proj = st.columns(3)
            with col_exp:
                st.info(f"**Experience Match:**\n\n{res.get('experience_match', 'N/A')}")
            with col_edu:
                st.info(f"**Education Match:**\n\n{res.get('education_match', 'N/A')}")
            with col_proj:
                st.info(f"**Project Match:**\n\n{res.get('project_match', 'N/A')}")

        with tab_skills:
            col_match, col_miss = st.columns(2)
            with col_match:
                st.markdown("### ✅ Matched Skills (Present in Resume)")
                matched = res.get("matched_skills", [])
                if matched:
                    for s in matched:
                        st.markdown(f"<span class='badge-pill badge-green'>✓ {s}</span>", unsafe_allow_html=True)
                else:
                    st.caption("No strong matches identified.")

            with col_miss:
                st.markdown("### ❌ Missing Skills (Required by JD)")
                missing = res.get("missing_skills", [])
                if missing:
                    for s in missing:
                        st.markdown(f"<span class='badge-pill badge-red'>• {s}</span>", unsafe_allow_html=True)
                else:
                    st.caption("No major missing skills.")

            st.markdown("### 🟡 Partial / Emerging Skills")
            partial = res.get("partial_match_skills", [])
            for s in partial:
                st.markdown(f"<span class='badge-pill badge-amber'>~ {s}</span>", unsafe_allow_html=True)

        with tab_sw:
            col_str, col_weak = st.columns(2)
            with col_str:
                st.markdown("### 💪 Key Strengths")
                for s in res.get("strengths", []):
                    st.success(f"✓ {s}")
            with col_weak:
                st.markdown("### ⚠️ Areas for Improvement / Gaps")
                for w in res.get("weaknesses", []):
                    st.warning(f"• {w}")

        with tab_questions:
            st.subheader("AI-Generated Interview Questions")
            st.caption("Tailored specifically to this candidate's background against the target job requirements.")
            questions = res.get("interview_questions", [])
            for idx, q in enumerate(questions, start=1):
                st.markdown(f"**Q{idx}.** {q}")

        with tab_actions:
            st.subheader("Targeted Resume Improvements")
            for idx, imp in enumerate(res.get("resume_improvements", []), start=1):
                st.markdown(f"**{idx}.** {imp}")


# ============================================================
# PAGE 2: MULTI-RESUME COMPARISON & CANDIDATE RANKING
# ============================================================
elif selected_page == "👥 Multi-Resume Comparison & Ranking":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">👥 Multi-Resume Comparison & Candidate Ranking</div>
        <div class="hero-subtitle">Screen and rank multiple resumes (PDF/DOCX) against a single job description to generate recruiter leaderboards and side-by-side matrices.</div>
    </div>
    """, unsafe_allow_html=True)

    col_files, col_jd = st.columns([1, 1])

    with col_files:
        multi_files = st.file_uploader(
            "Upload Multiple Resumes (PDF / DOCX)",
            type=["pdf", "docx"],
            accept_multiple_files=True,
            help="Upload up to 10 resumes for batch evaluation"
        )
        sample_batch_btn = st.button("📂 Load 3 Sample Candidate Resumes", help="Quick demo batch")

    with col_jd:
        rank_jd = st.text_area(
            "Target Job Description for Ranking",
            height=200,
            value="""Senior Python Developer:
Requirements:
- 4+ years of Python engineering
- FastAPI or Django
- PostgreSQL, MySQL, Redis caching
- Docker, Kubernetes, AWS deployments
- CI/CD pipelines, Git, Unit Testing
- Strong system design and microservices architecture"""
        )

    candidates_to_process = []

    if sample_batch_btn:
        candidates_to_process = [
            {
                "name": "Sarah Chen",
                "filename": "sarah_chen_resume.pdf",
                "text": "Sarah Chen. Senior Backend Developer with 5 years experience. Skills: Python, FastAPI, Docker, Kubernetes, AWS, PostgreSQL, Redis, Microservices, CI/CD, Git. Built high throughput payment services."
            },
            {
                "name": "Michael Brown",
                "filename": "michael_brown.docx",
                "text": "Michael Brown. Python Developer with 2 years experience. Skills: Python, Django, MySQL, SQLite, HTML, CSS, JavaScript, Git. Developed client websites and simple database schemas."
            },
            {
                "name": "David Miller",
                "filename": "david_miller_resume.pdf",
                "text": "David Miller. Cloud & Python Engineer. Skills: Python, Flask, AWS Lambda, Docker, MySQL, Jenkins CI/CD, Terraform, Git, Linux. Designed automated cloud provisioning scripts."
            }
        ]
        st.session_state["sample_batch"] = candidates_to_process
        st.info("Loaded 3 sample candidate resumes: Sarah Chen, Michael Brown, David Miller.")
    elif multi_files:
        for f in multi_files:
            try:
                txt = extract_document_text(f, f.name)
                fmt = inspect_ats_formatting(txt, f.name)
                cand_name = fmt["contact_info"].get("detected_name") or f.name.replace(".pdf", "").replace(".docx", "")
                candidates_to_process.append({
                    "name": cand_name,
                    "filename": f.name,
                    "text": txt
                })
            except Exception as e:
                st.warning(f"Could not read {f.name}: {e}")

    if st.button("🏆 Screen & Rank Candidates", type="primary", use_container_width=True):
        if not candidates_to_process and "sample_batch" in st.session_state:
            candidates_to_process = st.session_state["sample_batch"]

        if not candidates_to_process:
            st.warning("Please upload multiple resumes or click 'Load 3 Sample Candidate Resumes'.")
            st.stop()

        with st.spinner(f"Evaluating and ranking {len(candidates_to_process)} candidate resumes..."):
            ranking_results = []
            for c in candidates_to_process:
                analysis = analyze_resume_llm(c["text"], rank_jd, groq_api_key)
                ranking_results.append({
                    "name": c["name"],
                    "filename": c["filename"],
                    "score": analysis.get("ats_score", 0),
                    "matched_skills": analysis.get("matched_skills", []),
                    "missing_skills": analysis.get("missing_skills", []),
                    "summary": analysis.get("candidate_summary", ""),
                    "experience_match": analysis.get("experience_match", ""),
                    "full_data": analysis
                })

            # Sort descending by ATS Score
            ranking_results.sort(key=lambda x: x["score"], reverse=True)
            st.session_state["batch_ranking"] = ranking_results
            st.success("Candidate ranking completed!")

    if "batch_ranking" in st.session_state:
        rankings = st.session_state["batch_ranking"]

        st.divider()
        st.header("🏆 Candidate Screening Leaderboard")

        # Visual Comparison Bar Chart
        comp_fig = create_comparison_barchart(rankings)
        st.plotly_chart(comp_fig, use_container_width=True)

        # Leaderboard Cards
        for idx, cand in enumerate(rankings, start=1):
            badge = "🏆 Rank #1 (Top Recommendation)" if idx == 1 else f"Rank #{idx}"
            score = cand["score"]
            score_cls = "badge-green" if score >= 80 else ("badge-amber" if score >= 60 else "badge-red")

            with st.container():
                st.markdown(f"""
                <div class="custom-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span class="badge-pill badge-blue">{badge}</span>
                            <span style="font-size:20px; font-weight:700; margin-left:10px;">{cand['name']}</span>
                            <span style="font-size:13px; color:#64748B;">({cand['filename']})</span>
                        </div>
                        <div>
                            <span class="badge-pill {score_cls}" style="font-size:16px;">{score}% ATS MATCH</span>
                        </div>
                    </div>
                    <p style="margin-top:10px; color:#334155; font-size:14px;">{cand['summary']}</p>
                </div>
                """, unsafe_allow_html=True)

                col_det1, col_det2 = st.columns(2)
                with col_det1:
                    st.write("**Matched Skills:**", ", ".join(cand["matched_skills"][:6]) or "None")
                with col_det2:
                    st.write("**Missing Skills:**", ", ".join(cand["missing_skills"][:6]) or "None")

        # Export Leaderboard Table
        df_export = pd.DataFrame([
            {
                "Rank": i + 1,
                "Candidate Name": c["name"],
                "ATS Score": f"{c['score']}%",
                "Matched Count": len(c["matched_skills"]),
                "Missing Count": len(c["missing_skills"]),
                "File Name": c["filename"]
            }
            for i, c in enumerate(rankings)
        ])
        csv_data = df_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Export Candidate Ranking Table (CSV)",
            data=csv_data,
            file_name="candidate_ranking_leaderboard.csv",
            mime="text/csv",
            use_container_width=True
        )


# ============================================================
# PAGE 3: AI RESUME REWRITER
# ============================================================
elif selected_page == "✍️ AI Resume Rewriter":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">✍️ AI Resume Bullet & Section Rewriter</div>
        <div class="hero-subtitle">Transform generic, passive bullet points into high-impact, ATS-optimized achievements using Google's XYZ formula and action verbs.</div>
    </div>
    """, unsafe_allow_html=True)

    col_rew1, col_rew2 = st.columns(2)
    with col_rew1:
        rewrite_target = st.text_input("Target Role", value="Senior Backend Engineer")
        section_type = st.selectbox("Section Type", ["Experience Bullet Point", "Professional Summary", "Project Description"])
        original_content = st.text_area(
            "Original Text to Rewrite",
            height=180,
            value="Worked on the backend database and fixed bugs. Helped make the API run faster for customers."
        )
    with col_rew2:
        jd_context = st.text_area(
            "Target Job Context (Keywords to Inject)",
            height=250,
            value="Backend Engineer requirements: Python, MySQL query optimization, Redis caching, microservices, high concurrency, REST API latency reduction, CI/CD."
        )

    if st.button("✨ Rewrite with AI", type="primary", use_container_width=True):
        if not original_content.strip():
            st.warning("Please enter text to rewrite.")
        else:
            with st.spinner("Rewriting using executive action frameworks..."):
                res = rewrite_resume_section_llm(original_content, rewrite_target, jd_context, section_type, groq_api_key)
                st.session_state["rewrite_result"] = res

    if "rewrite_result" in st.session_state:
        rw = st.session_state["rewrite_result"]
        st.divider()
        st.subheader("💡 High-Impact Rewritten Variations")

        # Variation 1: Metric-Driven
        with st.container():
            st.markdown("#### 1. 📈 Quantifiable Metric-Driven (Google XYZ Formula)")
            st.info(rw.get("metric_driven", ""))

        # Variation 2: ATS Keyword Dense
        with st.container():
            st.markdown("#### 2. 🎯 ATS Keyword-Dense (Engineered for Keyword Parsers)")
            st.success(rw.get("ats_keyword_dense", ""))

        # Variation 3: Executive Action
        with st.container():
            st.markdown("#### 3. 👑 Executive & Leadership Scope (High Ownership)")
            st.warning(rw.get("executive_action", ""))

        st.markdown("#### 🔍 Improvements Breakdown")
        for change in rw.get("key_changes_made", []):
            st.write(f"• {change}")

        st.write("**ATS Keywords Injected:**", ", ".join(rw.get("ats_keywords_injected", [])))


# ============================================================
# PAGE 4: SKILL-GAP & LEARNING ROADMAP
# ============================================================
elif selected_page == "🗺️ Skill-Gap & Learning Roadmap":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🗺️ Skill-Gap Diagnostics & 4-Week Learning Roadmap</div>
        <div class="hero-subtitle">Bridge the gap between your current technical abilities and job requirements with a personalized, curriculum-grade study plan.</div>
    </div>
    """, unsafe_allow_html=True)

    default_skills = "Docker, Kubernetes, AWS ECS, FastAPI, Redis"
    if st.session_state.get("current_analysis"):
        miss = st.session_state["current_analysis"].get("missing_skills", [])
        if miss:
            default_skills = ", ".join(miss)

    col_sg1, col_sg2 = st.columns(2)
    with col_sg1:
        target_goal = st.text_input("Target Position", value="Full Stack Cloud Developer")
    with col_sg2:
        missing_skills_input = st.text_input("Missing Skills (comma separated)", value=default_skills)

    if st.button("🚀 Generate Personalized 4-Week Roadmap", type="primary", use_container_width=True):
        skills_list = [s.strip() for s in missing_skills_input.split(",") if s.strip()]
        with st.spinner("Generating step-by-step learning roadmap..."):
            roadmap = generate_skill_gap_roadmap_llm(skills_list, target_goal, groq_api_key)
            st.session_state["roadmap_result"] = roadmap

    if "roadmap_result" in st.session_state:
        rm = st.session_state["roadmap_result"]
        st.divider()
        st.subheader(f"📚 4-Week Mastery Roadmap for {rm.get('target_role')}")
        st.caption(f"Estimated Commitment: ~{rm.get('estimated_total_hours', 40)} Total Study & Build Hours")

        for week in rm.get("weeks", []):
            with st.expander(f"🗓️ Week {week.get('week_number')}: {week.get('title')}", expanded=True):
                st.write("**Skills Covered:**", ", ".join(week.get("skills_covered", [])))
                st.write("**Key Concepts to Learn:**")
                for topic in week.get("key_topics", []):
                    st.write(f"- {topic}")
                st.markdown(f"🔨 **Hands-On Capstone Project:** {week.get('hands_on_project')}")
                st.caption(f"📖 Recommended Resources: {', '.join(week.get('recommended_resources', []))}")

        st.markdown("### 🏅 Recommended High-ROI Certifications")
        for cert in rm.get("high_value_certifications", []):
            st.markdown(f"<span class='badge-pill badge-blue'>🏆 {cert}</span>", unsafe_allow_html=True)


# ============================================================
# PAGE 5: AI JOB RECOMMENDATIONS
# ============================================================
elif selected_page == "💼 AI Job Recommendations":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">💼 AI Career & Job Role Recommendations</div>
        <div class="hero-subtitle">Discover top matching career pathways, typical salary brackets, and search strategies tailored to your unique skill profile.</div>
    </div>
    """, unsafe_allow_html=True)

    current_text = st.session_state.get("current_resume_text", "")
    if not current_text:
        st.info("💡 Upload a resume in the 'Single Resume Analyzer' tab or paste resume text below:")
        current_text = st.text_area("Paste Resume Text", height=150, value="Python, SQL, REST APIs, MySQL, Git, Flask, Data Structures")

    if st.button("🔎 Match Career Opportunities", type="primary", use_container_width=True):
        with st.spinner("Analyzing candidate profile against market demand..."):
            recs = generate_job_recommendations_llm(current_text, groq_api_key)
            st.session_state["job_recs"] = recs

    if "job_recs" in st.session_state:
        recs = st.session_state["job_recs"]
        st.divider()
        st.subheader("🎯 Top Matching Job Roles")

        for r in recs:
            pct = r.get("match_percentage", 85)
            with st.container():
                st.markdown(f"""
                <div class="custom-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <h3 style="margin:0; color:#1E293B;">{r.get('job_title')}</h3>
                        <span class="badge-pill badge-green" style="font-size:15px;">{pct}% Match</span>
                    </div>
                    <p style="margin:8px 0; color:#4F46E5; font-weight:600;">💰 Estimated Compensation: {r.get('typical_salary_range', '$90k - $130k')}</p>
                    <p style="color:#334155; font-size:14px;"><b>Why You Match:</b> {r.get('why_you_match')}</p>
                    <p style="color:#64748B; font-size:13px;"><b>Core Skills:</b> {', '.join(r.get('required_core_skills', []))}</p>
                    <a href="https://www.linkedin.com/jobs/search/?keywords={r.get('search_query', 'Python')}" target="_blank" style="text-decoration:none;">
                        <button style="background-color:#0A66C2; color:white; border:none; padding:6px 14px; border-radius:6px; font-weight:600; cursor:pointer;">
                            Search on LinkedIn ↗
                        </button>
                    </a>
                </div>
                """, unsafe_allow_html=True)


# ============================================================
# PAGE 6: ATS KEYWORD & FORMAT AUDIT
# ============================================================
elif selected_page == "🔍 ATS Keyword & Format Audit":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🔍 ATS Keyword Density & Format Inspector</div>
        <div class="hero-subtitle">Perform a diagnostic check on keyword frequency, missing high-priority technical terms, and structural ATS readability.</div>
    </div>
    """, unsafe_allow_html=True)

    col_k1, col_k2 = st.columns(2)
    with col_k1:
        res_sample = st.session_state.get("current_resume_text") or "Python developer with experience in MySQL, REST APIs, Git, and database design."
        kw_resume = st.text_area("Resume Text", value=res_sample, height=180)
    with col_k2:
        kw_jd = st.text_area("Job Description", value="Looking for Python, MySQL, Docker, Kubernetes, AWS, REST APIs, Git, and Microservices.", height=180)

    if st.button("🔬 Run Deep Keyword Audit", type="primary", use_container_width=True):
        kw_data = analyze_ats_keywords(kw_resume, kw_jd)
        fmt_data = inspect_ats_formatting(kw_resume, "resume_audit.pdf")

        st.session_state["keyword_audit"] = kw_data
        st.session_state["format_audit"] = fmt_data

    if "keyword_audit" in st.session_state:
        kd = st.session_state["keyword_audit"]
        fd = st.session_state["format_audit"]

        st.divider()

        # Metric Header
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("Keyword Match %", f"{kd['match_percentage']}%")
        m_col2.metric("Matched Keywords", f"{kd['matched_count']} / {kd['total_jd_keywords']}")
        m_col3.metric("Missing Keywords", kd['missing_count'])
        m_col4.metric("ATS Format Score", f"{fd['format_score']}%")

        col_kw_l, col_kw_r = st.columns(2)
        with col_kw_l:
            st.subheader("🔥 High-Priority Missing Keywords")
            st.caption("Skills appearing frequently in JD that are absent from resume:")
            high_miss = kd["high_priority_missing"]
            if high_miss:
                for kw in high_miss:
                    st.markdown(f"<span class='badge-pill badge-red'>❌ {kw}</span>", unsafe_allow_html=True)
            else:
                st.success("No high-priority missing keywords!")

        with col_kw_r:
            st.subheader("✅ Present Keywords & Density")
            matched_kws = kd["matched_keywords"]
            if matched_kws:
                df_kws = pd.DataFrame(matched_kws)
                st.dataframe(df_kws, use_container_width=True, height=220)
            else:
                st.info("No matching keywords detected.")

        st.divider()
        st.subheader("📋 ATS Document Format Health")
        f_col1, f_col2 = st.columns(2)
        with f_col1:
            st.write("**Detected Standard Sections:**")
            for sec in fd.get("found_sections", []):
                st.markdown(f"✓ {sec}")
            if fd.get("missing_sections"):
                st.write("**Missing Standard Sections:**")
                for sec in fd.get("missing_sections", []):
                    st.markdown(f"<font color='orange'>• {sec}</font>", unsafe_allow_html=True)

        with f_col2:
            st.write("**Formatting Diagnostics & Warnings:**")
            warnings = fd.get("warnings", [])
            if warnings:
                for w in warnings:
                    st.warning(w)
            else:
                st.success("No structural formatting issues detected. Highly ATS friendly!")


# ============================================================
# PAGE 7: MOCK INTERVIEW CHATBOT
# ============================================================
elif selected_page == "🤖 Mock Interview Chatbot":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🤖 AI Interactive Mock Interview Simulator</div>
        <div class="hero-subtitle">Practice live technical and behavioral interviews. The AI acts as your hiring manager, dynamically scoring your answers and providing instant STAR feedback.</div>
    </div>
    """, unsafe_allow_html=True)

    # Context Header
    with st.expander("⚙️ Configure Interview Context", expanded=False):
        int_role = st.text_input("Target Role", value="Python Software Engineer")
        int_context = st.text_area("Target Skills / Job Context", value="Python, OOP, REST APIs, SQL, Data Structures, Git")

    # Display chat conversation
    for msg in st.session_state["interview_messages"]:
        if msg["role"] == "assistant":
            with st.chat_message("assistant", avatar="🤖"):
                st.write(msg["content"])
                if "feedback" in msg:
                    st.info(f"💡 **AI Feedback (Score: {msg.get('score', 8)}/10):**\n\n{msg['feedback']}")
        else:
            with st.chat_message("user", avatar="👤"):
                st.write(msg["content"])

    # Chat Input
    user_reply = st.chat_input("Type your interview response here...")

    if user_reply:
        # Append user response
        st.session_state["interview_messages"].append({"role": "user", "content": user_reply})

        with st.spinner("AI Hiring Manager is evaluating your answer..."):
            history = [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state["interview_messages"]
            ]
            feedback_res = interview_chatbot_turn(
                conversation_history=history,
                job_description=int_context,
                resume_summary=st.session_state.get("current_resume_text", "")[:300],
                api_key=groq_api_key
            )

            # Append assistant message with feedback
            assistant_msg = {
                "role": "assistant",
                "content": feedback_res.get("next_question", "What is your experience with database optimization?"),
                "feedback": feedback_res.get("feedback", ""),
                "score": feedback_res.get("evaluation_score", 8)
            }
            st.session_state["interview_messages"].append(assistant_msg)
            st.rerun()

    if st.button("🔄 Reset Interview Session"):
        st.session_state["interview_messages"] = [
            {"role": "assistant", "content": "Hello! I am your AI Technical Interviewer today. Whenever you are ready, please introduce yourself and highlight a project you are particularly proud of."}
        ]
        st.rerun()


# ============================================================
# PAGE 8: COMPANY RAG & CULTURE FIT
# ============================================================
elif selected_page == "🏢 Company RAG & Culture Fit":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">🏢 Company RAG Knowledge Base & Culture Alignment</div>
        <div class="hero-subtitle">Upload company culture codes, engineering handbooks, and values to verify organizational alignment and query company docs with AI retrieval.</div>
    </div>
    """, unsafe_allow_html=True)

    tab_eval, tab_qa, tab_manage = st.tabs([
        "🤝 Candidate-Company Fit Evaluation",
        "💬 Interactive Company Doc Q&A",
        "📂 Manage Company Knowledge Docs"
    ])

    rag: CompanyRAGEngine = st.session_state["rag_engine"]

    with tab_eval:
        st.subheader("Evaluate Resume Against Company Culture & Standards")
        resume_for_fit = st.session_state.get("current_resume_text") or "Python developer with strong collaborative habits, code review experience, and fast prototyping."

        if st.button("🔍 Evaluate Cultural & Technical Alignment", type="primary", use_container_width=True):
            with st.spinner("Running semantic retrieval over company guidelines..."):
                fit_result = rag.evaluate_company_culture_fit(resume_for_fit, groq_api_key)
                st.session_state["culture_fit_result"] = fit_result

        if "culture_fit_result" in st.session_state:
            cf = st.session_state["culture_fit_result"]
            fit_score = cf.get("culture_fit_score", 85)
            st.metric("Company Alignment Score", f"{fit_score}%")
            st.write("**Values & Engineering Standards Alignment:**")
            st.info(cf.get("values_alignment"))

            col_cf1, col_cf2 = st.columns(2)
            with col_cf1:
                st.markdown("#### ✅ Alignment Strengths")
                for s in cf.get("strengths_for_company", []):
                    st.success(f"✓ {s}")
            with col_cf2:
                st.markdown("#### 🎯 Behavioral Exploration Areas")
                for a in cf.get("areas_to_explore_in_interview", []):
                    st.warning(f"• {a}")

    with tab_qa:
        st.subheader("Ask Questions to the Company Knowledge Base (RAG)")
        sample_q = st.selectbox(
            "Quick Questions",
            [
                "What is our core tech stack and backend framework?",
                "What are NexusTech core cultural values?",
                "What are the expectations regarding code reviews and testing?"
            ]
        )
        custom_q = st.text_input("Or enter custom question:", value=sample_q)

        if st.button("Search Knowledge Base"):
            with st.spinner("Retrieving relevant passages and synthesizing answer..."):
                answer = rag.answer_query(custom_q, groq_api_key)
                st.markdown("### Answer")
                st.write(answer)

    with tab_manage:
        st.subheader("Uploaded Company Documents")
        docs = get_company_docs()
        for d in docs:
            with st.expander(f"📄 {d['title']} ({d['doc_type']}) - Uploaded {d['created_at']}"):
                st.text(d['content'][:500] + "...")
                if st.button(f"🗑️ Delete Document #{d['id']}", key=f"del_{d['id']}"):
                    delete_company_doc(d['id'])
                    # Rebuild RAG index
                    rag.build_index(get_company_docs())
                    st.success("Deleted document and updated vector index.")
                    st.rerun()

        st.divider()
        st.subheader("Add New Company Document")
        new_doc_title = st.text_input("Document Title", placeholder="e.g., NexusTech Onboarding Guide")
        new_doc_type = st.selectbox("Category", ["culture", "tech_stack", "handbook", "job_spec"])
        new_doc_content = st.text_area("Document Content", height=150, placeholder="Paste policy, values, or architecture guidelines...")

        if st.button("Add to Knowledge Base"):
            if new_doc_title and new_doc_content:
                add_company_doc(new_doc_title, new_doc_type, new_doc_content, uploaded_by=user.get("username", "admin"))
                rag.build_index(get_company_docs())
                st.success("Document indexed into RAG engine!")
                st.rerun()
            else:
                st.warning("Please provide a title and content.")


# ============================================================
# PAGE 9: RESUME HISTORY & RELOAD
# ============================================================
elif selected_page == "📜 Analysis History":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">📜 Resume Analysis History</div>
        <div class="hero-subtitle">Browse your past evaluations, reload full diagnostic reports, and re-download PDF executive summaries without re-running LLM inferences.</div>
    </div>
    """, unsafe_allow_html=True)

    user_id = user["id"] if user else None
    history_records = get_user_analysis_history(user_id=user_id, limit=30)

    if not history_records:
        st.info("No prior analysis records found for this account. Run an analysis in 'Single Resume Analyzer' to see your history.")
    else:
        st.write(f"Showing **{len(history_records)}** past evaluation records:")
        for r in history_records:
            score = r["ats_score"]
            score_cls = "badge-green" if score >= 80 else ("badge-amber" if score >= 60 else "badge-red")

            with st.container():
                st.markdown(f"""
                <div class="custom-card">
                    <div style="display:flex; justify-content:space-between; align-items:center;">
                        <div>
                            <span style="font-size:18px; font-weight:700;">{r['candidate_name']}</span>
                            <span class="badge-pill badge-blue">{r['job_title']}</span>
                            <span style="font-size:12px; color:#64748B;">({r['file_name']}) • {r['created_at']}</span>
                        </div>
                        <div>
                            <span class="badge-pill {score_cls}" style="font-size:16px;">{score}% ATS</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_h1, col_h2 = st.columns([1, 1])
                with col_h1:
                    if st.button(f"🔄 Reload Full Report #{r['id']}", key=f"reload_{r['id']}", use_container_width=True):
                        st.session_state["current_analysis"] = r["full_analysis"]
                        st.session_state["current_filename"] = r["file_name"]
                        st.success(f"Loaded record #{r['id']} into memory! Navigate to 'Single Resume Analyzer' to view.")
                with col_h2:
                    pdf_data = generate_ats_pdf_report(
                        candidate_name=r["candidate_name"],
                        job_title=r["job_title"],
                        analysis_data=r["full_analysis"]
                    )
                    st.download_button(
                        label=f"📥 Download PDF #{r['id']}",
                        data=pdf_data,
                        file_name=f"Report_{r['candidate_name'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"dl_{r['id']}",
                        use_container_width=True
                    )


# ============================================================
# PAGE 10: ADMIN & RECRUITER ANALYTICS DASHBOARD
# ============================================================
elif selected_page == "📊 Admin Analytics Dashboard":
    st.markdown("""
    <div class="hero-banner">
        <div class="hero-title">📊 Recruiter & Admin Talent Pool Intelligence</div>
        <div class="hero-subtitle">High-level insights across applicant submissions, score distributions, and market skill shortages.</div>
    </div>
    """, unsafe_allow_html=True)

    all_records = get_all_analyses(limit=300)

    # Top KPI Metrics
    total_resumes = len(all_records)
    avg_score = round(sum(r["ats_score"] for r in all_records) / max(total_resumes, 1), 1) if all_records else 0
    top_candidates_count = sum(1 for r in all_records if r["ats_score"] >= 80)

    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total Resumes Analyzed", total_resumes)
    kpi2.metric("Average ATS Score", f"{avg_score}%")
    kpi3.metric("Top Performers (≥80%)", top_candidates_count)
    kpi4.metric("Storage Engine", DB_TYPE)

    st.divider()

    # Visual Analytics Charts
    c_col1, c_col2 = st.columns(2)
    with c_col1:
        dist_fig = create_score_distribution_chart(all_records)
        st.plotly_chart(dist_fig, use_container_width=True)

    with c_col2:
        missing_fig = create_missing_skills_barchart(all_records)
        st.plotly_chart(missing_fig, use_container_width=True)

    st.divider()
    st.subheader("📑 Candidate Database Records")
    if all_records:
        df_all = pd.DataFrame([
            {
                "ID": r["id"],
                "Candidate": r["candidate_name"],
                "Job Title": r["job_title"],
                "File": r["file_name"],
                "ATS Score": f"{r['ats_score']}%",
                "Date": r["created_at"]
            }
            for r in all_records
        ])
        st.dataframe(df_all, use_container_width=True)
    else:
        st.info("No candidates in database yet.")


# ============================================================
# FOOTER
# ============================================================
st.divider()
st.caption("AI Resume Analyzer Pro • Built with Streamlit, Groq LLM (Llama 3.3), ReportLab, SQLAlchemy & Plotly • Portfolio Ready")
