import type { APIRoute } from "astro";

const BACKEND_URL = 'http://127.0.0.1:8000';

export const GET: APIRoute = async () => {
  try {
    const response = await fetch(`${BACKEND_URL}/posts/stats/impact`);
    if (!response.ok) throw new Error("Backend error");
    const data = await response.json();
    return new Response(JSON.stringify(data), { status: 200 });
  } catch (error) {
    console.error("Error fetching stats:", error);
    return new Response(JSON.stringify({ error: "Failed to fetch stats" }), { status: 500 });
  }
};
