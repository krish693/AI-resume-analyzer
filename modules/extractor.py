import re
import io
import logging
from pypdf import PdfReader
import docx

logger = logging.getLogger(__name__)


def clean_text(text: str) -> str:
    """
    Normalizes whitespace while preserving paragraph structure.
    Removes strange non-printable unicode control characters.
    """
    if not text:
        return ""
    # Normalize carriage returns
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Remove non-printable control characters except newline and tab
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]", "", text)
    # Collapse multiple consecutive empty lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse redundant horizontal spaces
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def extract_pdf_text(file_obj) -> str:
    """
    Extracts text from a PDF file using pypdf, falling back to PyMuPDF if needed.
    """
    text_parts = []
    try:
        # If passed as bytes or file-like object
        if isinstance(file_obj, bytes):
            file_stream = io.BytesIO(file_obj)
        else:
            file_stream = file_obj

        reader = PdfReader(file_stream)
        for page_idx, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    except Exception as e:
        logger.warning(f"pypdf extraction failed or partial ({e}). Attempting fitz fallback.")
        try:
            import fitz  # PyMuPDF
            if isinstance(file_obj, bytes):
                doc = fitz.open(stream=file_obj, filetype="pdf")
            else:
                doc = fitz.open(stream=file_obj.read(), filetype="pdf")
                file_obj.seek(0)
            text_parts = [page.get_text() for page in doc]
        except Exception as e2:
            raise ValueError(f"Failed to read PDF document: {e2}")

    extracted = "\n".join(text_parts)
    return clean_text(extracted)


def extract_docx_text(file_obj) -> str:
    """
    Extracts text from a DOCX file, including paragraphs and tables.
    """
    try:
        if isinstance(file_obj, bytes):
            file_stream = io.BytesIO(file_obj)
        else:
            file_stream = file_obj

        doc = docx.Document(file_stream)
        text_parts = []

        # Extract main body paragraphs
        for para in doc.paragraphs:
            if para.text.strip():
                text_parts.append(para.text.strip())

        # Extract text from tables
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    # Deduplicate adjacent cells if merged
                    unique_cells = []
                    for c in row_cells:
                        if not unique_cells or c != unique_cells[-1]:
                            unique_cells.append(c)
                    text_parts.append(" | ".join(unique_cells))

        extracted = "\n".join(text_parts)
        return clean_text(extracted)
    except Exception as e:
        raise ValueError(f"Failed to read DOCX document: {e}")


def extract_document_text(file_obj, filename: str) -> str:
    """
    Auto-detects document format from filename (.pdf or .docx) and extracts text.
    """
    fn_lower = filename.lower()
    if fn_lower.endswith(".pdf"):
        return extract_pdf_text(file_obj)
    elif fn_lower.endswith(".docx") or fn_lower.endswith(".doc"):
        return extract_docx_text(file_obj)
    else:
        # Try as plain text
        try:
            if isinstance(file_obj, bytes):
                return file_obj.decode("utf-8", errors="ignore")
            content = file_obj.read()
            if isinstance(content, bytes):
                return content.decode("utf-8", errors="ignore")
            return str(content)
        except Exception as e:
            raise ValueError(f"Unsupported file format '{filename}'. Please upload a PDF or DOCX file.")


# ============================================================
# CONTACT & ATS METADATA EXTRACTION
# ============================================================
def extract_contact_info(text: str) -> dict:
    """
    Extracts email, phone, links, and candidate name heuristics.
    """
    info = {
        "email": None,
        "phone": None,
        "linkedin": None,
        "github": None,
        "detected_name": None
    }

    # Email
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    if email_match:
        info["email"] = email_match.group(0)

    # Phone
    phone_match = re.search(r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text)
    if phone_match:
        info["phone"] = phone_match.group(0)

    # LinkedIn
    linkedin_match = re.search(r"(?:https?://)?(?:www\.)?linkedin\.com/in/[a-zA-Z0-9-_]+", text, re.IGNORECASE)
    if linkedin_match:
        info["linkedin"] = linkedin_match.group(0)

    # GitHub
    github_match = re.search(r"(?:https?://)?(?:www\.)?github\.com/[a-zA-Z0-9-_]+", text, re.IGNORECASE)
    if github_match:
        info["github"] = github_match.group(0)

    # Estimate candidate name (usually top 1-2 lines before email or headers)
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    if lines:
        for line in lines[:5]:
            # Look for line with 2 to 4 capitalized words and no special symbols
            if 2 <= len(line.split()) <= 4 and not re.search(r"[@|#|/|\\|:|;]", line) and len(line) < 40:
                info["detected_name"] = line
                break
    if not info["detected_name"] and lines:
        info["detected_name"] = lines[0][:40]

    return info


def inspect_ats_formatting(text: str, filename: str) -> dict:
    """
    Evaluates ATS parseability and standard resume formatting structure.
    """
    word_count = len(text.split())
    char_count = len(text)

    # Common standard section headers
    sections = {
        "Summary / Objective": bool(re.search(r"\b(summary|objective|profile|about me)\b", text, re.I)),
        "Work Experience": bool(re.search(r"\b(experience|employment|work history|professional background)\b", text, re.I)),
        "Education": bool(re.search(r"\b(education|academic|qualification|degree|university|college)\b", text, re.I)),
        "Skills": bool(re.search(r"\b(skills|technical skills|technologies|proficiencies|core competencies)\b", text, re.I)),
        "Projects": bool(re.search(r"\b(projects|personal projects|portfolio|key projects)\b", text, re.I)),
        "Certifications": bool(re.search(r"\b(certifications|certificates|licenses|courses)\b", text, re.I)),
    }

    found_sections = [sec for sec, found in sections.items() if found]
    missing_sections = [sec for sec, found in sections.items() if not found]

    # Calculate format health score
    contact = extract_contact_info(text)
    format_score = 50  # base
    if contact["email"]:
        format_score += 15
    if contact["phone"]:
        format_score += 10
    if len(found_sections) >= 4:
        format_score += 15
    if 250 <= word_count <= 1200:
        format_score += 10

    format_score = min(format_score, 100)

    warnings = []
    if word_count < 150:
        warnings.append("Document length is very short (< 150 words). ATS may consider it incomplete.")
    elif word_count > 1500:
        warnings.append("Resume exceeds 1500 words. Consider condensing to 1-2 pages for better ATS parsing.")
    if not contact["email"]:
        warnings.append("No email address detected. Ensure contact details are in standard text (not an image or nested header).")
    if not contact["phone"]:
        warnings.append("No telephone number detected.")
    if not sections["Work Experience"]:
        warnings.append("Standard 'Work Experience' or 'Experience' section heading not clearly identified.")
    if not sections["Skills"]:
        warnings.append("Standard 'Skills' section heading not clearly identified.")

    return {
        "filename": filename,
        "format_score": format_score,
        "word_count": word_count,
        "char_count": char_count,
        "contact_info": contact,
        "found_sections": found_sections,
        "missing_sections": missing_sections,
        "warnings": warnings,
        "is_ats_friendly": format_score >= 70
    }
