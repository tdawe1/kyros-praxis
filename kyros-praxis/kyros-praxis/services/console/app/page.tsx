'use client';

import React, { useState } from 'react';
import { Job, JobSchema, validate } from '@kyros/core';

// Typed API Client example
async function fetchJobs(): Promise<Job[]> {
  // Mock API call - integrate with orchestrator contracts in production
  const mockData = [
    { id: '1', status: 'pending' as const, spec: { task: 'scaffold' } },
    { id: '2', status: 'completed' as const, spec: { task: 'build' } },
  ];
  return mockData.map((jobData) => validate(JobSchema, jobData));
}

export default function Home() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const fetchedJobs = await fetchJobs();
      setJobs(fetchedJobs);
    } catch (err) {
      setError('Failed to load jobs');
      console.error('API error:', err);
    }
    setLoading(false);
  };

  return (
    <div className="max-w-4xl mx-auto">
      <h2 className="text-2xl font-bold mb-4">Jobs Dashboard</h2>
      <button 
        onClick={loadJobs} 
        disabled={loading}
        className="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded mb-4 disabled:opacity-50"
      >
        {loading ? 'Loading...' : 'Load Jobs'}
      </button>
      {error && <div className="text-red-500 mb-4">{error}</div>}
      <div className="grid gap-4">
        {jobs.length > 0 ? (
          jobs.map((job) => (
            <div key={job.id} className="border p-4 rounded">
              <h3 className="font-semibold">Job {job.id}</h3>
              <p>Status: <span className={`capitalize ${job.status === 'completed' ? 'text-green-600' : job.status === 'failed' ? 'text-red-600' : 'text-yellow-600'}`}>{job.status}</span></p>
              {job.spec && <p>Spec: {JSON.stringify(job.spec)}</p>}
            </div>
          ))
        ) : (
          <p>No jobs loaded. Click the button to fetch jobs using typed API client with Zod validation.</p>
        )}
      </div>
    </div>
  );
}