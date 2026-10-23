import { useState } from 'react';
import { browseOutputFolder, validateOutputPath } from '../api/client';

export default function OutputPathForm({ outputFolder, onOutputFolderChange, disabled }) {
  const [pathStatus, setPathStatus] = useState(null);
  const [validating, setValidating] = useState(false);
  const [browsing, setBrowsing] = useState(false);

  const handleValidate = async () => {
    if (!outputFolder.trim()) {
      setPathStatus({ valid: false, error: 'Path is required' });
      return;
    }
    setValidating(true);
    try {
      const result = await validateOutputPath(outputFolder);
      setPathStatus(result);
    } catch {
      setPathStatus({ valid: false, error: 'Validation request failed' });
    } finally {
      setValidating(false);
    }
  };

  const handleBrowse = async () => {
    setBrowsing(true);
    setPathStatus(null);
    try {
      const result = await browseOutputFolder();
      if (result.cancelled) return;
      if (result.error) {
        setPathStatus({ valid: false, error: result.error });
        return;
      }
      if (result.folder_path) {
        onOutputFolderChange(result.folder_path);
        setPathStatus({ valid: true, resolved_path: result.folder_path });
      }
    } catch (err) {
      setPathStatus({ valid: false, error: err.message });
    } finally {
      setBrowsing(false);
    }
  };

  return (
    <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-1">Output Location</h2>
      <p className="text-sm text-slate-500 mb-4">
        Choose where Markdown results will be saved. Browse opens a folder picker on this machine.
      </p>

      <div>
        <label htmlFor="output-folder" className="block text-sm font-medium text-slate-700 mb-1">
          Output folder path
        </label>
        <div className="flex gap-2">
          <input
            id="output-folder"
            type="text"
            value={outputFolder}
            onChange={(e) => {
              onOutputFolderChange(e.target.value);
              setPathStatus(null);
            }}
            placeholder="/home/user/ocr_output or C:\OCR_Results"
            disabled={disabled}
            className="flex-1 rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:opacity-50"
          />
          <button
            type="button"
            onClick={handleBrowse}
            disabled={disabled || browsing}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50 whitespace-nowrap"
          >
            {browsing ? 'Opening…' : 'Browse…'}
          </button>
          <button
            type="button"
            onClick={handleValidate}
            disabled={disabled || validating || !outputFolder.trim()}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-100 text-slate-700 hover:bg-slate-200 disabled:opacity-50"
          >
            {validating ? 'Checking…' : 'Validate'}
          </button>
        </div>
        {pathStatus && (
          <p className={`mt-2 text-sm ${pathStatus.valid ? 'text-green-600' : 'text-red-600'}`}>
            {pathStatus.valid
              ? `Valid: ${pathStatus.resolved_path}`
              : pathStatus.error}
          </p>
        )}
      </div>
    </section>
  );
}
