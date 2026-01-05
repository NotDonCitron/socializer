export interface GitHubRelease {
    tag_name: string;
    name: string;
    body: string;
    html_url: string;
    published_at: string;
}

export async function getLatestRelease(owner: string, repo: string): Promise<GitHubRelease | null> {
    const token = import.meta.env.GITHUB_TOKEN || import.meta.env.github_token || process.env.GITHUB_TOKEN || process.env.github_token;
    const url = `https://api.github.com/repos/${owner}/${repo}/releases/latest`;

    try {
        const response = await fetch(url, {
            headers: {
                'Accept': 'application/vnd.github.v3+json',
                ...(token ? { 'Authorization': `token ${token}` } : {}),
                'User-Agent': 'Socializer-Bot'
            }
        });

        if (!response.ok) {
            if (response.status === 404) return null;
            throw new Error(`GitHub API error: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(`Error fetching release for ${owner}/${repo}:`, error);
        return null;
    }
}
