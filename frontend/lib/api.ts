const API_BASE = process.env.NEXT_PUBLIC_API_URL || "https://zeroij-exovetter-api.hf.space";

async function postJSON(url: string, body: object) {
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ message: res.statusText }));
    throw new Error(err.message || `Request failed: ${res.statusText}`);
  }
  return res.json();
}

export async function stepUpload(file: File) {
  const formData = new FormData();
  formData.append("file", file);
  const res = await fetch(`${API_BASE}/api/step/upload`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error(body.message || `Upload failed: ${res.statusText}`);
  }
  return res.json();
}

export async function stepRunTLS(sessionId: string) {
  return postJSON(`${API_BASE}/api/step/tls`, { session_id: sessionId });
}

export async function stepRunFeatures(sessionId: string) {
  return postJSON(`${API_BASE}/api/step/features`, { session_id: sessionId });
}

export async function stepRunClassify(sessionId: string) {
  return postJSON(`${API_BASE}/api/step/classify`, { session_id: sessionId });
}

export async function stepRunParameters(sessionId: string) {
  return postJSON(`${API_BASE}/api/step/parameters`, { session_id: sessionId });
}

export async function stepRunOutput(sessionId: string) {
  return postJSON(`${API_BASE}/api/step/output`, { session_id: sessionId });
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
