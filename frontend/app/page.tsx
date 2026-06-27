"use client";

import { useCallback, useRef, useState } from "react";
import { stepUpload, stepRunTLS, stepRunClassify, getSampleData, downloadResults } from "@/lib/api";

import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import UploadZone from "./components/UploadZone";
import ChartCard from "./components/ChartCard";
import MetricCard from "./components/MetricCard";
import VerdictBadge from "./components/VerdictBadge";
import Footer from "./components/Footer";
import Toast from "./components/Toast";

export default function Home() {
  const uploadRef = useRef<HTMLDivElement>(null);
  const [toast, setToast] = useState<{ message: string; type: "error" | "success" | "info" } | null>(null);

  const [sessionId, setSessionId] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0); // 0=upload, 1=preprocess, 2=tls, 3=classify
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

  const scrollTo = useCallback((ref: React.RefObject<HTMLDivElement | null>) => {
    setTimeout(() => {
      ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }, []);

  const showError = useCallback((msg: string) => {
    setError(msg);
    setToast({ message: msg, type: "error" });
  }, []);

  const handleUploadClick = useCallback(() => {
    scrollTo(uploadRef);
  }, [scrollTo]);

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
      scrollTo(uploadRef);
      setToast({ message: "Sample data loaded", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "Failed to load sample data");
    } finally {
      setLoading(false);
    }
  }, [showError, scrollTo]);

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

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />
      <main className="flex-1 pt-[73px]">
        <Hero onUploadClick={handleUploadClick} onSampleClick={handleSampleClick} />

        {/* Stepper UI Progress indicator */}
        {currentStep > 0 && (
          <div className="w-full max-w-4xl mx-auto px-6 py-8">
            <div className="flex items-center justify-between relative">
              <div className="absolute left-0 top-1/2 -translate-y-1/2 w-full h-1 bg-chroma-muted -z-10" />
              <div 
                className="absolute left-0 top-1/2 -translate-y-1/2 h-1 bg-chroma-primary -z-10 transition-all duration-500"
                style={{ width: `${((currentStep) / 3) * 100}%` }}
              />
              {["Upload", "Preprocess", "Transit Search", "Verify"].map((label, idx) => (
                <div key={label} className="flex flex-col items-center">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-bold border-2 ${
                    currentStep >= idx ? "bg-chroma-primary border-chroma-primary text-white" : "bg-white border-chroma-muted text-chroma-muted-fg"
                  }`}>
                    {currentStep > idx ? "✓" : idx + 1}
                  </div>
                  <span className={`text-xs mt-2 font-medium ${currentStep >= idx ? "text-chroma-fg" : "text-chroma-muted-fg"}`}>
                    {label}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Step 0: Upload Zone */}
        {currentStep === 0 && (
          <div ref={uploadRef}>
            <UploadZone onFileAccepted={handleFileAccepted} />
            {loading && (
              <div className="w-full max-w-3xl mx-auto px-6 mt-6">
                <div className="w-full h-1 bg-chroma-muted rounded-full overflow-hidden">
                  <div className="h-full bg-chroma-primary rounded-full animate-pulse-ring w-2/3" />
                </div>
                <p className="text-xs text-chroma-muted-fg mt-2 text-center">Uploading & Preprocessing...</p>
              </div>
            )}
          </div>
        )}

        {/* Step 1: Preprocessing Results */}
        {currentStep >= 1 && results.preprocess && (
          <div className="w-full max-w-5xl mx-auto px-6 py-6" ref={currentStep === 1 ? uploadRef : null}>
            <div className="rounded-lg border border-chroma-border bg-white p-6 shadow-sm mb-6">
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-chroma-border">
                <h3 className="text-lg font-medium">Step 1/3: Data Preprocessing</h3>
                <span className="text-green-600 font-medium text-sm flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  Complete
                </span>
              </div>
              
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="p-4 rounded-md bg-chroma-muted">
                  <p className="text-xs text-chroma-muted-fg uppercase mb-1">Raw points</p>
                  <p className="text-xl font-medium">{results.preprocess.stats.n_points_raw.toLocaleString()}</p>
                </div>
                <div className="p-4 rounded-md bg-chroma-muted">
                  <p className="text-xs text-chroma-muted-fg uppercase mb-1">Outliers removed</p>
                  <p className="text-xl font-medium">{results.preprocess.stats.outliers_removed.toLocaleString()}</p>
                </div>
                <div className="p-4 rounded-md bg-chroma-muted">
                  <p className="text-xs text-chroma-muted-fg uppercase mb-1">Cleaned points</p>
                  <p className="text-xl font-medium">{results.preprocess.stats.n_points.toLocaleString()}</p>
                </div>
              </div>

              <div className="mb-6">
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
                    }
                  ]}
                  layout={{
                    xaxis: { title: { text: "Time (BTJD)" } },
                    yaxis: { title: { text: "Flux" } },
                    showlegend: true,
                    legend: { x: 0, y: 1, font: { size: 10 } },
                  }}
                />
              </div>

              {currentStep === 1 && (
                <div className="flex justify-center mt-6">
                  <button
                    onClick={handleRunTLS}
                    disabled={loading}
                    className="bg-chroma-primary text-chroma-primary-fg rounded-lg px-6 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-50"
                  >
                    {loading ? "Processing..." : "Continue to Transit Search"}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 2: TLS Results */}
        {currentStep >= 2 && results.tls && (
          <div className="w-full max-w-5xl mx-auto px-6 py-6">
            <div className="rounded-lg border border-chroma-border bg-white p-6 shadow-sm mb-6">
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-chroma-border">
                <h3 className="text-lg font-medium">Step 2/3: Transit Search</h3>
                <span className="text-green-600 font-medium text-sm flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  Complete
                </span>
              </div>
              
              <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
                <MetricCard label="Period" value={results.tls.period.toFixed(4)} unit="days" />
                <MetricCard label="Depth" value={results.tls.depth.toFixed(1)} unit="ppm" />
                <MetricCard label="Duration" value={results.tls.duration.toFixed(1)} unit="hrs" />
                <MetricCard label="SNR" value={results.tls.snr.toFixed(1)} />
                <MetricCard label="SDE" value={results.tls.sde.toFixed(1)} />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
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
                    }
                  ]}
                  layout={{
                    xaxis: { title: { text: "Phase" } },
                    yaxis: { title: { text: "Flux" } },
                    showlegend: true,
                    legend: { x: 0, y: 1, font: { size: 10 } },
                  }}
                />
              </div>

              {currentStep === 2 && (
                <div className="flex justify-center mt-6">
                  <button
                    onClick={handleRunClassify}
                    disabled={loading}
                    className="bg-chroma-primary text-chroma-primary-fg rounded-lg px-6 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer disabled:opacity-50"
                  >
                    {loading ? "Processing..." : "Continue to Classification"}
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Step 3: Classify Results */}
        {currentStep === 3 && results.classify && (
          <div className="w-full max-w-5xl mx-auto px-6 py-6 pb-16">
            <div className="rounded-lg border border-chroma-border bg-white p-6 shadow-sm mb-6">
              <div className="flex justify-between items-center mb-6 pb-4 border-b border-chroma-border">
                <h3 className="text-lg font-medium">Step 3/3: Classification</h3>
                <span className="text-green-600 font-medium text-sm flex items-center gap-1">
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" /></svg>
                  Complete
                </span>
              </div>
              
              <div className="flex flex-col items-center justify-center mb-8">
                <p className="text-sm text-chroma-muted-fg uppercase tracking-wider mb-3">Final Verdict</p>
                <VerdictBadge verdict={results.classify.verdict} />
                <p className="text-sm text-chroma-fg mt-3">Confidence: {(results.classify.confidence * 100).toFixed(1)}%</p>
              </div>

              <div className="max-w-2xl mx-auto mb-8">
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
                        return "#7b7b7b";
                      }),
                    },
                  }]}
                  layout={{
                    xaxis: { title: { text: "Class" } },
                    yaxis: { title: { text: "Probability" }, range: [0, 1] },
                  }}
                />
              </div>

              <div className="flex items-center justify-center gap-4 mt-8 pt-6 border-t border-chroma-border">
                <button
                  onClick={handleDownload}
                  className="bg-chroma-primary text-chroma-primary-fg rounded-lg px-6 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
                >
                  Download All Results
                </button>
                <button
                  onClick={handleReset}
                  className="border border-chroma-border rounded-lg px-6 py-2.5 text-sm font-medium hover:bg-chroma-muted transition-colors cursor-pointer"
                >
                  Analyze Another File
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Global Error Display */}
        {error && currentStep === 0 && (
          <div className="w-full max-w-3xl mx-auto px-6 py-12 text-center">
            <div className="rounded-lg border border-chroma-error/30 bg-chroma-error/5 p-8">
              <p className="text-sm text-chroma-fg mb-4">{error}</p>
              <div className="flex items-center justify-center gap-3">
                <button
                  onClick={handleReset}
                  className="border border-chroma-border rounded-lg px-4 py-2 text-sm font-medium hover:bg-chroma-muted transition-colors cursor-pointer"
                >
                  Start over
                </button>
                <button
                  onClick={handleSampleClick}
                  className="bg-chroma-primary text-chroma-primary-fg rounded-lg px-4 py-2 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
                >
                  Try sample data
                </button>
              </div>
            </div>
          </div>
        )}
      </main>
      <Footer />
      {toast && <Toast message={toast.message} type={toast.type} onClose={() => setToast(null)} />}
    </div>
  );
}
