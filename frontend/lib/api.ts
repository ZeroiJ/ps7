import type { UploadResponse, ProcessResponse } from "./types";

const API_BASE =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE}/api/upload`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `Upload failed: ${res.status}`);
  }

  return res.json();
}

export async function processFile(jobId: string): Promise<ProcessResponse> {
  const res = await fetch(`${API_BASE}/api/process/${jobId}`, {
    method: "POST",
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `Processing failed: ${res.status}`);
  }

  return res.json();
}

export async function getSampleData(): Promise<UploadResponse> {
  const res = await fetch(`${API_BASE}/api/sample-data`);

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `Sample data failed: ${res.status}`);
  }

  return res.json();
}

export async function checkStatus(jobId: string): Promise<ProcessResponse> {
  const res = await fetch(`${API_BASE}/api/status/${jobId}`);

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || err.message || `Status check failed: ${res.status}`);
  }

  return res.json();
}

export async function downloadResults(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/download/${jobId}`);

  if (!res.ok) {
    throw new Error(`Download failed: ${res.status}`);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `exovetter-results-${jobId}.zip`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
