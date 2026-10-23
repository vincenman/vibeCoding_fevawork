import { useState } from 'react';
import ReactMarkdown from 'react-markdown';

function downloadText(content, filename) {
  const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

export default function ResultsViewer({ result }) {
  const [activeTab, setActiveTab] = useState('text');
  const [selectedFileIdx, setSelectedFileIdx] = useState(0);

  if (!result || !result.files?.length) return null;

  const file = result.files[selectedFileIdx] || result.files[0];
  const allText = result.files
    .filter((f) => f.success && f.text)
    .map((f) => `# ${f.filename}\n\n${f.text}`)
    .join('\n\n---\n\n');

  const tabs = [
    { id: 'text', label: 'Plain Text' },
    { id: 'markdown', label: 'Markdown Preview' },
    { id: 'json', label: 'JSON' },
  ];

  const copyToClipboard = async (text) => {
    await navigator.clipboard.writeText(text);
  };

  return (
    <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-slate-800">Results</h2>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => copyToClipboard(file.text || '')}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200"
          >
            Copy
          </button>
          <button
            type="button"
            onClick={() => downloadText(allText, 'ocr_results.md')}
            className="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200"
          >
            Download .md
          </button>
        </div>
      </div>

      {result.files.length > 1 && (
        <div className="flex flex-wrap gap-2 mb-4">
          {result.files.map((f, idx) => (
            <button
              key={f.filename + idx}
              type="button"
              onClick={() => setSelectedFileIdx(idx)}
              className={`px-3 py-1 text-xs rounded-full border ${
                idx === selectedFileIdx
                  ? 'bg-blue-100 border-blue-300 text-blue-800'
                  : 'bg-slate-50 border-slate-200 text-slate-600'
              }`}
            >
              {f.filename} {f.success ? '✓' : '✗'}
            </button>
          ))}
        </div>
      )}

      <div className="flex border-b border-slate-200 mb-4">
        {tabs.map((tab) => (
          <button
            key={tab.id}
            type="button"
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 text-sm font-medium border-b-2 -mb-px ${
              activeTab === tab.id
                ? 'border-blue-600 text-blue-600'
                : 'border-transparent text-slate-500 hover:text-slate-700'
            }`}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {!file.success && (
        <div className="rounded-lg bg-red-50 border border-red-200 p-4 text-sm text-red-700">
          Error processing {file.filename}: {file.error}
        </div>
      )}

      {file.success && activeTab === 'text' && (
        <pre className="text-sm text-slate-700 whitespace-pre-wrap bg-slate-50 rounded-lg p-4 max-h-96 overflow-auto">
          {file.text}
        </pre>
      )}

      {file.success && activeTab === 'markdown' && (
        <div className="markdown-preview text-sm text-slate-700 bg-slate-50 rounded-lg p-4 max-h-96 overflow-auto">
          <ReactMarkdown>{file.text}</ReactMarkdown>
        </div>
      )}

      {activeTab === 'json' && (
        <pre className="text-sm text-slate-700 whitespace-pre-wrap bg-slate-50 rounded-lg p-4 max-h-96 overflow-auto">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </section>
  );
}
