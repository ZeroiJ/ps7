"use client";

import { useCallback, useRef, useState, useMemo } from "react";
import { stepUpload, stepRunTLS, stepRunClassify, getSampleData, downloadResults } from "@/lib/api";

import UploadZone from "./components/UploadZone";
import ChartCard from "./components/ChartCard";
import MetricCard from "./components/MetricCard";
import VerdictBadge from "./components/VerdictBadge";
import Toast from "./components/Toast";

const STEPS = ["Upload", "Preprocess", "Transit Search", "Verify"];

export default function Home() {
  const uploadRef = useRef<HTMLDivElement>(null);
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" | "info" } | null>(null);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [results, setResults] = useState<{
    preprocess: any;
    tls: any;
    classify: any;
  }>({
    preprocess: null,
    tls: null,
    classify: null,
  });

  const showError = useCallback((msg: string) => {
    setError(msg);
    setToast({ message: msg, type: "error" });
  }, []);

  const handleReset = useCallback(() => {
    setSessionId(null);
    setCurrentStep(0);
    setResults({ preprocess: null, tls: null, classify: null });
    setError(null);
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, []);

  const handleFileAccepted = useCallback(
    async (file: File) => {
      setLoading(true);
      setError(null);
      try {
        const res = await stepUpload(file);
        setSessionId(res.session_id);
        setResults((prev) => ({ ...prev, preprocess: res }));
        setCurrentStep(1);
        setToast({ message: "Upload & preprocessing complete", type: "success" });
      } catch (err) {
        showError(err instanceof Error ? err.message : "Upload failed");
      } finally {
        setLoading(false);
      }
    },
    [showError]
  );

  const handleSampleClick = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await getSampleData();
      setSessionId(res.session_id);
      setResults((prev) => ({ ...prev, preprocess: res }));
      setCurrentStep(1);
      setToast({ message: "Sample data loaded", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "Failed to load sample data");
    } finally {
      setLoading(false);
    }
  }, [showError]);

  const handleRunTLS = async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await stepRunTLS(sessionId);
      setResults((prev) => ({ ...prev, tls: res }));
      setCurrentStep(2);
      setToast({ message: "Transit search complete", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "TLS search failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRunClassify = async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await stepRunClassify(sessionId);
      setResults((prev) => ({ ...prev, classify: res }));
      setCurrentStep(3);
      setToast({ message: "Classification complete", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "Classification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async () => {
    if (sessionId) {
      try {
        await downloadResults(sessionId);
      } catch (err) {
        showError(err instanceof Error ? err.message : "Download failed");
      }
    }
  };

  // ── Stepper ──
  const stepper = useMemo(() => {
    if (currentStep === 0) return null;
    return (
      <div className="flex items-center gap-0">
        {STEPS.map((label, idx) => {
          const isActive = idx === currentStep;
          const isDone = idx < currentStep;
          return (
            <div key={label} className="flex items-center">
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm font-medium transition-colors ${
                    isDone
                      ? "text-chroma-fg"
                      : isActive
                      ? "text-chroma-fg"
                      : "text-chroma-muted-fg"
                  }`}
                >
                  {label}
                </span>
                {isDone && (
                  <svg
                    width="14"
                    height="14"
                    viewBox="0 0 14 14"
                    fill="none"
                    className="text-chroma-success"
                  >
                    <path
                      d="M3 7L6 10L11 4"
                      stroke="currentColor"
                      strokeWidth="1.5"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                    />
                  </svg>
                )}
              </div>
              {idx < STEPS.length - 1 && (
                <div
                  className={`w-8 h-px mx-3 ${
                    isDone ? "bg-chroma-fg" : "bg-chroma-border"
                  }`}
                />
              )}
            </div>
          );
        })}
      </div>
    );
  }, [currentStep]);

  return (
    <div className="min-h-screen flex flex-col">
      <main className="flex-1 w-full max-w-5xl mx-auto px-6 py-12">
        {/* ── Step 0: Upload ── */}
        {currentStep === 0 && (
          <div className="bento-grid" ref={uploadRef}>
            <div className="bento-card col-span-full" style={{ padding: 0, border: "none", background: "transparent" }}>
              <UploadZone onFileAccepted={handleFileAccepted} />
            </div>
            {loading && (
              <div className="col-span-full">
                <div className="w-full h-1 bg-chroma-border overflow-hidden">
                  <div className="h-full bg-chroma-primary animate-pulse-ring w-2/3" />
                </div>
              </div>
            )}
            <div className="col-span-full flex justify-center gap-3 pt-2">
              <button
                onClick={handleSampleClick}
                disabled={loading}
                className="text-sm text-chroma-muted-fg hover:text-chroma-fg transition-colors cursor-pointer disabled:opacity-50 border-b border-transparent hover:border-chroma-fg pb-px"
              >
                Try sample data instead
              </button>
            </div>
          </div>
        )}

        {/* ── Stepper ── */}
        {currentStep > 0 && (
          <div className="bento-enter mb-10">{stepper}</div>
        )}

        {/* ── Step 1: Preprocess Results ── */}
        {currentStep >= 1 && results.preprocess && (
          <div
            className={`bento-grid mb-10 ${currentStep === 1 ? "bento-enter" : ""}`}
            ref={currentStep === 1 ? uploadRef : null}
          >
            <div className="col-span-full flex items-center justify-between">
              <span className="bento-label">Preprocessing</span>
              <span className="text-sm text-chroma-success">Complete</span>
            </div>

            {/* Chart — spans 3 cols */}
            <div className="col-span-3">
              <ChartCard
                title="Raw vs Cleaned Flux"
                data={[
                  {
                    x: results.preprocess.cleaned_flux_chart_data.raw_time,
                    y: results.preprocess.cleaned_flux_chart_data.raw_flux,
                    type: "scattergl",
                    mode: "markers",
                    marker: { color: "#d4d4d4", size: 2 },
                    name: "Raw",
                  },
                  {
                    x: results.preprocess.cleaned_flux_chart_data.cleaned_time,
                    y: results.preprocess.cleaned_flux_chart_data.cleaned_flux,
                    type: "scattergl",
                    mode: "markers",
                    marker: { color: "#141414", size: 2 },
                    name: "Cleaned",
                  },
                ]}
                layout={{
                  xaxis: { title: { text: "Time (BTJD)" } },
                  yaxis: { title: { text: "Flux" } },
                  showlegend: true,
                  legend: { x: 0, y: 1, font: { size: 10 } },
                }}
              />
            </div>

            {/* Stats — stacked in 1 col */}
            <div className="col-span-1 flex flex-col gap-3">
              <div className="bento-card flex-1 flex flex-col justify-center">
                <span className="bento-label mb-1">Raw points</span>
                <span className="text-2xl font-semibold tracking-tight font-mono text-chroma-fg">
                  {results.preprocess.stats.n_points_raw.toLocaleString()}
                </span>
              </div>
              <div className="bento-card flex-1 flex flex-col justify-center">
                <span className="bento-label mb-1">Outliers removed</span>
                <span className="text-2xl font-semibold tracking-tight font-mono text-chroma-error">
                  {results.preprocess.stats.outliers_removed.toLocaleString()}
                </span>
              </div>
              <div className="bento-card flex-1 flex flex-col justify-center">
                <span className="bento-label mb-1">Cleaned points</span>
                <span className="text-2xl font-semibold tracking-tight font-mono text-chroma-fg">
                  {results.preprocess.stats.n_points.toLocaleString()}
                </span>
              </div>
            </div>

            {/* Action */}
            {currentStep === 1 && (
              <div className="col-span-full flex justify-center pt-2">
                <button
                  onClick={handleRunTLS}
                  disabled={loading}
                  className="bg-chroma-primary text-chroma-primary-fg px-5 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-50"
                >
                  {loading ? "Processing..." : "Run Transit Search"}
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── Step 2: TLS Results ── */}
        {currentStep >= 2 && results.tls && (
          <div className={`bento-grid mb-10 ${currentStep === 2 ? "bento-enter" : ""}`}>
            <div className="col-span-full flex items-center justify-between">
              <span className="bento-label">Transit Search</span>
              <span className="text-sm text-chroma-success">Complete</span>
            </div>

            {/* Metrics — 5 in a row */}
            <MetricCard label="Period" value={results.tls.period.toFixed(4)} unit="days" />
            <MetricCard label="Depth" value={results.tls.depth.toFixed(1)} unit="ppm" />
            <MetricCard label="Duration" value={results.tls.duration.toFixed(1)} unit="hrs" />
            <MetricCard label="SNR" value={results.tls.snr.toFixed(1)} />
            <MetricCard label="SDE" value={results.tls.sde.toFixed(1)} />

            {/* Charts */}
            <div className="col-span-3">
              <ChartCard
                title="Periodogram"
                data={[{
                  x: results.tls.periodogram_chart_data.frequency,
                  y: results.tls.periodogram_chart_data.power,
                  type: "scatter",
                  mode: "lines",
                  line: { color: "#141414", width: 1 },
                }]}
                layout={{
                  xaxis: { title: { text: "Frequency (1/d)" } },
                  yaxis: { title: { text: "Power" } },
                }}
              />
            </div>
            <div className="col-span-2">
              <ChartCard
                title="Phase-Folded Light Curve"
                data={[
                  {
                    x: results.tls.phase_fold_chart_data.phase,
                    y: results.tls.phase_fold_chart_data.flux,
                    type: "scattergl",
                    mode: "markers",
                    marker: { color: "#141414", size: 2 },
                    name: "Data",
                  },
                  {
                    x: results.tls.phase_fold_chart_data.phase,
                    y: results.tls.phase_fold_chart_data.model,
                    type: "scatter",
                    mode: "lines",
                    line: { color: "#ef4444", width: 2 },
                    name: "Model",
                  },
                ]}
                layout={{
                  xaxis: { title: { text: "Phase" } },
                  yaxis: { title: { text: "Flux" } },
                  showlegend: true,
                  legend: { x: 0, y: 1, font: { size: 10 } },
                }}
              />
            </div>

            {/* Action */}
            {currentStep === 2 && (
              <div className="col-span-full flex justify-center pt-2">
                <button
                  onClick={handleRunClassify}
                  disabled={loading}
                  className="bg-chroma-primary text-chroma-primary-fg px-5 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-50"
                >
                  {loading ? "Processing..." : "Run Classification"}
                </button>
              </div>
            )}
          </div>
        )}

        {/* ── Step 3: Classification ── */}
        {currentStep === 3 && results.classify && (
          <div className="bento-grid bento-enter">
            <div className="col-span-full flex items-center justify-between">
              <span className="bento-label">Classification</span>
              <span className="text-sm text-chroma-success">Complete</span>
            </div>

            {/* Verdict Card */}
            <div className="col-span-2 bento-card flex flex-col items-center justify-center py-10">
              <span className="bento-label mb-4">Final Verdict</span>
              <VerdictBadge verdict={results.classify.verdict} />
              <p className="text-sm text-chroma-muted-fg mt-3">
                Confidence: {(results.classify.confidence * 100).toFixed(1)}%
              </p>
            </div>

            {/* Probabilities Chart */}
            <div className="col-span-3">
              <ChartCard
                title="Classification Probabilities"
                data={[{
                  x: results.classify.classification_chart_data.classes,
                  y: results.classify.classification_chart_data.probabilities,
                  type: "bar",
                  marker: {
                    color: results.classify.classification_chart_data.classes.map((c: string) => {
                      if (c === "planet") return "#4ade80";
                      if (c === "fp") return "#ef4444";
                      return "#d4d4d4";
                    }),
                  },
                }]}
                layout={{
                  xaxis: { title: { text: "Class" } },
                  yaxis: { title: { text: "Probability" }, range: [0, 1] },
                }}
              />
            </div>

            {/* Actions */}
            <div className="col-span-full flex items-center justify-center gap-4 pt-6 border-t border-chroma-border mt-2">
              <button
                onClick={handleDownload}
                className="bg-chroma-primary text-chroma-primary-fg px-5 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
              >
                Download Results
              </button>
              <button
                onClick={handleReset}
                className="text-sm text-chroma-muted-fg hover:text-chroma-fg transition-colors cursor-pointer border-b border-transparent hover:border-chroma-fg pb-px"
              >
                Analyze another file
              </button>
            </div>
          </div>
        )}

        {/* ── Error Display ── */}
        {error && currentStep === 0 && (
          <div className="bento-grid mt-8">
            <div className="col-span-full bento-card flex flex-col items-center py-10">
              <p className="text-sm text-chroma-fg mb-6">{error}</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReset}
                  className="text-sm text-chroma-muted-fg hover:text-chroma-fg transition-colors cursor-pointer border-b border-transparent hover:border-chroma-fg pb-px"
                >
                  Start over
                </button>
                <button
                  onClick={handleSampleClick}
                  className="bg-chroma-primary text-chroma-primary-fg px-4 py-2 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
                >
                  Try sample data
                </button>
              </div>
            </div>
          </div>
        )}

        {/* ── Footer ── */}
        <footer className="mt-20 pt-8 border-t border-chroma-border flex items-center justify-between">
          <span className="text-sm text-chroma-muted-fg">ExoVetter</span>
          <span className="text-xs text-chroma-muted-fg">BAH 2026 — Challenge 7</span>
        </footer>
      </main>

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}
