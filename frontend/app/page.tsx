"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useAppStore } from "@/lib/store";
import { uploadFile, processFile, getSampleData, checkStatus } from "@/lib/api";

import Navbar from "./components/Navbar";
import Hero from "./components/Hero";
import UploadZone from "./components/UploadZone";
import PreviewTable from "./components/PreviewTable";
import ProgressStepper from "./components/ProgressStepper";
import ResultsDashboard from "./components/ResultsDashboard";
import Footer from "./components/Footer";
import Toast from "./components/Toast";

const PIPELINE_STEPS = [
  "Upload",
  "Preprocess",
  "TLS Search",
  "Features",
  "Classify",
];

export default function Home() {
  const store = useAppStore();
  const uploadRef = useRef<HTMLDivElement>(null);
  const resultsRef = useRef<HTMLDivElement>(null);
  const [toast, setToast] = useState<{
    message: string;
    type: "error" | "success" | "info";
  } | null>(null);

  const scrollTo = useCallback((ref: React.RefObject<HTMLDivElement | null>) => {
    setTimeout(() => {
      ref.current?.scrollIntoView({ behavior: "smooth", block: "start" });
    }, 100);
  }, []);

  const showError = useCallback(
    (msg: string) => {
      store.setError(msg);
      store.setState("error");
      setToast({ message: msg, type: "error" });
    },
    [store]
  );

  const handleFileAccepted = useCallback(
    async (file: File) => {
      store.setFile(file);
      store.setState("uploading");

      try {
        const response = await uploadFile(file);
        store.setUploadResponse(response);
        store.setState("previewing");
        setToast({
          message: `Uploaded ${response.filename} (${response.rows} rows)`,
          type: "success",
        });
      } catch (err) {
        showError(err instanceof Error ? err.message : "Upload failed");
      }
    },
    [store, showError]
  );

  const handleSampleClick = useCallback(async () => {
    store.setState("uploading");

    try {
      const response = await getSampleData();
      store.setUploadResponse(response);
      store.setState("previewing");
      scrollTo(uploadRef);
      setToast({ message: "Sample data loaded", type: "success" });
    } catch (err) {
      showError(err instanceof Error ? err.message : "Failed to load sample data");
    }
  }, [store, showError, scrollTo]);

  const handleUploadClick = useCallback(() => {
    scrollTo(uploadRef);
  }, [scrollTo]);

  const pollStatus = useCallback(
    async (jobId: string) => {
      const maxAttempts = 60;
      let attempts = 0;

      const poll = async () => {
        if (attempts >= maxAttempts) {
          showError("Processing timed out. Please try again.");
          return;
        }
        attempts++;

        try {
          const status = await checkStatus(jobId);

          if (status.status === "done" && status.result) {
            store.setResult(status.result);
            store.setCurrentStep(PIPELINE_STEPS.length);
            store.setState("results");
            scrollTo(resultsRef);
            setToast({ message: "Analysis complete", type: "success" });
            return;
          }

          if (status.status === "error") {
            showError(status.error || "Processing failed");
            return;
          }

          // Update progress step based on progress percentage
          if (status.progress != null) {
            const step = Math.min(
              Math.floor((status.progress / 100) * PIPELINE_STEPS.length),
              PIPELINE_STEPS.length - 1
            );
            store.setCurrentStep(step);
            store.setProgress(status.progress);
          }

          setTimeout(poll, 2000);
        } catch (err) {
          showError(err instanceof Error ? err.message : "Status check failed");
        }
      };

      await poll();
    },
    [store, showError, scrollTo]
  );

  const handleStartAnalysis = useCallback(async () => {
    if (!store.uploadResponse) return;

    store.setState("processing");
    store.setCurrentStep(0);

    try {
      const response = await processFile(store.uploadResponse.job_id);

      if (response.status === "done" && response.result) {
        store.setResult(response.result);
        store.setCurrentStep(PIPELINE_STEPS.length);
        store.setState("results");
        scrollTo(resultsRef);
        setToast({ message: "Analysis complete", type: "success" });
      } else if (response.status === "processing") {
        store.setCurrentStep(1);
        await pollStatus(store.uploadResponse.job_id);
      } else if (response.status === "error") {
        showError(response.error || "Processing failed");
      }
    } catch (err) {
      showError(err instanceof Error ? err.message : "Processing failed");
    }
  }, [store, showError, scrollTo, pollStatus]);

  const handleReset = useCallback(() => {
    store.reset();
    window.scrollTo({ top: 0, behavior: "smooth" });
  }, [store]);

  return (
    <div className="min-h-screen flex flex-col">
      <Navbar />

      <main className="flex-1 pt-[73px]">
        {/* Hero -- always shown */}
        <Hero
          onUploadClick={handleUploadClick}
          onSampleClick={handleSampleClick}
        />

        {/* Upload zone */}
        {(store.state === "idle" ||
          store.state === "uploading" ||
          store.state === "previewing") && (
          <div ref={uploadRef}>
            <UploadZone onFileAccepted={handleFileAccepted} />

            {/* Preview table */}
            {store.state === "previewing" && store.uploadResponse && (
              <>
                <PreviewTable
                  columns={store.uploadResponse.columns}
                  rows={store.uploadResponse.preview}
                />

                {/* Start Analysis button */}
                <div className="flex justify-center mt-8 mb-12">
                  <button
                    onClick={handleStartAnalysis}
                    className="bg-chroma-primary text-chroma-primary-fg rounded-lg px-6 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
                  >
                    Start Analysis
                  </button>
                </div>
              </>
            )}

            {/* Uploading progress bar */}
            {store.state === "uploading" && (
              <div className="w-full max-w-3xl mx-auto px-6 mt-6">
                <div className="w-full h-1 bg-chroma-muted rounded-full overflow-hidden">
                  <div className="h-full bg-chroma-primary rounded-full animate-pulse-ring w-2/3" />
                </div>
                <p className="text-xs text-chroma-muted-fg mt-2 text-center">
                  Uploading file...
                </p>
              </div>
            )}
          </div>
        )}

        {/* Processing */}
        {store.state === "processing" && (
          <div className="w-full max-w-3xl mx-auto px-6 py-12">
            <ProgressStepper
              currentStep={store.currentStep}
              steps={PIPELINE_STEPS}
            />
          </div>
        )}

        {/* Results */}
        {store.state === "results" && store.result && (
          <div ref={resultsRef}>
            <ResultsDashboard result={store.result} />
            <div className="flex justify-center pb-12">
              <button
                onClick={handleReset}
                className="border border-chroma-border rounded-lg px-4 py-2 text-sm font-medium hover:bg-chroma-muted transition-colors cursor-pointer"
              >
                Analyze another file
              </button>
            </div>
          </div>
        )}

        {/* Error state */}
        {store.state === "error" && (
          <div className="w-full max-w-3xl mx-auto px-6 py-12 text-center">
            <div className="rounded-lg border border-chroma-error/30 bg-chroma-error/5 p-8">
              <p className="text-sm text-chroma-fg mb-4">
                {store.error || "An unexpected error occurred."}
              </p>
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

      {/* Toast */}
      {toast && (
        <Toast
          message={toast.message}
          type={toast.type}
          onClose={() => setToast(null)}
        />
      )}
    </div>
  );
}
