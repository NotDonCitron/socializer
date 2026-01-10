import React, { useEffect, useState } from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';

interface Stat {
  repo: string;
  impact: number;
  count: number;
}

const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

export default function ImpactChart() {
  const [data, setData] = useState<Stat[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const response = await fetch('http://localhost:8000/posts/stats/impact');
        if (response.ok) {
          const stats = await response.json();
          // Sort by impact descending
          setData(stats.sort((a: Stat, b: Stat) => b.impact - a.impact));
        }
      } catch (error) {
        console.error("Error fetching stats:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  if (loading) return <div className="h-64 flex items-center justify-center text-gray-500">Analyzing impact...</div>;
  if (data.length === 0) return null;

  return (
    <div className="bg-white border rounded-lg p-6 shadow-sm mb-8">
      <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
        <span>📊 Project Impact Analysis</span>
        <span className="text-xs font-normal text-gray-500">Based on published updates</span>
      </h2>
      
      <div className="h-64 w-full">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={data} layout="vertical" margin={{ left: 40, right: 30 }}>
            <CartesianGrid strokeDasharray="3 3" horizontal={true} vertical={false} stroke="#f0f0f0" />
            <XAxis type="number" hide />
            <YAxis 
              dataKey="repo" 
              type="category" 
              tick={{ fontSize: 12, fill: '#666' }}
              width={100}
            />
            <Tooltip 
              cursor={{ fill: '#f8fafc' }}
              contentStyle={{ borderRadius: '8px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
            />
            <Bar dataKey="impact" radius={[0, 4, 4, 0]} barSize={24}>
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
