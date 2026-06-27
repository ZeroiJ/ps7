import type { UploadResponse, ProcessResponse } from "./types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function stepUpload(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/step/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);
  return res.json();
}

export async function stepRunTLS(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/step/tls`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error(`TLS search failed: ${res.statusText}`);
  return res.json();
}

export async function stepRunClassify(sessionId: string) {
  const res = await fetch(`${API_BASE}/api/step/classify`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  if (!res.ok) throw new Error(`Classification failed: ${res.statusText}`);
  return res.json();
}

export async function getSampleData() {
  const res = await fetch(`${API_BASE}/api/sample-data`);
  if (!res.ok) throw new Error(`Sample data failed: ${res.statusText}`);
  return res.json();
}

export async function downloadResults(jobId: string) {
  const res = await fetch(`${API_BASE}/api/download/${jobId}`);
  if (!res.ok) throw new Error(`Download failed: ${res.status}`);

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
