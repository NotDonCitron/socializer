from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from openai import OpenAI
import os
from dotenv import load_dotenv
from copilotkit import CopilotKitRemoteEndpoint
from copilotkit.integrations.fastapi import add_copilotkit_endpoint

load_dotenv()

router = APIRouter(prefix="/ai", tags=["ai"])

# ... existing Summary logic ...

sdk = CopilotKitRemoteEndpoint()

add_copilotkit_endpoint(router, sdk, "/copilotkit")

class SummaryRequest(BaseModel):
    project_name: str
    release_notes: str

class SummaryResponse(BaseModel):
    summary: str

def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENAI_API_KEY not set in backend environment")
    return OpenAI(api_key=api_key)

@router.post("/scan")
async def trigger_scan():
    # In a real app, this would trigger the github logic.
    # For now, we return a success message to indicate the backend is ready.
    return {"message": "Scan initiated"}

@router.post("/summarize", response_model=SummaryResponse)
async def summarize_release(request: SummaryRequest):
    try:
        client = get_openai_client()
        
        prompt = f"""
        Project: {request.project_name}
        
        Release Notes:
        {request.release_notes[:4000]}
        
        Please provide:
        1. A concise TL;DR (3 bullet points max).
        2. A viral X Thread Hook (first tweet).
        3. A professional LinkedIn post draft.
        Focus on why this update matters to AI developers and businesses.
        """
        
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": "You are a world-class social media manager for tech and AI news."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
        )
        
        summary_text = response.choices[0].message.content
        return SummaryResponse(summary=summary_text)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
