export interface Task {
    id: string;
    title: string;
    status: 'todo' | 'inprogress' | 'inreview' | 'done' | 'cancelled';
    description?: string;
    created_at: string;
}

export interface Project {
    id: string;
    path: string;
    name: string;
}

const API_BASE = 'http://127.0.0.1:45613/api';

export async function getTasks(): Promise<Task[]> {
    // In production (GitHub Pages), we can't fetch localhost.
    // So we return mock data or empty array if we are not in DEV mode.
    // OR we could fetch from a JSON file if we decided to export tasks at build time.
    
    if (!import.meta.env.DEV) {
        console.warn('Vibe Kanban fetching is disabled in production (cannot reach localhost)');
        return [];
    }

    try {
        const response = await fetch(`${API_BASE}/tasks`);
        if (!response.ok) {
            throw new Error(`Failed to fetch tasks: ${response.statusText}`);
        }
        const data = await response.json();
        // The API returns { tasks: Task[], count: number, ... }
        return data.tasks || [];
    } catch (error) {
        console.error('Error fetching Vibe Kanban tasks:', error);
        return [];
    }
}
