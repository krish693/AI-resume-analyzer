# 🚀 AI Resume Analyzer Pro & Recruitment Intelligence Platform

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.35%2B-FF4B4B.svg)](https://streamlit.io/)
[![Groq](https://img.shields.io/badge/LLM-Groq%20Llama%203.3%2070B-orange.svg)](https://groq.com/)
[![Database](https://img.shields.io/badge/Database-MySQL%20%7C%20SQLite%20Fallback-00758F.svg)](https://www.mysql.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

An **enterprise-grade, portfolio-level AI Recruitment & ATS Intelligence Platform** built with **Python**, **Streamlit**, and **Groq (Llama 3.3 70B)**. 

Transforming a basic resume analyzer MVP into a complete talent intelligence suite for both **Job Seekers** and **Technical Recruiters**.

---

## 🌟 Key Features Overview (15 Major Additions)

| # | Feature | Description |
|---|---|---|
| 1 | **DOCX Resume Support** | Native parsing for Microsoft Word `.docx` documents (including tables) alongside standard PDFs. |
| 2 | **Multiple Resume Comparison** | Side-by-side comparative matrices, score distribution, and metric overlays for up to 10 candidates simultaneously. |
| 3 | **Downloadable Executive PDF Report** | High-fidelity, styled PDF reports generated dynamically with ReportLab, featuring category cards, skill lists, and recommendations. |
| 4 | **AI Resume Rewriter** | Bullet point and section optimizer transforming weak descriptions into high-impact achievements using Google's XYZ formula. |
| 5 | **Skill-Gap Analysis & Roadmap** | Actionable 4-week learning roadmap with hands-on projects, study topics, and recommended certifications for missing skills. |
| 6 | **AI Job Recommendations** | Career pathway matcher mapping candidate skills to top 5 industry job roles, salary bands, and direct search queries. |
| 7 | **ATS Keyword Density Analysis** | Keyword frequency counter, density inspector, and high/medium/low priority missing keyword alerts. |
| 8 | **Candidate Ranking Leaderboard** | Recruiter screening engine ranking candidates #1, #2, #3 by ATS Match Score with exportable CSV tables. |
| 9 | **MySQL + SQLite Auto-Fallback** | SQLAlchemy ORM supporting production MySQL databases with seamless zero-config SQLite local fallback. |
| 10 | **Role-Based Auth & Sessions** | Secure user registration and login with bcrypt password hashing, supporting Candidate and Recruiter/Admin roles. |
| 11 | **Admin & Recruiter Dashboard** | Talent pool analytics, score distribution histograms, applicant tracking, and talent shortage heatmaps. |
| 12 | **Resume Analysis History** | Chronological audit trail of past scans; reload full diagnostic views and re-download PDF reports with one click. |
| 13 | **AI Mock Interview Chatbot** | Interactive conversational interview simulator with real-time scoring, STAR-method feedback, and technical follow-ups. |
| 14 | **Company RAG & Culture Fit** | Retrieval-Augmented Generation over uploaded company handbooks, culture docs, and engineering standards for culture fit scoring. |
| 15 | **Streamlit Cloud Deployment Ready** | Pre-configured `.streamlit/config.toml`, clean `requirements.txt`, environment templates, and secrets handling. |

---

## 🏗️ Architecture & Data Flow

```text
                                  USER INTERFACE
             ┌────────────────────────────────────────────────────────┐
             │       Streamlit Multi-Feature Web Application         │
             │   (Candidate Portal  &  Recruiter / Admin Console)    │
             └───────────────────────────┬────────────────────────────┘
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   │                                           │
                   ▼                                           ▼
      Single / Multi Document Ingestion               Knowledge Base (RAG)
      ├── PDF Parser (PyPDF / PyMuPDF)                ├── Company Culture Docs
      └── DOCX Parser (python-docx)                   └── TF-IDF / Vector Retrieval
                   │                                           │
                   └─────────────────────┬─────────────────────┘
                                         ▼
                             Intelligence Processing
                   ┌───────────────────────────────────────────┐
                   │ • ATS Keyword Frequency & Density Engine  │
                   │ • Document Format & Structure Auditor     │
                   │ • Prompt Engineering Orchestration        │
                   └─────────────────────┬─────────────────────┘
                                         │
                                         ▼
                             Groq High-Speed LLM
                    (Llama 3.3 70B Versatile / Llama 3.1 8B)
                                         │
                   ┌─────────────────────┴─────────────────────┐
                   ▼                                           ▼
          Visual & File Outputs                         Data Persistence
      ├── Plotly Semicircle Gauge                 ├── SQLAlchemy ORM
      ├── 5-Axis Radar Competency Chart           ├── MySQL (Production)
      ├── Executive PDF Report (ReportLab)        └── SQLite (Auto-Fallback)
      └── Candidate Ranking CSV Export
```

---

## 🛠️ Project Structure

```text
├── app.py                      # Main Streamlit web application & routing
├── requirements.txt            # Python dependencies
├── .env.example                # Template for environment variables
├── .gitignore                  # Git exclusions
├── README.md                   # Complete documentation & deployment guide
├── resume_analyzer.db          # Auto-generated SQLite database (when local)
│
├── modules/
│   ├── database.py             # SQLAlchemy models, MySQL + SQLite connection & CRUD
│   ├── extractor.py            # PDF & DOCX text parsing & formatting checks
│   ├── keyword_analyzer.py     # ATS keyword matching, density & frequency audit
│   ├── llm_engine.py           # Groq LLM wrapper, prompts, JSON parsers & fallbacks
│   ├── pdf_report.py           # Executive PDF report builder with ReportLab
│   ├── rag_engine.py           # RAG document indexing, semantic Q&A & culture fit
│   └── visualizations.py       # Plotly charts (gauge, radar, comparisons, histograms)
│
└── .streamlit/
    └── config.toml             # Theme settings (colors, fonts, server configuration)
```

---

## ⚡ Quick Start (Local Setup)

### 1. Clone the repository
```bash
git clone https://github.com/your-username/ai-resume-analyzer-pro.git
cd ai-resume-analyzer-pro
```

### 2. Create and activate a virtual environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables (Optional)
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```
Fill in your Groq API key:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
```
> **Tip:** You can obtain a free Groq API key from [Groq Console](https://console.groq.com/keys). If you do not provide a key, the application automatically runs in **Intelligent Demo Mode** with realistic heuristics, so you can test all UI features and workflows immediately!

### 5. Launch the application
```bash
streamlit run app.py
```
Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 🗄️ MySQL Database Setup (Optional)

The application has **built-in zero-config SQLite auto-fallback**. If MySQL credentials are not provided or if MySQL is unreachable, it automatically initializes and uses a local SQLite database (`resume_analyzer.db`).

To connect to a live MySQL database:
1. Create a MySQL database:
   ```sql
   CREATE DATABASE resume_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
   ```
2. In `.env`, configure:
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=resume_db
   ```
   Or set `DATABASE_URL`:
   ```env
   DATABASE_URL=mysql+pymysql://root:your_password@localhost:3306/resume_db
   ```

---

## 👥 Default Demo Accounts

Initial seed credentials are created automatically on first run:

| Role | Username | Email | Password |
|---|---|---|---|
| **Recruiter / Admin** | `admin` | `admin@resumepro.ai` | `Admin@123` |
| **Candidate** | `candidate` | `candidate@resumepro.ai` | `Candidate@123` |

*(You can also register brand new candidate or recruiter accounts via the Sign Up tab).*

---

## ☁️ Deployment to Streamlit Cloud

1. **Push your code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "feat: AI Resume Analyzer Pro complete portfolio release"
   git branch -M main
   git remote add origin https://github.com/your-username/ai-resume-analyzer-pro.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Community Cloud**:
   - Go to [share.streamlit.io](https://share.streamlit.io/).
   - Click **New app** and select your repository and `main` branch.
   - Set **Main file path** to `app.py`.

3. **Configure Secrets in Streamlit Cloud Settings**:
   Under **App Settings > Secrets**, paste:
   ```toml
   GROQ_API_KEY = "gsk_your_groq_api_key_here"

   # Optional: If connecting to a cloud MySQL (e.g. PlanetScale, AWS RDS, Aiven)
   # DATABASE_URL = "mysql+pymysql://user:password@cloud-host:3306/resume_db"
   ```

4. Click **Deploy!** Your application is now live on the web with a public HTTPS URL.

---

## 📄 License
This project is open-source under the [MIT License](LICENSE).
