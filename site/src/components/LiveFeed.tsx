import React, { useEffect, useState } from 'react';

interface Post {
  id: number;
  title: string;
  content: string;
  source_repo: string;
  impact_score: number;
  created_at: string;
}

export default function LiveFeed() {
  const [posts, setPosts] = useState<Post[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchPosts() {
      try {
        // Direct fetch to Python backend to bypass static site limitations
        const response = await fetch('http://localhost:8000/posts/');
        if (response.ok) {
          const data = await response.json();
          setPosts(data);
        }
      } catch (error) {
        console.error("Error fetching live feed:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchPosts();
  }, []);

  if (loading) return <div className="p-4 text-gray-500">Loading live feed...</div>;
  if (posts.length === 0) return null;

  return (
    <div className="mt-8 border-t pt-8">
      <h2 className="text-2xl font-bold mb-4 flex items-center gap-2">
        <span>📡 Live Social Feed</span>
        <span className="text-xs bg-blue-100 text-blue-700 px-2 py-1 rounded-full uppercase tracking-wider">Refined & Published</span>
      </h2>
      <div className="space-y-6">
        {posts.map(post => (
          <div key={post.id} className="bg-white border rounded-lg p-6 shadow-sm">
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-bold text-lg">{post.title}</h3>
              <span className="text-xs text-gray-500">{new Date(post.created_at).toLocaleDateString()}</span>
            </div>
            {post.source_repo && post.source_repo !== 'manual' && (
               <div className="inline-block bg-gray-100 text-gray-600 text-xs px-2 py-1 rounded mb-4">
                 Source: {post.source_repo}
               </div>
            )}
            <div className="text-gray-700 whitespace-pre-wrap leading-relaxed">
              {post.content}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
