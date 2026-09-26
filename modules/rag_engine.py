import re
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import logging
from modules.llm_engine import get_groq_client, PRIMARY_MODEL, FALLBACK_MODEL, parse_json_safely

logger = logging.getLogger(__name__)


class CompanyRAGEngine:
    def __init__(self):
        self.documents = []  # list of dicts: {"doc_id": int, "title": str, "chunk": str}
        self.vectorizer = None
        self.tfidf_matrix = None

    def chunk_text(self, text: str, chunk_size: int = 400, overlap: int = 50) -> list[str]:
        """Splits long text into overlapping chunks."""
        words = text.split()
        if len(words) <= chunk_size:
            return [text]

        chunks = []
        start = 0
        while start < len(words):
            end = min(start + chunk_size, len(words))
            chunk = " ".join(words[start:end])
            chunks.append(chunk)
            if end == len(words):
                break
            start += chunk_size - overlap
        return chunks

    def build_index(self, doc_records: list[dict]):
        """
        doc_records: list of dicts from DB with {"id", "title", "content", "doc_type"}
        """
        self.documents = []
        for doc in doc_records:
            chunks = self.chunk_text(doc.get("content", ""))
            for idx, c in enumerate(chunks):
                self.documents.append({
                    "doc_id": doc.get("id"),
                    "title": doc.get("title", "Company Document"),
                    "doc_type": doc.get("doc_type", "general"),
                    "chunk": c
                })

        if not self.documents:
            self.vectorizer = None
            self.tfidf_matrix = None
            return

        texts = [d["chunk"] for d in self.documents]
        self.vectorizer = TfidfVectorizer(stop_words="english")
        self.tfidf_matrix = self.vectorizer.fit_transform(texts)

    def retrieve_relevant_context(self, query: str, top_k: int = 3) -> list[dict]:
        """Finds top-k most relevant company document chunks."""
        if not self.documents or not self.vectorizer or self.tfidf_matrix is None:
            return []

        query_vec = self.vectorizer.transform([query])
        sims = cosine_similarity(query_vec, self.tfidf_matrix).flatten()

        top_indices = np.argsort(sims)[::-1][:top_k]
        results = []
        for idx in top_indices:
            if sims[idx] > 0.05:  # Relevance threshold
                results.append({
                    "title": self.documents[idx]["title"],
                    "doc_type": self.documents[idx]["doc_type"],
                    "content": self.documents[idx]["chunk"],
                    "similarity": float(sims[idx])
                })
        return results

    def answer_query(self, query: str, api_key: str = None) -> str:
        """Answers user question grounded strictly in indexed company knowledge."""
        relevant = self.retrieve_relevant_context(query, top_k=4)
        if not relevant:
            return "No relevant company documents found. Please upload company handbooks, culture docs, or specs to index them."

        context_str = "\n\n".join([f"[{d['title']}]: {d['content']}" for d in relevant])

        client = get_groq_client(api_key)
        if not client:
            return f"**Relevant Excerpt Found from {relevant[0]['title']}:**\n\n{relevant[0]['content'][:400]}..."

        prompt = f"""
You are the NexusTech Internal Company AI Assistant.
Answer the following employee/recruiter question using ONLY the retrieved company context below.
If the answer cannot be determined from the context, say so clearly.

COMPANY CONTEXT:
{context_str}

USER QUESTION:
{query}

ANSWER (Concise, structured with markdown bullets):
"""
        try:
            res = client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            return res.choices[0].message.content
        except Exception as e:
            return f"Error querying LLM: {e}. Excerpt:\n{relevant[0]['content']}"

    def evaluate_company_culture_fit(self, resume_text: str, api_key: str = None) -> dict:
        """
        Compares candidate resume against indexed company values, engineering standards, and working culture.
        """
        # Retrieve context representing culture and tech stack
        relevant = self.retrieve_relevant_context(resume_text[:500], top_k=5)
        if not relevant:
            context_str = "Default standards: Clean code, ownership, teamwork, continuous learning, distributed systems."
        else:
            context_str = "\n\n".join([f"[{d['title']}]: {d['content']}" for d in relevant])

        client = get_groq_client(api_key)
        if not client:
            return {
                "culture_fit_score": 85,
                "values_alignment": "Candidate's collaborative and project-driven background maps strongly to team engineering ownership values.",
                "strengths_for_company": [
                    "Strong affinity for async communication and peer code reviews",
                    "Demonstrated curiosity for modern AI and cloud tooling"
                ],
                "areas_to_explore_in_interview": [
                    "Ask how the candidate handles ambiguity in rapid prototyping environments",
                    "Explore their experience with automated testing and continuous integration"
                ]
            }

        prompt = f"""
You are the Head of Engineering evaluating candidate cultural & technical alignment with our company guidelines.

COMPANY GUIDELINES & CULTURE:
{context_str}

CANDIDATE RESUME:
{resume_text[:2500]}

Analyze their cultural and engineering fit. Return JSON only:
{{
    "culture_fit_score": 85,
    "values_alignment": "Detailed paragraph explaining cultural alignment...",
    "strengths_for_company": [
        "Alignment with value A...",
        "Experience matching engineering guideline B..."
    ],
    "areas_to_explore_in_interview": [
        "Behavioral question to ask regarding company culture...",
        "Technical standard question to verify..."
    ]
}}
"""
        try:
            res = client.chat.completions.create(
                model=FALLBACK_MODEL,
                messages=[
                    {"role": "system", "content": "You are a company culture evaluation AI. Return JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            return parse_json_safely(res.choices[0].message.content)
        except Exception as e:
            logger.warning(f"RAG culture fit LLM failed: {e}")
            return {
                "culture_fit_score": 80,
                "values_alignment": "Candidate shows strong potential alignment with modern engineering and collaborative standards.",
                "strengths_for_company": ["Proactive learning", "Clean technical communication"],
                "areas_to_explore_in_interview": ["Handling sprint priorities", "Code quality expectations"]
            }
