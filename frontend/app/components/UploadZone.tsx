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

function getExtBadge(name: string): string {
  const ext = name.split(".").pop()?.toUpperCase() || "";
  return ext;
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
      <div className="w-full max-w-3xl mx-auto px-6">
        <div className="rounded-lg border border-chroma-border p-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* File icon */}
              <div className="w-10 h-10 rounded-lg bg-chroma-muted flex items-center justify-center">
                <svg
                  width="20"
                  height="20"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="text-chroma-muted-fg"
                >
                  <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z" />
                  <polyline points="14 2 14 8 20 8" />
                </svg>
              </div>
              <div className="flex flex-col">
                <span className="text-sm font-medium text-chroma-fg">
                  {file.name}
                </span>
                <span className="text-xs text-chroma-muted-fg">
                  {formatFileSize(file.size)}
                </span>
              </div>
              <span className="px-2 py-0.5 rounded text-xs font-mono bg-chroma-muted text-chroma-muted-fg">
                {getExtBadge(file.name)}
              </span>
            </div>
            <button
              onClick={removeFile}
              className="p-1.5 rounded-lg hover:bg-chroma-muted transition-colors cursor-pointer"
              aria-label="Remove file"
            >
              <svg
                width="16"
                height="16"
                viewBox="0 0 16 16"
                fill="none"
                xmlns="http://www.w3.org/2000/svg"
              >
                <path
                  d="M4 4L12 12M12 4L4 12"
                  stroke="currentColor"
                  strokeWidth="1.5"
                  strokeLinecap="round"
                />
              </svg>
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="w-full max-w-3xl mx-auto px-6">
      <div
        {...getRootProps()}
        className={`min-h-[300px] rounded-lg border-2 border-dashed flex flex-col items-center justify-center gap-4 cursor-pointer transition-colors ${
          isDragActive
            ? "border-chroma-primary bg-chroma-muted"
            : "border-chroma-border hover:border-chroma-muted-fg"
        }`}
      >
        <input {...getInputProps()} />

        {/* Upload icon */}
        <svg
          width="40"
          height="40"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="text-chroma-muted-fg"
        >
          <path d="M21 15v4a2 2 0 01-2 2H5a2 2 0 01-2-2v-4" />
          <polyline points="17 8 12 3 7 8" />
          <line x1="12" y1="3" x2="12" y2="15" />
        </svg>

        <div className="flex flex-col items-center gap-1">
          <span className="text-sm text-chroma-fg font-medium">
            {isDragActive ? "Drop your file here" : "Drop your file here"}
          </span>
          <span className="text-xs text-chroma-muted-fg">
            CSV, JSON, NPZ up to 200 MB
          </span>
        </div>
      </div>
    </div>
  );
}
