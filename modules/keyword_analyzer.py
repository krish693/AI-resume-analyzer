import re
from collections import Counter
import math

COMMON_STOPWORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and",
    "any", "are", "aren't", "as", "at", "be", "because", "been", "before", "being",
    "below", "between", "both", "but", "by", "can't", "cannot", "could", "couldn't",
    "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't",
    "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here",
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i",
    "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's",
    "its", "itself", "let's", "me", "more", "most", "mustn't", "my", "myself",
    "no", "nor", "not", "of", "off", "on", "once", "only", "or", "other", "ought",
    "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such",
    "than", "that", "that's", "the", "their", "theirs", "them", "themselves",
    "then", "there", "there's", "these", "they", "they'd", "they'll", "they're",
    "they've", "this", "those", "through", "to", "too", "under", "until", "up",
    "very", "was", "wasn't", "we", "we'd", "we'll", "we're", "we've", "were",
    "weren't", "what", "what's", "when", "when's", "where", "where's", "which",
    "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours",
    "yourself", "yourselves", "will", "shall", "may", "might", "must", "can",
    "looking", "role", "team", "work", "experience", "candidate", "years",
    "responsibilities", "requirements", "including", "knowledge", "strong",
    "good", "ability", "skills", "understanding", "well", "plus", "must", "have"
}

KNOWN_TECH_TERMS = [
    # Languages & Runtimes
    "python", "java", "javascript", "typescript", "c++", "c#", "go", "golang", "rust", "php", "ruby", "swift", "kotlin", "scala",
    # Frameworks & Libraries
    "react", "react.js", "angular", "vue", "vue.js", "next.js", "node.js", "express", "django", "flask", "fastapi", "spring", "spring boot",
    "asp.net", ".net", "laravel", "rails", "streamlit", "gradio",
    # AI / ML / Data
    "machine learning", "deep learning", "nlp", "llm", "generative ai", "rag", "langchain", "llamaindex", "groq", "openai", "huggingface",
    "pytorch", "tensorflow", "keras", "scikit-learn", "pandas", "numpy", "opencv", "computer vision", "transformers", "fine-tuning",
    # Databases & Storage
    "sql", "mysql", "postgresql", "postgres", "mongodb", "redis", "elasticsearch", "cassandra", "sqlite", "oracle", "dynamodb",
    # Cloud & DevOps
    "aws", "azure", "gcp", "google cloud", "docker", "kubernetes", "k8s", "terraform", "ci/cd", "jenkins", "github actions", "gitlab",
    "linux", "bash", "ansible", "nginx", "helm",
    # Software Engineering Core
    "git", "github", "gitlab", "rest", "rest api", "restful", "graphql", "microservices", "oop", "object oriented programming",
    "data structures", "algorithms", "dsa", "system design", "agile", "scrum", "kanban", "tdd", "unit testing", "design patterns"
]


def extract_keywords_from_text(text: str) -> list[str]:
    """
    Extracts significant words and technical phrases.
    """
    text_lower = text.lower()
    found_keywords = set()

    # Check multi-word and known tech terms first
    for term in KNOWN_TECH_TERMS:
        pattern = r"\b" + re.escape(term) + r"\b"
        if re.search(pattern, text_lower):
            found_keywords.add(term)

    # Word-level extraction
    words = re.findall(r"\b[a-zA-Z0-9#+.]+\b", text_lower)
    for word in words:
        if len(word) > 2 and word not in COMMON_STOPWORDS and not word.isdigit():
            # Filter clean alphabetic/technical tokens
            if re.match(r"^[a-z0-9#+.]+$", word):
                found_keywords.add(word)

    return sorted(list(found_keywords))


def analyze_ats_keywords(resume_text: str, job_description: str) -> dict:
    """
    Compares resume keywords against job description keywords.
    Provides match %, frequency analysis, keyword density, and priority breakdown.
    """
    resume_lower = resume_text.lower()
    jd_lower = job_description.lower()

    resume_words = re.findall(r"\b\w+\b", resume_lower)
    total_resume_words = max(len(resume_words), 1)

    jd_keywords = extract_keywords_from_text(job_description)

    matched_keywords = []
    missing_keywords = []
    keyword_freq_resume = {}
    keyword_freq_jd = {}

    for kw in jd_keywords:
        # Count in JD
        jd_count = len(re.findall(r"\b" + re.escape(kw) + r"\b", jd_lower))
        keyword_freq_jd[kw] = jd_count

        # Count in Resume
        res_count = len(re.findall(r"\b" + re.escape(kw) + r"\b", resume_lower))
        keyword_freq_resume[kw] = res_count

        if res_count > 0:
            matched_keywords.append({
                "keyword": kw,
                "resume_count": res_count,
                "jd_count": jd_count,
                "density": round((res_count / total_resume_words) * 100, 2)
            })
        else:
            missing_keywords.append({
                "keyword": kw,
                "jd_count": jd_count,
                "priority": "High" if jd_count >= 2 or kw in KNOWN_TECH_TERMS else "Medium"
            })

    total_jd_kw = len(jd_keywords)
    match_count = len(matched_keywords)
    match_percentage = round((match_count / total_jd_kw * 100), 1) if total_jd_kw > 0 else 0

    # Categorize missing
    high_priority_missing = [item["keyword"] for item in missing_keywords if item["priority"] == "High"]
    medium_priority_missing = [item["keyword"] for item in missing_keywords if item["priority"] == "Medium"]

    # Top keyword density warnings
    overused_keywords = [
        item["keyword"] for item in matched_keywords if item["density"] > 3.0
    ]

    return {
        "match_percentage": match_percentage,
        "total_jd_keywords": total_jd_kw,
        "matched_count": match_count,
        "missing_count": len(missing_keywords),
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "high_priority_missing": high_priority_missing,
        "medium_priority_missing": medium_priority_missing,
        "overused_keywords": overused_keywords,
        "total_resume_words": total_resume_words
    }
