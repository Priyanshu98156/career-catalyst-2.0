from typing import Any, Dict, List, Optional
from langchain_core.prompts import ChatPromptTemplate

from backend.ai_client import get_chat_model
from backend.models import Profile
from backend.schemas.job import JDAnalysis
from backend.schemas.resume import TailoredResumeResponse

RESUME_SYNTHESIS_PROMPT = """You are an elite executive technical resume strategist and ATS optimization expert.
Your mission is to synthesize a tailored, high-impact resume that targets the Job Description using the candidate's REAL experiences and knowledge vault bullets.

CRITICAL RULES (ANTI-HALLUCINATION & ATS EXCELLENCE):
1. ZERO HALLUCINATION: Do NOT invent fake companies, job titles, education, or unearned technologies.
2. STAR METHODOLOGY: Rewrite retrieved master bullets and experiences using the STAR method (Situation, Task, Action, Result).
   - Start each bullet point with a powerful action verb (e.g., "Architected", "Engineered", "Optimized", "Spearheaded").
   - Quantify results with metrics wherever plausible based on the candidate's real data (e.g., latency, throughput, cost, team size).
3. KEYWORD ALIGNMENT: Seamlessly weave target JD keywords into the professional summary, skills section, and bullet points.
4. ATS MATCH SCORING:
   - Calculate an objective ATS match score (0 - 100) based on how well the candidate's real skills match the JD.
   - List the matched keywords and missing keywords explicitly.
5. LATEX SOURCE: Generate clean, professional, compilable LaTeX code for the resume (using modern simple article style with standard geometry and hyperref packages).

TARGET JOB DESCRIPTION:
-----------------------
Title: {job_title}
Requirements: {jd_text}
Target Keywords: {target_keywords}
-----------------------

CANDIDATE'S RETRIEVED REAL BULLETS (FROM KNOWLEDGE VAULT):
-----------------------
{retrieved_bullets}
-----------------------

CANDIDATE BASE PROFILE:
-----------------------
Name: {candidate_name}
Email: {candidate_email}
Phone: {candidate_phone}
Location: {candidate_location}
LinkedIn: {candidate_linkedin}
GitHub: {candidate_github}
Portfolio: {candidate_portfolio}
Base Skills: {candidate_skills}
Education: {candidate_education}
Base Summary: {candidate_summary}
-----------------------
"""


def synthesize_tailored_resume(
    job_description: str,
    jd_analysis: JDAnalysis,
    retrieved_bullets: List[str],
    user_profile: Optional[Profile] = None,
) -> TailoredResumeResponse:
    """
    Synthesize an ATS-tailored resume using retrieved candidate bullets and base profile
    through a LangChain structured LLM chain.
    """
    # Prepare profile attributes with graceful defaults
    profile_dict: Dict[str, Any] = {
        "candidate_name": user_profile.full_name if user_profile else "Candidate Name",
        "candidate_email": user_profile.email if user_profile else "candidate@example.com",
        "candidate_phone": user_profile.phone if (user_profile and user_profile.phone) else "N/A",
        "candidate_location": user_profile.location if (user_profile and user_profile.location) else "N/A",
        "candidate_linkedin": user_profile.linkedin_url if (user_profile and user_profile.linkedin_url) else "N/A",
        "candidate_github": user_profile.github_url if (user_profile and user_profile.github_url) else "N/A",
        "candidate_portfolio": user_profile.portfolio_url if (user_profile and user_profile.portfolio_url) else "N/A",
        "candidate_skills": ", ".join(user_profile.skills) if (user_profile and user_profile.skills) else "Software Engineering",
        "candidate_education": str(user_profile.education) if (user_profile and user_profile.education) else "Degree in Computer Science or related field",
        "candidate_summary": user_profile.summary if (user_profile and user_profile.summary) else "Experienced software professional.",
    }

    bullets_text = (
        "\n".join([f"- {bullet}" for bullet in retrieved_bullets])
        if retrieved_bullets
        else "No specific prior bullets found. Use base profile to synthesize experiences."
    )

    llm = get_chat_model(temperature=0.1)
    structured_llm = llm.with_structured_output(TailoredResumeResponse)

    prompt = ChatPromptTemplate.from_template(RESUME_SYNTHESIS_PROMPT)
    chain = prompt | structured_llm

    result: TailoredResumeResponse = chain.invoke({
        "job_title": jd_analysis.job_title,
        "jd_text": job_description,
        "target_keywords": ", ".join(jd_analysis.keywords_to_target + jd_analysis.primary_skills),
        "retrieved_bullets": bullets_text,
        **profile_dict,
    })

    if not result.job_title:
        result.job_title = jd_analysis.job_title

    return result
