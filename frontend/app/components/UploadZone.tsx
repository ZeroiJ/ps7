"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";

interface UploadZoneProps {
  onFileAccepted: (file: File) => void;
}

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function UploadZone({ onFileAccepted }: UploadZoneProps) {
  const [file, setFile] = useState<File | null>(null);

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      if (acceptedFiles.length > 0) {
        const f = acceptedFiles[0];
        setFile(f);
        onFileAccepted(f);
      }
    },
    [onFileAccepted]
  );

  const removeFile = useCallback(() => {
    setFile(null);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "text/csv": [".csv"],
      "application/json": [".json"],
      "application/octet-stream": [".npz"],
    },
    maxSize: 200 * 1024 * 1024,
    multiple: false,
  });

  if (file) {
    return (
      <div className="bento-card-muted flex items-center justify-between">
        <div className="flex items-center gap-4">
          <div className="w-10 h-10 flex items-center justify-center border border-chroma-border bg-chroma-bg">
            <svg
              width="18"
              height="18"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.5"
              className="text-chroma-muted-fg"
            >
              <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
              <polyline points="14 2 14 8 20 8" />
            </svg>
          </div>
          <div>
            <p className="text-sm font-medium text-chroma-fg">{file.name}</p>
            <p className="text-xs text-chroma-muted-fg mt-0.5">
              {formatFileSize(file.size)}
            </p>
          </div>
        </div>
        <button
          onClick={removeFile}
          className="text-xs text-chroma-muted-fg hover:text-chroma-fg transition-colors cursor-pointer border border-chroma-border px-3 py-1.5 hover:bg-chroma-muted"
          aria-label="Remove file"
        >
          Remove
        </button>
      </div>
    );
  }

  return (
    <div
      {...getRootProps()}
      className={`bento-card-muted flex flex-col items-center justify-center py-16 cursor-pointer transition-colors ${
        isDragActive ? "border-chroma-fg bg-chroma-muted" : ""
      }`}
    >
      <input {...getInputProps()} />

      <svg
        width="32"
        height="32"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1"
        className="text-chroma-muted-fg mb-4"
      >
        <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
        <polyline points="17 8 12 3 7 8" />
        <line x1="12" y1="3" x2="12" y2="15" />
      </svg>

      <p className="text-sm text-chroma-fg mb-1">
        {isDragActive ? "Drop your file" : "Drop your light curve file here"}
      </p>
      <p className="text-xs text-chroma-muted-fg">CSV, JSON, NPZ &mdash; up to 200 MB</p>
    </div>
  );
}
