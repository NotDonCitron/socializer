const BACKEND_URL = 'http://127.0.0.1:8000';

export async function generateSocialContent(projectName: string, releaseNotes: string) {
  try {
    const response = await fetch(`${BACKEND_URL}/ai/summarize`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        project_name: projectName,
        release_notes: releaseNotes
      })
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || `Backend error: ${response.statusText}`);
    }

    const data = await response.json();
    return data.summary;
  } catch (error) {
    console.error("AI Generation failed:", error);
    return "AI generation failed. Please review raw notes.";
  }
}