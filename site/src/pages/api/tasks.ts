import type { APIRoute } from "astro";
import { createTask, updateTask } from "../../lib/vibe";

export const POST: APIRoute = async ({ request }) => {
  try {
    const body = await request.json();
    
    // Support for both Create and Update in one endpoint to simplify static routing
    if (body.taskId) {
        const success = await updateTask(body.taskId, body);
        if (success) {
            return new Response(JSON.stringify({ message: "Task updated" }), { status: 200 });
        } else {
            return new Response(JSON.stringify({ error: "Failed to update task" }), { status: 500 });
        }
    }

    const { title, description } = body;
    if (!title) {
      return new Response(JSON.stringify({ error: "Title is required" }), { status: 400 });
    }

    const taskId = await createTask(title, description || "");
    
    if (taskId) {
      return new Response(JSON.stringify({ task_id: taskId }), { status: 201 });
    } else {
      return new Response(JSON.stringify({ error: "Failed to create task in Vibe Kanban" }), { status: 500 });
    }
  } catch (error) {
    console.error("Error in API route:", error);
    return new Response(JSON.stringify({ error: "Internal Server Error" }), { status: 500 });
  }
};
