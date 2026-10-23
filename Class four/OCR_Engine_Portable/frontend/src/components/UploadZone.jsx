import { useCallback, useRef, useState } from 'react';

export default function UploadZone({ onFilesSelected, disabled }) {
  const [dragOver, setDragOver] = useState(false);
  const fileInputRef = useRef(null);
  const folderInputRef = useRef(null);

  const handleFiles = useCallback(
    (fileList) => {
      const files = Array.from(fileList);
      if (files.length > 0) onFilesSelected(files);
    },
    [onFilesSelected],
  );

  const onDrop = (e) => {
    e.preventDefault();
    setDragOver(false);
    if (!disabled) handleFiles(e.dataTransfer.files);
  };

  return (
    <section className="bg-white rounded-xl shadow-sm border border-slate-200 p-6">
      <h2 className="text-lg font-semibold text-slate-800 mb-4">Upload Documents</h2>

      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={onDrop}
        className={`border-2 border-dashed rounded-xl p-10 text-center transition-colors ${
          dragOver ? 'border-blue-400 bg-blue-50' : 'border-slate-300 bg-slate-50'
        } ${disabled ? 'opacity-50 pointer-events-none' : ''}`}
      >
        <p className="text-slate-600 mb-4">
          Drag and drop images or PDFs here
        </p>
        <div className="flex justify-center gap-3">
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={disabled}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-blue-600 text-white hover:bg-blue-700 disabled:opacity-50"
          >
            Select Files
          </button>
          <button
            type="button"
            onClick={() => folderInputRef.current?.click()}
            disabled={disabled}
            className="px-4 py-2 text-sm font-medium rounded-lg bg-slate-200 text-slate-700 hover:bg-slate-300 disabled:opacity-50"
          >
            Select Folder
          </button>
        </div>
        <p className="text-xs text-slate-400 mt-3">
          Supported: PNG, JPG, WEBP, TIFF, PDF
        </p>
      </div>

      <input
        ref={fileInputRef}
        type="file"
        multiple
        accept=".png,.jpg,.jpeg,.webp,.tiff,.tif,.pdf,image/*,application/pdf"
        className="hidden"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = '';
        }}
      />
      <input
        ref={folderInputRef}
        type="file"
        webkitdirectory=""
        directory=""
        multiple
        className="hidden"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = '';
        }}
      />
    </section>
  );
}
