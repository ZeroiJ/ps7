"use client";

import type { PipelineResult } from "@/lib/types";
import VerdictBadge from "./VerdictBadge";
import MetricCard from "./MetricCard";
import ChartCard from "./ChartCard";
import { downloadResults } from "@/lib/api";
import { useAppStore } from "@/lib/store";

interface ResultsDashboardProps {
  result: PipelineResult;
}

export default function ResultsDashboard({ result }: ResultsDashboardProps) {
  const uploadResponse = useAppStore((s) => s.uploadResponse);

  const { tls_result, classification, plots } = result;

  const rawFluxData: Plotly.Data[] = [
    {
      x: plots.raw_flux.time,
      y: plots.raw_flux.flux,
      type: "scattergl",
      mode: "markers",
      marker: { color: "#d4d4d4", size: 2 },
      name: "Raw",
    },
    {
      x: plots.cleaned_flux.time,
      y: plots.cleaned_flux.flux,
      type: "scattergl",
      mode: "markers",
      marker: { color: "#141414", size: 2 },
      name: "Cleaned",
    },
  ];

  const periodogramData: Plotly.Data[] = [
    {
      x: plots.periodogram.frequency,
      y: plots.periodogram.power,
      type: "scatter",
      mode: "lines",
      line: { color: "#141414", width: 1 },
    },
  ];

  const foldedData: Plotly.Data[] = [
    {
      x: plots.folded_curve.phase,
      y: plots.folded_curve.flux,
      type: "scattergl",
      mode: "markers",
      marker: { color: "#141414", size: 2 },
      name: "Data",
    },
    {
      x: plots.folded_curve.phase,
      y: plots.folded_curve.model,
      type: "scatter",
      mode: "lines",
      line: { color: "#ef4444", width: 2 },
      name: "Model",
    },
  ];

  const classBarData: Plotly.Data[] = [
    {
      x: plots.classification_bars.classes,
      y: plots.classification_bars.probabilities,
      type: "bar",
      marker: {
        color: plots.classification_bars.classes.map((c) => {
          if (c === "planet") return "#4ade80";
          if (c === "fp") return "#ef4444";
          return "#7b7b7b";
        }),
      },
    },
  ];

  const handleDownload = async () => {
    if (uploadResponse?.job_id) {
      try {
        await downloadResults(uploadResponse.job_id);
      } catch {
        // Toast will handle error
      }
    }
  };

  return (
    <div className="w-full max-w-5xl mx-auto px-6 py-12">
      {/* Verdict */}
      <div className="flex justify-center mb-8">
        <VerdictBadge verdict={classification.predicted_class} />
      </div>

      {/* Target name */}
      {result.target_name && (
        <h2 className="text-center text-lg font-medium text-chroma-fg mb-8">
          {result.target_name}
        </h2>
      )}

      {/* Metric cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4 mb-8">
        <MetricCard
          label="Period"
          value={tls_result.period.toFixed(4)}
          unit="days"
        />
        <MetricCard
          label="Depth"
          value={tls_result.depth.toFixed(1)}
          unit="ppm"
        />
        <MetricCard
          label="Duration"
          value={tls_result.duration.toFixed(1)}
          unit="hrs"
        />
        <MetricCard label="SNR" value={tls_result.snr.toFixed(1)} />
        <MetricCard label="SDE" value={tls_result.sde.toFixed(1)} />
        <MetricCard
          label="Confidence"
          value={(classification.confidence * 100).toFixed(1)}
          unit="%"
        />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <ChartCard
          title="Raw vs Cleaned Flux"
          data={rawFluxData}
          layout={{
            xaxis: { title: { text: "Time (BTJD)" } },
            yaxis: { title: { text: "Flux" } },
            showlegend: true,
            legend: { x: 0, y: 1, font: { size: 10 } },
          }}
        />
        <ChartCard
          title="Periodogram"
          data={periodogramData}
          layout={{
            xaxis: { title: { text: "Frequency (1/d)" } },
            yaxis: { title: { text: "Power" } },
          }}
        />
        <ChartCard
          title="Phase-Folded Light Curve"
          data={foldedData}
          layout={{
            xaxis: { title: { text: "Phase" } },
            yaxis: { title: { text: "Flux" } },
            showlegend: true,
            legend: { x: 0, y: 1, font: { size: 10 } },
          }}
        />
        <ChartCard
          title="Classification Probabilities"
          data={classBarData}
          layout={{
            xaxis: { title: { text: "Class" } },
            yaxis: { title: { text: "Probability" }, range: [0, 1] },
          }}
        />
      </div>

      {/* Download bar */}
      <div className="flex justify-center pt-6 border-t border-chroma-border">
        <button
          onClick={handleDownload}
          className="bg-chroma-primary text-chroma-primary-fg rounded-lg px-6 py-2.5 text-sm font-medium hover:opacity-90 transition-opacity cursor-pointer"
        >
          Download All Results
        </button>
      </div>
    </div>
  );
}
