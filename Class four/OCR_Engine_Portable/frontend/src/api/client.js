const API_BASE = '/api/v1';

function formatApiError(detail, status) {
  if (!detail) return `Request failed (${status})`;
  if (typeof detail === 'string') return detail;
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg || JSON.stringify(item)).join('; ');
  }
  return String(detail);
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

export async function validateOutputPath(outputFolder) {
  const res = await fetch(`${API_BASE}/ocr/validate-path`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ output_folder: outputFolder }),
  });
  return res.json();
}

export async function browseOutputFolder() {
  let res;
  try {
    res = await fetch(`${API_BASE}/ocr/browse-folder`);
  } catch {
    throw new Error('Could not reach the OCR backend to open folder picker.');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatApiError(err.detail, res.status));
  }

  return res.json();
}

export async function startOcrJob(files, outputFolder) {
  const formData = new FormData();
  for (const file of files) {
    formData.append('files', file);
  }
  formData.append('output_folder', outputFolder);

  let res;
  try {
    res = await fetch(`${API_BASE}/ocr/upload`, {
      method: 'POST',
      body: formData,
    });
  } catch {
    throw new Error('Could not reach the OCR backend. Make sure the backend server is running.');
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({}));
    throw new Error(formatApiError(err.detail, res.status));
  }

  return res.json();
}

export async function fetchJob(jobId, { retries = 8, retryDelayMs = 400 } = {}) {
  for (let attempt = 0; attempt <= retries; attempt += 1) {
    let res;
    try {
      res = await fetch(`${API_BASE}/ocr/jobs/${jobId}`);
    } catch {
      if (attempt < retries) {
        await sleep(retryDelayMs);
        continue;
      }
      throw new Error('Could not reach the OCR backend while checking job status.');
    }

    if (res.ok) {
      return res.json();
    }

    if (res.status === 404 && attempt < retries) {
      await sleep(retryDelayMs);
      continue;
    }

    const err = await res.json().catch(() => ({}));
    throw new Error(formatApiError(err.detail, res.status) || 'Job not found');
  }

  throw new Error('Job not found');
}

export async function pollJobUntilComplete(jobId, onUpdate, intervalMs = 800) {
  while (true) {
    const job = await fetchJob(jobId);
    onUpdate(job);

    if (job.status === 'completed') {
      return job;
    }
    if (job.status === 'failed') {
      throw new Error(job.export_error || job.progress?.message || 'OCR job failed');
    }

    await sleep(intervalMs);
  }
}

export async function uploadAndOcr(files, outputFolder, onProgress) {
  const started = await startOcrJob(files, outputFolder);
  if (!started?.job_id) {
    throw new Error('Backend did not return a job id');
  }

  return pollJobUntilComplete(started.job_id, (job) => {
    if (onProgress) onProgress(job.progress || null, job);
  });
}

export async function fetchJobs() {
  const res = await fetch(`${API_BASE}/ocr/jobs`);
  if (!res.ok) throw new Error('Failed to fetch jobs');
  return res.json();
}

export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
