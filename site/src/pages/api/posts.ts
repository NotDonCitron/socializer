import type { APIRoute } from "astro";

const BACKEND_URL = 'http://127.0.0.1:8000';

export const GET: APIRoute = async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/posts/`);
    const data = await response.json();
    return new Response(JSON.stringify(data), { status: 200 });
  } catch (error) {
    return new Response(JSON.stringify({ error: "Failed to fetch posts" }), { status: 500 });
  }
};

export const stats: APIRoute = async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/posts/stats/impact`);
    const data = await response.json();
    return new Response(JSON.stringify(data), { status: 200 });
  } catch (error) {
    return new Response(JSON.stringify({ error: "Failed to fetch stats" }), { status: 500 });
  }
};

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    
    // For the prototype, we use user_id = 1 (the 'admin' we created)
    const postData = {
      user_id: 1,
      title: body.title || "Published Update",
      content: body.content,
      source_repo: body.source_repo || "manual",
      impact_score: body.impact_score || 5
    };

    const response = await fetch(`${BACKEND_URL}/posts/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(postData)
    });

    if (!response.ok) {
      const errorData = await response.json();
      return new Response(JSON.stringify(errorData), { status: response.status });
    }

    const data = await response.json();
    return new Response(JSON.stringify(data), { status: 201 });
  } catch (error) {
    console.error("Error publishing post:", error);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), { status: 500 });
  }
};
