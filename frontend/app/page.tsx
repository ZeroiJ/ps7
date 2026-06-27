"use client";

import { useCallback, useRef, useState, useMemo } from "react";
import {
  stepUpload,
  stepRunTLS,
  stepRunFeatures,
  stepRunClassify,
  stepRunParameters,
  stepRunOutput,
  getSampleData,
  downloadResults,
} from "@/lib/api";

import UploadZone from "./components/UploadZone";
import ChartCard from "./components/ChartCard";
import MetricCard from "./components/MetricCard";
import VerdictBadge from "./components/VerdictBadge";
import Toast from "./components/Toast";

const STEPS = ["Preprocess", "Transit Search", "Features", "Classify", "Parameters"];

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
    features: any;
    classify: any;
    params: any;
    output: any;
  }>({
    preprocess: null,
    tls: null,
    features: null,
    classify: null,
    params: null,
    output: null,
  });

  const showError = useCallback((msg: string) => {
    setError(msg);
    setToast({ message: msg, type: "error" });
  }, []);

  const handleReset = useCallback(() => {
    setSessionId(null);
    setCurrentStep(0);
    setResults({ preprocess: null, tls: null, features: null, classify: null, params: null, output: null });
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

  const handleRunFeatures = async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await stepRunFeatures(sessionId);
      setResults((prev) => ({ ...prev, features: res }));
      setCurrentStep(3);
      setToast({ message: "Features extracted", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "Feature extraction failed");
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
      setCurrentStep(4);
      setToast({ message: "Classification complete", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "Classification failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRunParameters = async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await stepRunParameters(sessionId);
      setResults((prev) => ({ ...prev, params: res }));
      setCurrentStep(5);
      setToast({ message: "Parameters estimated", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "Parameter estimation failed");
    } finally {
      setLoading(false);
    }
  };

  const handleRunOutput = async () => {
    if (!sessionId) return;
    setLoading(true);
    setError(null);
    try {
      const res = await stepRunOutput(sessionId);
      setResults((prev) => ({ ...prev, output: res }));
      setCurrentStep(6);
      setToast({ message: "Report ready", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "Output assembly failed");
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
    const cur = currentStep > 5 ? 5 : currentStep;
    return (
      <div className="flex items-center gap-0 overflow-x-auto w-full mb-8">
        {STEPS.map((label, idx) => {
          const stepNum = idx + 1;
          const isActive = stepNum === cur;
          const isDone = stepNum < cur;
          return (
            <div key={label} className="flex items-center shrink-0">
              <div className="flex items-center gap-2">
                <span
                  className={`text-sm font-medium transition-colors whitespace-nowrap ${
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
                    className="text-chroma-success shrink-0"
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
                  className={`w-8 h-px mx-3 shrink-0 ${
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
    <div className="min-h-screen flex flex-col bg-chroma-bg">
      <main className="flex-1 w-full max-w-[1800px] mx-auto px-4 py-8 flex flex-col">
        {/* ── Step 0: Upload ── */}
        {currentStep === 0 && (
          <div className="w-full max-w-3xl mx-auto mt-20" ref={uploadRef}>
            <div className="bento-card border border-chroma-border bg-white p-8">
              <UploadZone onFileAccepted={handleFileAccepted} />
              {loading && (
                <div className="mt-6 w-full h-1 bg-chroma-border overflow-hidden rounded-full">
                  <div className="h-full bg-chroma-primary animate-pulse-ring w-2/3 rounded-full" />
                </div>
              )}
              <div className="mt-6 flex justify-center">
                <button
                  onClick={handleSampleClick}
                  disabled={loading}
                  className="text-sm text-chroma-muted-fg hover:text-chroma-fg transition-colors cursor-pointer disabled:opacity-50 border-b border-transparent hover:border-chroma-fg pb-px"
                >
                  Try sample data instead
                </button>
              </div>
            </div>
          </div>
        )}

        {currentStep > 0 && stepper}

        {/* ── Horizontal 5-Column Dashboard ── */}
        {currentStep > 0 && (
          <div className="grid grid-cols-1 xl:grid-cols-5 gap-4 flex-1 items-start">
            
            {/* Column 1: Preprocess */}
            {currentStep >= 1 && results.preprocess && (
              <div className="flex flex-col gap-3 animate-fade-in">
                <div className="flex items-center justify-between px-1">
                  <span className="bento-label">1. Preprocess</span>
                  <span className="text-xs text-chroma-success font-medium">Complete</span>
                </div>
                <ChartCard
                  title="Flux"
                  series={[
                    {
                      name: "Raw",
                      x: results.preprocess.cleaned_flux_chart_data.raw_time,
                      y: results.preprocess.cleaned_flux_chart_data.raw_flux,
                      color: "#d4d4d4",
                      dots: true,
                    },
                    {
                      name: "Cleaned",
                      x: results.preprocess.cleaned_flux_chart_data.cleaned_time,
                      y: results.preprocess.cleaned_flux_chart_data.cleaned_flux,
                      color: "#141414",
                      dots: true,
                    },
                  ]}
                  xLabel="Time"
                  yLabel="Flux"
                />
                <div className="grid grid-cols-2 gap-3">
                  <MetricCard label="Raw Pts" value={results.preprocess.stats.n_points_raw?.toLocaleString()} />
                  <MetricCard label="Clean Pts" value={results.preprocess.stats.n_points?.toLocaleString()} />
                </div>
                {currentStep === 1 && (
                  <button
                    onClick={handleRunTLS}
                    disabled={loading}
                    className="w-full bg-chroma-primary text-chroma-primary-fg py-2.5 text-sm font-medium hover:opacity-90 rounded-md transition-opacity disabled:opacity-50 mt-2"
                  >
                    {loading ? "..." : "Run Transit Search →"}
                  </button>
                )}
              </div>
            )}

            {/* Column 2: Transit Search */}
            {currentStep >= 2 && results.tls && (
              <div className="flex flex-col gap-3 animate-fade-in">
                <div className="flex items-center justify-between px-1">
                  <span className="bento-label">2. Transit Search</span>
                  <span className="text-xs text-chroma-success font-medium">Complete</span>
                </div>
                <div className="grid grid-cols-2 gap-3">
                  <MetricCard label="Period" value={results.tls.period.toFixed(4)} unit="d" />
                  <MetricCard label="Depth" value={results.tls.depth.toFixed(1)} unit="ppm" />
                  <MetricCard label="SNR" value={results.tls.snr.toFixed(1)} />
                  <MetricCard label="SDE" value={results.tls.sde.toFixed(1)} />
                </div>
                <ChartCard
                  title="Phase Fold"
                  series={[
                    {
                      name: "Data",
                      x: results.tls.phase_fold_chart_data.phase,
                      y: results.tls.phase_fold_chart_data.flux,
                      color: "#141414",
                      dots: true,
                    },
                    {
                      name: "Model",
                      x: results.tls.phase_fold_chart_data.phase,
                      y: results.tls.phase_fold_chart_data.model,
                      color: "#ef4444",
                    },
                  ]}
                  xLabel="Phase"
                  yLabel="Flux"
                />
                {currentStep === 2 && (
                  <button
                    onClick={handleRunFeatures}
                    disabled={loading}
                    className="w-full bg-chroma-primary text-chroma-primary-fg py-2.5 text-sm font-medium hover:opacity-90 rounded-md transition-opacity disabled:opacity-50 mt-2"
                  >
                    {loading ? "..." : "Extract Features →"}
                  </button>
                )}
              </div>
            )}

            {/* Column 3: Features */}
            {currentStep >= 3 && results.features && (
              <div className="flex flex-col gap-3 animate-fade-in">
                <div className="flex items-center justify-between px-1">
                  <span className="bento-label">3. Features</span>
                  <span className="text-xs text-chroma-success font-medium">Complete</span>
                </div>
                <MetricCard label="Physics [0]" value={results.features.features.physics[0].toFixed(4)} />
                <MetricCard label="Physics [1]" value={results.features.features.physics[1].toFixed(6)} />
                <MetricCard label="Stats [0]" value={results.features.features.stats[0].toFixed(4)} />
                <MetricCard label="Stats [2]" value={results.features.features.stats[2].toFixed(6)} />
                <MetricCard label="Diagnostics [0]" value={results.features.features.diagnostics[0].toFixed(6)} />
                <MetricCard label="Diagnostics [1]" value={results.features.features.diagnostics[1].toFixed(6)} />
                {currentStep === 3 && (
                  <button
                    onClick={handleRunClassify}
                    disabled={loading}
                    className="w-full bg-chroma-primary text-chroma-primary-fg py-2.5 text-sm font-medium hover:opacity-90 rounded-md transition-opacity disabled:opacity-50 mt-2"
                  >
                    {loading ? "..." : "Classify Signal →"}
                  </button>
                )}
              </div>
            )}

            {/* Column 4: Classify */}
            {currentStep >= 4 && results.classify && (
              <div className="flex flex-col gap-3 animate-fade-in">
                <div className="flex items-center justify-between px-1">
                  <span className="bento-label">4. Classification</span>
                  <span className="text-xs text-chroma-success font-medium">Complete</span>
                </div>
                <div className="bento-card py-6 flex flex-col items-center justify-center">
                  <span className="text-xs text-chroma-muted-fg uppercase mb-2">Verdict</span>
                  <VerdictBadge verdict={results.classify.verdict} />
                  <span className="text-xs text-chroma-fg mt-2">{(results.classify.confidence * 100).toFixed(1)}%</span>
                </div>
                <ChartCard
                  title="Probabilities"
                  series={[{
                    name: "Prob",
                    x: Object.keys(results.classify.class_probs),
                    y: Object.values(results.classify.class_probs) as number[],
                    color: "#4ade80",
                  }]}
                  xLabel="Class"
                  yLabel="Prob"
                />
                {currentStep === 4 && (
                  <button
                    onClick={handleRunParameters}
                    disabled={loading}
                    className="w-full bg-chroma-primary text-chroma-primary-fg py-2.5 text-sm font-medium hover:opacity-90 rounded-md transition-opacity disabled:opacity-50 mt-2"
                  >
                    {loading ? "..." : "Estimate Params →"}
                  </button>
                )}
              </div>
            )}

            {/* Column 5: Parameters */}
            {currentStep >= 5 && results.params && (
              <div className="flex flex-col gap-3 animate-fade-in">
                <div className="flex items-center justify-between px-1">
                  <span className="bento-label">5. Parameters</span>
                  <span className="text-xs text-chroma-success font-medium">Complete</span>
                </div>
                <MetricCard label="Radius" value={results.params.planet_radius_rearth.toFixed(2)} unit="R⊕" />
                <MetricCard label="Distance" value={results.params.orbital_distance.toFixed(4)} unit="AU" />
                <MetricCard label="Eq Temp" value={results.params.equilibrium_temperature} unit="K" />
                <div className="bento-card py-6 flex flex-col items-center justify-center">
                  <span className="text-xs text-chroma-muted-fg uppercase mb-2">Type</span>
                  <span className="text-sm font-semibold text-chroma-fg text-center">
                    {results.params.planet_radius_rearth < 1.25 ? "Earth-sized"
                    : results.params.planet_radius_rearth < 2.0 ? "Super-Earth"
                    : results.params.planet_radius_rearth < 4.0 ? "Sub-Neptune"
                    : results.params.planet_radius_rearth < 8.0 ? "Neptune-sized"
                    : results.params.planet_radius_rearth < 12.0 ? "Sub-Jupiter"
                    : "Jupiter-sized"}
                  </span>
                </div>
                {currentStep === 5 && (
                  <button
                    onClick={handleRunOutput}
                    disabled={loading}
                    className="w-full bg-chroma-primary text-chroma-primary-fg py-2.5 text-sm font-medium hover:opacity-90 rounded-md transition-opacity disabled:opacity-50 mt-2"
                  >
                    {loading ? "..." : "Finalize Report →"}
                  </button>
                )}
                {currentStep === 6 && (
                  <button
                    onClick={handleDownload}
                    className="w-full bg-chroma-fg text-white py-2.5 text-sm font-medium hover:opacity-90 rounded-md transition-opacity mt-2 flex items-center justify-center gap-2"
                  >
                    <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3"/></svg>
                    Download .zip
                  </button>
                )}
                {currentStep === 6 && (
                  <button
                    onClick={handleReset}
                    className="w-full border border-chroma-border py-2.5 text-sm font-medium hover:bg-chroma-muted rounded-md transition-colors"
                  >
                    Analyze New File
                  </button>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Error Display ── */}
        {error && currentStep === 0 && (
          <div className="mt-8 w-full max-w-3xl mx-auto">
            <div className="bento-card border border-chroma-error/20 flex flex-col items-center py-10 bg-chroma-error/5">
              <p className="text-sm text-chroma-error mb-6 font-medium">{error}</p>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleReset}
                  className="text-sm text-chroma-muted-fg hover:text-chroma-fg transition-colors cursor-pointer border-b border-transparent hover:border-chroma-fg pb-px"
                >
                  Start over
                </button>
                <button
                  onClick={handleSampleClick}
                  className="bg-chroma-primary text-chroma-primary-fg px-4 py-2 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer rounded-md"
                >
                  Try sample data
                </button>
              </div>
            </div>
          </div>
        )}
      </main>

      <footer className="mt-auto py-6 border-t border-chroma-border flex items-center justify-between px-6 bg-white">
        <span className="text-sm text-chroma-muted-fg font-medium">ExoVetter</span>
        <span className="text-xs text-chroma-muted-fg">BAH 2026 — Challenge 7</span>
      </footer>

      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}
