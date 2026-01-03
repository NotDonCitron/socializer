import { CopilotKit, useCopilotAction, useCopilotReadable } from "@copilotkit/react-core";
import { CopilotPopup } from "@copilotkit/react-ui";
import "@copilotkit/react-ui/styles.css";

interface Task {
  id: string;
  title: string;
  description?: string;
  status: string;
}

function CopilotActions({ tasks }: { tasks: Task[] }) {
  // Make tasks readable to Copilot
  useCopilotReadable({
    description: "The current tasks on the Kanban board",
    value: tasks,
  });

  useCopilotAction({
    name: "createTask",
    description: "Create a new task in the Kanban board",
    parameters: [
      {
        name: "title",
        type: "string",
        description: "The title of the task",
        required: true,
      },
      {
        name: "description",
        type: "string",
        description: "The description of the task",
      },
    ],
    handler: async ({ title, description }) => {
      console.log("Copilot attempting to create task:", title);
      
      try {
        const response = await fetch("/api/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ title, description }),
        });

        if (response.ok) {
          const data = await response.json();
          return `Successfully created task: ${title} (ID: ${data.task_id})`;
        } else {
          return "Failed to create task via API.";
        }
      } catch (e) {
        return "Error calling task API.";
      }
    },
  });

  useCopilotAction({
    name: "updateTaskDescription",
    description: "Update the description of an existing task. Use this to refine AI drafts.",
    parameters: [
      {
        name: "taskId",
        type: "string",
        description: "The ID of the task to update",
        required: true,
      },
      {
        name: "newDescription",
        type: "string",
        description: "The new description/content for the task",
        required: true,
      },
    ],
    handler: async ({ taskId, newDescription }) => {
      console.log("Copilot attempting to update task:", taskId);
      
      try {
        const response = await fetch("/api/tasks", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ taskId, description: newDescription }),
        });

        if (response.ok) {
          return `Successfully updated task ${taskId}.`;
        } else {
          return "Failed to update task via API.";
        }
      } catch (e) {
        return "Error calling task API.";
      }
    },
  });

  useCopilotAction({
    name: "publishPost",
    description: "Publish a refined content draft to the live social feed.",
    parameters: [
      {
        name: "content",
        type: "string",
        description: "The final refined content to publish",
        required: true,
      },
      {
        name: "title",
        type: "string",
        description: "The title for the post",
      },
      {
        name: "sourceRepo",
        type: "string",
        description: "The repository this update is about (e.g. langchain-ai/langchain)",
      },
    ],
    handler: async ({ content, title, sourceRepo }) => {
      console.log("Copilot attempting to publish post");
      
      try {
        const response = await fetch("http://localhost:8000/posts/", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ 
            user_id: 1, // Default admin user
            content, 
            title: title || "New Update", 
            source_repo: sourceRepo,
            impact_score: 5 // Default impact
          }),
        });

        if (response.ok) {
          return "Successfully published post to the live feed!";
        } else {
          return "Failed to publish post via API.";
        }
      } catch (e) {
        return "Error calling posts API.";
      }
    },
  });

  return null;
}

export default function CopilotWrapper({ children, tasks = [] }: { children: React.ReactNode, tasks?: Task[] }) {
  return (
    <CopilotKit runtimeUrl="http://localhost:8000/ai/copilotkit">
      <CopilotActions tasks={tasks} />
      {children}
      <CopilotPopup
        instruction={"You are an assistant for the Socializer project. You can help manage tasks and refine AI-generated content drafts found in task descriptions."}
        labels={{
          title: "Socializer Copilot",
          initial: "Hi! I can help you create, list, and refine tasks and AI drafts.",
        }}
      />
    </CopilotKit>
  );
}

