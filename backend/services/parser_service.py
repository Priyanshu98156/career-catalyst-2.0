import io
from pathlib import Path
from typing import Union
from pypdf import PdfReader
from langchain_core.prompts import ChatPromptTemplate
from backend.ai_client import get_chat_model
from backend.schemas.profile import ParsedProfile

RESUME_EXTRACTION_PROMPT = """You are an expert ATS resume parser and data extraction system.
Extract all relevant candidate details from the provided raw resume text into the exact structured schema.

CRITICAL RULES:
1. STRICT TRUTHFULNESS: Do not hallucinate or invent dates, companies, metrics, or technologies not present in the text.
2. If a specific field (e.g. phone, linkedin, portfolio, location) is not found, leave it as null/empty.
3. Split candidate work history into individual experiences, each with its role, company, duration, and list of bullet points.
4. Extract skills as a clean list of individual technical and professional proficiencies mentioned in the resume.
5. Extract all education and certification entries accurately.

RAW RESUME TEXT:
----------------
{resume_text}
----------------
"""


def extract_text_from_pdf(source: Union[bytes, io.BytesIO, str, Path]) -> str:
    """
    Extract raw text from a PDF provided as raw bytes, a BytesIO stream, or a file path.
    Does not require saving files to disk (in-memory, clean, zero temporary file leaks).
    """
    if isinstance(source, (str, Path)):
        reader = PdfReader(str(source))
    elif isinstance(source, bytes):
        reader = PdfReader(io.BytesIO(source))
    elif isinstance(source, io.BytesIO):
        reader = PdfReader(source)
    else:
        raise ValueError(f"Unsupported source type for PDF extraction: {type(source)}")

    pages_text = []
    for page_idx, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            pages_text.append(text.strip())

    extracted = "\n\n".join(pages_text).strip()
    if not extracted:
        raise ValueError("Could not extract any text from the provided PDF document.")
    return extracted


def parse_resume_text(resume_text: str) -> ParsedProfile:
    """
    Parse raw resume text into a strictly typed ParsedProfile using Gemini structured output.
    """
    llm = get_chat_model(temperature=0.0)
    structured_llm = llm.with_structured_output(ParsedProfile)

    prompt = ChatPromptTemplate.from_template(RESUME_EXTRACTION_PROMPT)
    chain = prompt | structured_llm

    result = chain.invoke({"resume_text": resume_text})
    return result


def parse_resume_document(source: Union[bytes, io.BytesIO, str, Path]) -> ParsedProfile:
    """
    High-level helper: extracts text from a PDF source and parses it into ParsedProfile.
    """
    raw_text = extract_text_from_pdf(source)
    return parse_resume_text(raw_text)
