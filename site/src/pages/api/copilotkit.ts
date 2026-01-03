import { CopilotRuntime, OpenAIAdapter } from "@copilotkit/runtime";
import type { APIRoute } from "astro";
import OpenAI from "openai";

export const POST: APIRoute = async ({ request }) => {
  const apiKey = process.env.OPENAI_API_KEY || import.meta.env.OPENAI_API_KEY;
  
  if (!apiKey) {
    return new Response(JSON.stringify({ error: "Missing API Key" }), { status: 500 });
  }

  const openai = new OpenAI({ apiKey });
  const runtime = new CopilotRuntime();
  const adapter = new OpenAIAdapter({ openai: openai as any });

  try {
    const response = await runtime.response(request, adapter);
    return new Response(response.body, {
      status: response.status,
      headers: response.headers,
    });
  } catch (error) {
    console.error("CopilotKit Runtime Error:", error);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), {
      status: 500,
    });
  }
};