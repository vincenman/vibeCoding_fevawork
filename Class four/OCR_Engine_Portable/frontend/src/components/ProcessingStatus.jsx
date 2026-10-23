function stageLabel(stage) {
  switch (stage) {
    case 'uploading':
      return 'Uploading';
    case 'queued':
      return 'Queued';
    case 'processing':
      return 'Processing';
    case 'exporting':
      return 'Saving';
    case 'completed':
      return 'Completed';
    case 'failed':
      return 'Failed';
    default:
      return 'Working';
  }
}

export default function ProcessingStatus({ processing, progress, result, error }) {
  if (!processing && !result && !error) return null;

  const percent = progress?.percent ?? (processing ? 5 : result ? 100 : 0);
  const message = progress?.message || (processing ? 'Starting OCR…' : '');

  return (
    <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Processing Status</h2>

      {processing && (
        <div className="space-y-3">
          <div className="flex items-center justify-between text-sm">
            <span className="font-medium text-slate-700">
              {stageLabel(progress?.stage)}
              {progress?.current_filename ? `: ${progress.current_filename}` : ''}
            </span>
            <span className="text-slate-500">{percent}%</span>
          </div>

          <div className="h-2.5 w-full rounded-full bg-slate-200 overflow-hidden">
            <div
              className="h-full rounded-full bg-blue-600 transition-all duration-500 ease-out"
              style={{ width: `${Math.max(percent, processing ? 5 : 0)}%` }}
            />
          </div>

          <p className="text-sm text-slate-600">{message}</p>

          {progress?.total_files > 0 && (
            <p className="text-xs text-slate-400">
              File {Math.max(progress.current_file, 0)} of {progress.total_files}
              {progress.current_page && progress.total_pages > 1
                ? ` · Page ${progress.current_page} of ${progress.total_pages}`
                : ''}
            </p>
          )}
        </div>
      )}

      {error && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          {error}
        </div>
      )}

      {result && !processing && (
        <div className="space-y-3">
          <div className="h-2.5 w-full rounded-full bg-slate-200 overflow-hidden">
            <div className="h-full w-full rounded-full bg-green-500" />
          </div>

          <div className="rounded-lg bg-green-50 border border-green-200 p-4 text-sm text-green-800">
            Job <code className="font-mono">{result.job_id.slice(0, 8)}…</code> completed
            {result.md_files?.length > 0 && (
              <div className="mt-2 space-y-1">
                <p>Markdown files saved:</p>
                <ul className="list-disc list-inside">
                  {result.md_files.map((path) => (
                    <li key={path}><strong>{path}</strong></li>
                  ))}
                </ul>
              </div>
            )}
          </div>

          {result.export_error && (
            <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
              Export warning: {result.export_error}. OCR text is still available below.
            </div>
          )}
        </div>
      )}
    </section>
  );
}
