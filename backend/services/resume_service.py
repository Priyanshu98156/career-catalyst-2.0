from google import genai
from backend.config import GEMINI_CHAT_MODEL
from backend.schemas import TailorRequest, TailoredResumeResponse

# Initialize client with environment configuration
client = genai.Client()


def generate_tailored_resume(request: TailorRequest) -> TailoredResumeResponse:
    prompt = f"""
    You are an expert technical recruiter. 
    Analyze this Job Description: {request.job_description}
    Filter and rewrite the following master bullets to perfectly match the JD keywords.
    Master Bullets: {request.master_bullets}
    Generate the raw LaTeX string for the final output.
    """
    
    response = client.models.generate_content(
        model=GEMINI_CHAT_MODEL,
        contents=prompt,
        config={
            'response_mime_type': 'application/json',
            'response_schema': TailoredResumeResponse,
        },
    )
    
    return response.parsed