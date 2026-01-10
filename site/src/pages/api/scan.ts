import type { APIRoute } from "astro";
import { processProjectUpdate } from "../../lib/automation";
import sources from "../../config/sources.json";

export const POST: APIRoute = async () => {
  const repos = sources.github_repos;

  console.log(`Starting manual scan for ${repos.length} sources...`);
  
  for (const { owner, repo } of repos) {
    try {
        await processProjectUpdate(owner, repo);
    } catch (e) {
        console.error(`Error scanning ${owner}/${repo}:`, e);
    }
  }

  return new Response(JSON.stringify({ 
    message: 'Scan complete', 
    count: repos.length 
  }), {
    status: 200,
    headers: { 'Content-Type': 'application/json' }
  });
}