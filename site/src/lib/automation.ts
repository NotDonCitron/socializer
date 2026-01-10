import { getLatestRelease } from './github';
import { createTask } from './vibe';
import { generateSocialContent } from './ai';

export async function processProjectUpdate(owner: string, repo: string) {
    console.log(`Checking for updates: ${owner}/${repo}...`);
    const release = await getLatestRelease(owner, repo);

    if (!release) {
        console.log(`No releases found for ${owner}/${repo}.`);
        return;
    }

    console.log(`Generating AI content for ${repo} ${release.tag_name}...`);
    const aiContent = await generateSocialContent(repo, release.body);

    const taskTitle = `📣 POST DRAFT: ${repo} ${release.tag_name}`;
    const taskDescription = `
# 🚀 New Release detected: ${repo} ${release.tag_name}
Link: ${release.html_url}

---
## 🤖 AI GENERATED CONTENT DRAFTS
${aiContent}

---
## 📄 RAW RELEASE NOTES (Excerpt)
${release.body.substring(0, 500)}...
    `.trim();

    console.log(`Creating task in Vibe Kanban...`);
    const taskId = await createTask(taskTitle, taskDescription);
    
    if (taskId) {
        console.log(`Task created successfully with ID: ${taskId}`);
    } else {
        console.log(`Failed to create task.`);
    }
}