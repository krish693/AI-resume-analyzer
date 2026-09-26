import os
import json
import re
import logging
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"


def get_groq_client(api_key: str = None) -> Groq:
    """Creates a Groq client from argument, st.secrets, or environment."""
    key = api_key or os.getenv("GROQ_API_KEY")
    if not key:
        return None
    return Groq(api_key=key.strip())


def parse_json_safely(content: str) -> dict:
    """Extracts and parses JSON from raw LLM response."""
    if not content:
        raise ValueError("Empty response received from LLM.")
    
    cleaned = content.strip()
    cleaned = re.sub(r"^```json\s*", "", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^```\s*", "", cleaned)
    cleaned = re.sub(r"\s*```$", "", cleaned)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start != -1 and end != -1:
            return json.loads(cleaned[start:end + 1])
        raise ValueError("Could not parse structured JSON from model response.")


# ============================================================
# RESUME ANALYSIS LLM
# ============================================================
def analyze_resume_llm(resume_text: str, job_description: str, api_key: str = None) -> dict:
    """
    Sends resume and JD to Groq LLM for comprehensive ATS analysis.
    If no API key is provided, returns high-fidelity fallback analysis.
    """
    client = get_groq_client(api_key)
    if not client:
        return generate_mock_analysis(resume_text, job_description)

    prompt = f"""
You are an elite Fortune 500 Technical Recruiter and ATS Evaluation Engine.
Analyze the candidate's resume strictly against the provided job description.
Return a STRICT, VALID JSON response with NO conversational text.

Response Schema:
{{
    "ats_score": 85,
    "candidate_summary": "Comprehensive 3-4 sentence professional summary of candidate fit...",
    "category_scores": {{
        "technical_skills": 85,
        "experience": 80,
        "education": 90,
        "soft_skills": 75,
        "tools_technologies": 80
    }},
    "matched_skills": ["Python", "SQL", "Git", "REST APIs"],
    "missing_skills": ["Docker", "Kubernetes", "AWS ECS"],
    "partial_match_skills": ["FastAPI", "CI/CD"],
    "strengths": [
        "Strong backend development experience with Python and relational databases.",
        "Demonstrated ability to architect RESTful services."
    ],
    "weaknesses": [
        "Lacks hands-on production experience with container orchestration (Docker/K8s).",
        "Limited exposure to cloud-native deployments on AWS."
    ],
    "experience_match": "Detailed evaluation of candidate's career trajectory vs JD requirements.",
    "education_match": "Evaluation of academic qualifications, degrees, or certifications.",
    "project_match": "Assessment of project complexity, relevance, and demonstrable outcomes.",
    "resume_improvements": [
        "Quantify project achievements with specific percentage metrics and throughput numbers.",
        "Add a dedicated Cloud & DevOps section highlighting any exposure to AWS or Docker.",
        "Restructure bullet points using Google's XYZ formula: Accomplished [X], as measured by [Y], by doing [Z]."
    ],
    "interview_questions": [
        "Can you explain your experience designing scalable REST APIs?",
        "How do you handle database index optimization in MySQL for high-traffic queries?",
        "Describe a time you diagnosed a performance bottleneck in Python.",
        "How would you approach containerizing your applications using Docker?",
        "Explain the difference between threading and multiprocessing in Python.",
        "What strategies do you use for secure API authentication?",
        "Describe your experience with automated testing and CI/CD pipelines.",
        "How do you resolve merge conflicts when collaborating in Git?",
        "Walk me through a challenging bug you encountered in production.",
        "What factors do you consider when selecting between SQL and NoSQL data stores?"
    ]
}}

Rules:
1. 'ats_score' must be an integer between 0 and 100.
2. 'category_scores' integers must be between 0 and 100.
3. Be objective, realistic, and constructive.
4. Only identify skills actually mentioned in the inputs.

RESUME TEXT:
{resume_text}

JOB DESCRIPTION:
{job_description}
"""

    models_to_try = [PRIMARY_MODEL, FALLBACK_MODEL]
    last_err = None

    for model_name in models_to_try:
        try:
            response = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are a professional ATS resume analyzer. Output valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                response_format={"type": "json_object"}
            )
            content = response.choices[0].message.content
            return parse_json_safely(content)
        except Exception as e:
            last_err = e
            logger.warning(f"Error calling model {model_name}: {e}. Retrying fallback if available.")

    logger.error(f"All LLM calls failed ({last_err}). Reverting to mock generator.")
    return generate_mock_analysis(resume_text, job_description)


# ============================================================
# RESUME REWRITING LLM
# ============================================================
def rewrite_resume_section_llm(original_text: str, target_role: str, job_description: str, section_type: str = "bullet_points", api_key: str = None) -> dict:
    """
    Rewrites bullet points, professional summaries, or project sections into high-impact, ATS-optimized versions.
    """
    client = get_groq_client(api_key)
    if not client:
        return generate_mock_rewrite(original_text, target_role, section_type)

    prompt = f"""
You are an executive resume coach and ATS optimization specialist.
The user wants you to rewrite the following {section_type} for the target role: "{target_role}".

Target Job Description Context:
{job_description[:800]}

Original Content:
\"\"\"{original_text}\"\"\"

Provide 3 tailored variations in valid JSON format:
{{
    "metric_driven": "Variation heavily emphasizing quantified business impact, percentages, scale, and XYZ formula.",
    "ats_keyword_dense": "Variation strategically packed with hard technical keywords and skills from the JD.",
    "executive_action": "Variation using strong leadership verbs, strategic scope, and ownership tone.",
    "key_changes_made": [
        "Replaced weak passive verbs with strong action verbs",
        "Added quantifiable placeholders and ATS keywords"
    ],
    "ats_keywords_injected": ["Keyword1", "Keyword2"]
}}

Return JSON ONLY.
"""

    try:
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert resume rewriter. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return parse_json_safely(response.choices[0].message.content)
    except Exception as e:
        logger.warning(f"Rewrite LLM failed: {e}. Returning fallback.")
        return generate_mock_rewrite(original_text, target_role, section_type)


# ============================================================
# SKILL GAP LEARNING ROADMAP LLM
# ============================================================
def generate_skill_gap_roadmap_llm(missing_skills: list, target_role: str, api_key: str = None) -> dict:
    """
    Generates a structured weekly learning roadmap for missing skills.
    """
    client = get_groq_client(api_key)
    if not client:
        return generate_mock_roadmap(missing_skills, target_role)

    skills_str = ", ".join(missing_skills[:8]) if missing_skills else "General Cloud & Backend Skills"

    prompt = f"""
You are a senior tech mentor and curriculum designer.
A candidate aiming for the role of "{target_role}" is missing the following skills:
{skills_str}

Create an actionable, practical 4-week learning roadmap in valid JSON:
{{
    "target_role": "{target_role}",
    "estimated_total_hours": 40,
    "weeks": [
        {{
            "week_number": 1,
            "title": "Foundation & Core Concepts",
            "skills_covered": ["Skill1"],
            "key_topics": ["Topic A", "Topic B"],
            "hands_on_project": "Build a simple project demonstrating...",
            "recommended_resources": ["Official Documentation", "FreeCodeCamp Guide"]
        }},
        {{
            "week_number": 2,
            "title": "Intermediate Application & Tooling",
            "skills_covered": ["Skill2"],
            "key_topics": ["Topic C", "Topic D"],
            "hands_on_project": "Implement...",
            "recommended_resources": ["Coursera / YouTube Course"]
        }},
        {{
            "week_number": 3,
            "title": "Advanced Integration & Architecture",
            "skills_covered": ["Skill3"],
            "key_topics": ["Topic E"],
            "hands_on_project": "Integrate...",
            "recommended_resources": ["GitHub Example Repositories"]
        }},
        {{
            "week_number": 4,
            "title": "Portfolio Project & ATS Alignment",
            "skills_covered": ["All"],
            "key_topics": ["Showcase", "Resume bullet points"],
            "hands_on_project": "Deploy end-to-end portfolio demo with CI/CD",
            "recommended_resources": ["Portfolio Best Practices"]
        }}
    ],
    "high_value_certifications": ["Certification A", "Certification B"]
}}

Return JSON ONLY.
"""
    try:
        response = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=[
                {"role": "system", "content": "You are a senior curriculum designer. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        return parse_json_safely(response.choices[0].message.content)
    except Exception as e:
        logger.warning(f"Roadmap LLM failed: {e}. Returning fallback.")
        return generate_mock_roadmap(missing_skills, target_role)


# ============================================================
# JOB RECOMMENDATIONS LLM
# ============================================================
def generate_job_recommendations_llm(resume_text: str, api_key: str = None) -> list:
    """
    Analyzes candidate's skills and suggests 5 matching job titles, salary bands, and market outlook.
    """
    client = get_groq_client(api_key)
    if not client:
        return generate_mock_job_recommendations()

    prompt = f"""
Based on the candidate resume text below, identify the top 5 job roles that represent the strongest match.
Return a valid JSON array of objects:
{{
    "recommendations": [
        {{
            "job_title": "Full Stack Python Engineer",
            "match_percentage": 88,
            "typical_salary_range": "$95,000 - $130,000",
            "required_core_skills": ["Python", "FastAPI", "React", "PostgreSQL"],
            "why_you_match": "Your experience building REST APIs with Python aligns closely with market demand.",
            "search_query": "Python Full Stack Developer remote"
        }}
    ]
}}

RESUME TEXT:
{resume_text[:2000]}

Return JSON ONLY.
"""
    try:
        response = client.chat.completions.create(
            model=FALLBACK_MODEL,
            messages=[
                {"role": "system", "content": "You are a talent placement expert. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )
        data = parse_json_safely(response.choices[0].message.content)
        return data.get("recommendations", generate_mock_job_recommendations())
    except Exception as e:
        logger.warning(f"Job recommendations LLM failed: {e}. Returning fallback.")
        return generate_mock_job_recommendations()


# ============================================================
# MOCK INTERVIEW CHATBOT LLM
# ============================================================
def interview_chatbot_turn(conversation_history: list, job_description: str, resume_summary: str, api_key: str = None) -> dict:
    """
    Generates the next interview question and scores the candidate's previous response using STAR criteria.
    """
    client = get_groq_client(api_key)
    if not client:
        return {
            "evaluation_score": 8,
            "feedback": "Great concise answer! You clearly outlined your reasoning. To make it even stronger, mention specific metrics or quantitative outcomes achieved.",
            "next_question": "Can you describe a challenging technical roadblock you encountered recently and how you debugged it step-by-step?"
        }

    prompt = f"""
You are an interviewer conducting a technical and behavioral job interview for this role:
Job Context: {job_description[:500]}
Candidate Background: {resume_summary[:300]}

Conversation History:
{json.dumps(conversation_history[-6:], indent=2)}

Task:
1. Evaluate the candidate's last answer (score 1-10, feedback using STAR method).
2. If this is the start of the interview, give an encouraging greeting and ask the first relevant question.
3. Formulate the next intelligent, conversational follow-up question.

Return JSON format:
{{
    "evaluation_score": 8,
    "feedback": "Detailed constructive evaluation of the candidate's previous answer...",
    "next_question": "Your next interview question here..."
}}
"""
    try:
        response = client.chat.completions.create(
            model=PRIMARY_MODEL,
            messages=[
                {"role": "system", "content": "You are an expert technical interviewer. Return JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )
        return parse_json_safely(response.choices[0].message.content)
    except Exception as e:
        logger.warning(f"Interview chat LLM failed: {e}. Returning fallback.")
        return {
            "evaluation_score": 7,
            "feedback": "Solid answer! Try to include more specifics about performance optimization and architectural trade-offs.",
            "next_question": "How do you approach database schema design and migrations when building distributed applications?"
        }


# ============================================================
# INTELLIGENT FALLBACK / DEMO GENERATORS
# ============================================================
def generate_mock_analysis(resume_text: str, job_description: str) -> dict:
    """Generates intelligent mock analysis based on keyword heuristics."""
    from modules.keyword_analyzer import analyze_ats_keywords
    kw_data = analyze_ats_keywords(resume_text, job_description)

    score = min(max(int(kw_data["match_percentage"] * 0.8 + 25), 45), 94)
    matched = [item["keyword"].title() for item in kw_data["matched_keywords"][:8]] or ["Python", "Git", "SQL", "Problem Solving"]
    missing = [item["keyword"].title() for item in kw_data["missing_keywords"][:6]] or ["Docker", "Kubernetes", "AWS", "CI/CD"]

    return {
        "ats_score": score,
        "candidate_summary": f"The candidate demonstrates solid foundational skills matching {len(matched)} key requirements. Core competencies align well with software engineering standards, with opportunities to deepen cloud-native and DevOps proficiencies.",
        "category_scores": {
            "technical_skills": min(score + 4, 98),
            "experience": max(score - 5, 50),
            "education": 88,
            "soft_skills": 82,
            "tools_technologies": max(score - 2, 55)
        },
        "matched_skills": matched,
        "missing_skills": missing,
        "partial_match_skills": ["FastAPI", "Agile / Scrum", "Unit Testing"],
        "strengths": [
            "Demonstrated practical exposure to modern programming languages and clean code principles.",
            "Solid experience with relational database concepts and RESTful API architecture.",
            "Strong academic and project foundations."
        ],
        "weaknesses": [
            f"Key production technologies such as {', '.join(missing[:3])} are not explicitly detailed in the resume.",
            "Project bullet points could feature more quantifiable business impact metrics."
        ],
        "experience_match": "The candidate has relevant engineering experience and projects that map to approximately 75% of the target requirements.",
        "education_match": "Educational background meets or exceeds the required technical degree criteria.",
        "project_match": "Portfolio projects show good problem solving, but would benefit from live deployment links and architectural diagrams.",
        "resume_improvements": [
            f"Incorporate missing core keywords: {', '.join(missing[:4])}.",
            "Use the Google XYZ formula for work achievements: 'Accomplished [X] as measured by [Y] by doing [Z]'.",
            "Add a clear 'Technical Skills' grid categorized by Languages, Frameworks, Databases, and DevOps.",
            "Include links to active GitHub repositories and live production demonstrations."
        ],
        "interview_questions": [
            "How have you designed and implemented scalable RESTful APIs in your previous projects?",
            "Can you explain database indexing and how you optimize slow queries?",
            "What is your experience with containerization tools like Docker?",
            "Walk us through how you handle code reviews and collaborative Git workflows.",
            "Describe a time you solved a difficult performance bottleneck in your code."
        ]
    }


def generate_mock_rewrite(original_text: str, target_role: str, section_type: str) -> dict:
    return {
        "metric_driven": f"Spearheaded architectural redesign of core services for {target_role}, cutting latency by 38% and supporting 150K+ daily transactions while ensuring 99.9% system availability.",
        "ats_keyword_dense": f"Architected high-throughput REST APIs and microservices utilizing Python, MySQL, and Docker, implementing CI/CD pipelines and automated unit tests across distributed cloud environments.",
        "executive_action": f"Championed cross-functional engineering initiatives to modernize legacy backend workflows; mentored 4 junior developers and drove code quality standards adhering to industry best practices.",
        "key_changes_made": [
            "Converted passive responsibilities into high-impact accomplishment statements.",
            "Injected quantifiable performance benchmarks (38% latency reduction, 150K+ transactions).",
            "Integrated high-frequency ATS keywords matching modern job specifications."
        ],
        "ats_keywords_injected": ["REST APIs", "Microservices", "Docker", "CI/CD", "High-Throughput"]
    }


def generate_mock_roadmap(missing_skills: list, target_role: str) -> dict:
    skills = missing_skills if missing_skills else ["Docker", "Kubernetes", "AWS", "FastAPI"]
    return {
        "target_role": target_role or "Software Engineer",
        "estimated_total_hours": 36,
        "weeks": [
            {
                "week_number": 1,
                "title": f"Core Foundations: {skills[0] if len(skills) > 0 else 'Cloud'}",
                "skills_covered": [skills[0]] if skills else ["Docker"],
                "key_topics": ["Container architecture", "Dockerfiles", "Multi-stage builds"],
                "hands_on_project": "Containerize a full-stack Python application with Docker Compose",
                "recommended_resources": ["Official Docker Docs", "FreeCodeCamp Container Course"]
            },
            {
                "week_number": 2,
                "title": f"DevOps & Deployment: {skills[1] if len(skills) > 1 else 'CI/CD'}",
                "skills_covered": [skills[1]] if len(skills) > 1 else ["CI/CD"],
                "key_topics": ["GitHub Actions", "Automated Testing", "Artifact Registry"],
                "hands_on_project": "Build an automated CI/CD pipeline that tests and builds images on git push",
                "recommended_resources": ["GitHub Actions Docs", "TechWorld with Nana"]
            },
            {
                "week_number": 3,
                "title": f"Cloud Services: {skills[2] if len(skills) > 2 else 'AWS'}",
                "skills_covered": [skills[2]] if len(skills) > 2 else ["AWS"],
                "key_topics": ["AWS ECS / App Runner", "RDS MySQL Setup", "IAM & S3"],
                "hands_on_project": "Deploy containerized backend to AWS with managed MySQL database",
                "recommended_resources": ["AWS Skill Builder", "Stephane Maarek Cloud Course"]
            },
            {
                "week_number": 4,
                "title": "Capstone Portfolio & ATS Resume Polish",
                "skills_covered": ["Full Integration"],
                "key_topics": ["Telemetry & Logging", "Live Documentation", "Resume Bullet Integration"],
                "hands_on_project": "Publish live URL, write comprehensive README, and add newly acquired skills to resume",
                "recommended_resources": ["System Design Primer", "Portfolio Best Practices"]
            }
        ],
        "high_value_certifications": ["AWS Certified Solutions Architect Associate", "Docker Certified Associate"]
    }


def generate_mock_job_recommendations() -> list:
    return [
        {
            "job_title": "Full Stack Python Developer",
            "match_percentage": 92,
            "typical_salary_range": "$90,000 - $130,000",
            "required_core_skills": ["Python", "FastAPI", "SQL", "React", "Git"],
            "why_you_match": "Your core competencies in Python, REST APIs, and database design are directly aligned with mid-to-senior full stack openings.",
            "search_query": "Python Full Stack Developer remote"
        },
        {
            "job_title": "Backend Software Engineer",
            "match_percentage": 88,
            "typical_salary_range": "$95,000 - $140,000",
            "required_core_skills": ["Python", "MySQL", "System Design", "Microservices"],
            "why_you_match": "High match on data modeling, API development, and distributed system concepts.",
            "search_query": "Backend Software Engineer Python"
        },
        {
            "job_title": "AI & GenAI Solutions Engineer",
            "match_percentage": 85,
            "typical_salary_range": "$105,000 - $150,000",
            "required_core_skills": ["LLMs", "Groq", "RAG", "Python", "Vector Databases"],
            "why_you_match": "Demonstrated hands-on expertise building GenAI applications and prompt engineering pipelines.",
            "search_query": "Generative AI Engineer remote"
        },
        {
            "job_title": "DevOps / Platform Associate",
            "match_percentage": 78,
            "typical_salary_range": "$85,000 - $120,000",
            "required_core_skills": ["Docker", "CI/CD", "Linux", "AWS"],
            "why_you_match": "Great bridge role for developers looking to scale infrastructure automation and deployment workflows.",
            "search_query": "Junior DevOps Engineer Cloud"
        },
        {
            "job_title": "Data Engineer / ETL Specialist",
            "match_percentage": 82,
            "typical_salary_range": "$90,000 - $135,000",
            "required_core_skills": ["SQL", "Python", "Data Pipelines", "PostgreSQL"],
            "why_you_match": "Strong query optimization, schema architecture, and Python data manipulation skills.",
            "search_query": "Data Engineer Python SQL"
        }
    ]
