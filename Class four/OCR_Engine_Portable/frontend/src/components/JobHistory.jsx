import { useEffect, useState } from 'react';
import { fetchJobs } from '../api/client';

export default function JobHistory({ refreshKey }) {
  const [jobs, setJobs] = useState([]);
  const [expanded, setExpanded] = useState(null);

  useEffect(() => {
    fetchJobs()
      .then(setJobs)
      .catch(() => setJobs([]));
  }, [refreshKey]);

  if (jobs.length === 0) return null;

  return (
    <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Recent Jobs</h2>
      <ul className="divide-y divide-slate-100">
        {jobs.map((job) => (
          <li key={job.job_id} className="py-3">
            <button
              type="button"
              onClick={() => setExpanded(expanded === job.job_id ? null : job.job_id)}
              className="w-full text-left flex items-center justify-between"
            >
              <div>
                <span className="text-sm font-mono text-slate-600">
                  {job.job_id.slice(0, 8)}…
                </span>
                <span className="ml-2 text-xs text-slate-400">
                  {job.file_count} file(s)
                </span>
              </div>
              <span
                className={`text-xs font-medium px-2 py-0.5 rounded-full ${
                  job.status === 'completed'
                    ? 'bg-green-100 text-green-700'
                    : job.status === 'failed'
                      ? 'bg-red-100 text-red-700'
                      : 'bg-yellow-100 text-yellow-700'
                }`}
              >
                {job.status}
              </span>
            </button>
            {expanded === job.job_id && (
              <div className="mt-2 text-xs text-slate-500 space-y-1">
                <p>Created: {new Date(job.created_at).toLocaleString()}</p>
                {job.md_files?.length > 0 && (
                  <ul>
                    {job.md_files.map((path) => (
                      <li key={path}>MD: {path}</li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </li>
        ))}
      </ul>
    </section>
  );
}
