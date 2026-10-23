import { useState } from 'react';
import { uploadAndOcr } from './api/client';
import OutputPathForm from './components/OutputPathForm';
import UploadZone from './components/UploadZone';
import ProcessingStatus from './components/ProcessingStatus';
import ResultsViewer from './components/ResultsViewer';
import JobHistory from './components/JobHistory';

const STORAGE_KEY = 'ocr_output_folder';
const SUPPORTED_FILE_RE = /\.(png|jpe?g|webp|tiff?|pdf)$/i;

function filterSupportedFiles(files) {
  return files.filter((f) => SUPPORTED_FILE_RE.test(f.name));
}

export default function App() {
  const [outputFolder, setOutputFolder] = useState(
    () => localStorage.getItem(STORAGE_KEY) || '',
  );
  const [selectedFiles, setSelectedFiles] = useState([]);
  const [selectionMessage, setSelectionMessage] = useState('');
  const [processing, setProcessing] = useState(false);
  const [progress, setProgress] = useState(null);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);
  const [refreshKey, setRefreshKey] = useState(0);

  const handleOutputFolderChange = (value) => {
    setOutputFolder(value);
    if (value.trim()) localStorage.setItem(STORAGE_KEY, value);
  };

  const handleFilesSelected = (files) => {
    const allFiles = Array.from(files);
    const supported = filterSupportedFiles(allFiles);

    if (allFiles.length === 0) {
      setSelectionMessage('');
      setSelectedFiles([]);
    } else if (supported.length === 0) {
      setSelectionMessage(
        `No supported files found among ${allFiles.length} selected. Use PNG, JPG, WEBP, TIFF, or PDF.`,
      );
      setSelectedFiles([]);
    } else if (supported.length < allFiles.length) {
      setSelectionMessage(
        `Using ${supported.length} supported file(s); skipped ${allFiles.length - supported.length} unsupported file(s).`,
      );
      setSelectedFiles(supported);
    } else {
      setSelectionMessage('');
      setSelectedFiles(supported);
    }

    setResult(null);
    setError(null);
  };

  const canStart = outputFolder.trim().length > 0 && selectedFiles.length > 0 && !processing;

  const handleStartOcr = async () => {
    if (!outputFolder.trim()) {
      setError('Please enter an output folder path');
      return;
    }
    if (selectedFiles.length === 0) {
      setError('Please select at least one supported file');
      return;
    }

    setProcessing(true);
    setError(null);
    setResult(null);
    setProgress({ stage: 'uploading', percent: 0, message: 'Uploading files…' });

    try {
      const data = await uploadAndOcr(
        selectedFiles,
        outputFolder.trim(),
        (progressUpdate) => setProgress(progressUpdate),
      );
      setResult(data);
      setProgress(data.progress || { stage: 'completed', percent: 100, message: 'OCR job completed' });
      setRefreshKey((k) => k + 1);
    } catch (err) {
      setError(err.message || 'OCR request failed');
    } finally {
      setProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="bg-white border-b border-slate-200">
        <div className="max-w-4xl mx-auto px-6 py-5">
          <h1 className="text-2xl font-bold text-slate-900">OCR Detection Engine</h1>
          <p className="text-sm text-slate-500 mt-1">
            Extract text from images and PDFs, save results as Markdown files
          </p>
        </div>
      </header>

      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        <OutputPathForm
          outputFolder={outputFolder}
          onOutputFolderChange={handleOutputFolderChange}
          disabled={processing}
        />

        <UploadZone
          onFilesSelected={handleFilesSelected}
          disabled={processing}
        />

        {selectionMessage && (
          <div className="rounded-lg bg-amber-50 border border-amber-200 p-4 text-sm text-amber-800">
            {selectionMessage}
          </div>
        )}

        {selectedFiles.length > 0 && (
          <div className="bg-white rounded-xl shadow-sm border border-slate-200 p-4">
            <p className="text-sm text-slate-600 mb-3">
              {selectedFiles.length} file(s) ready to process:
            </p>
            <ul className="text-xs text-slate-500 mb-4 max-h-24 overflow-auto">
              {selectedFiles.map((f) => (
                <li key={`${f.name}-${f.size}-${f.lastModified}`}>{f.name}</li>
              ))}
            </ul>
            {!outputFolder.trim() && (
              <p className="text-sm text-amber-700 mb-3">
                Enter an output folder path above to enable Start OCR.
              </p>
            )}
            <button
              type="button"
              onClick={handleStartOcr}
              disabled={!canStart}
              className="w-full py-3 text-sm font-semibold rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {processing ? 'Processing…' : 'Start OCR'}
            </button>
          </div>
        )}

        <ProcessingStatus
          processing={processing}
          progress={progress}
          result={result}
          error={error}
        />

        <ResultsViewer result={result} />

        <JobHistory refreshKey={refreshKey} />
      </main>
    </div>
  );
}
