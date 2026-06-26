"use client";

import dynamic from "next/dynamic";
import { useCallback, useRef } from "react";

const Plot = dynamic(() => import("react-plotly.js"), { ssr: false });

interface ChartCardProps {
  title: string;
  data: Plotly.Data[];
  layout?: Partial<Plotly.Layout>;
}

export default function ChartCard({ title, data, layout }: ChartCardProps) {
  const plotRef = useRef<HTMLDivElement>(null);

  const handleExport = useCallback(async () => {
    if (!plotRef.current) return;
    const Plotly = await import("plotly.js-dist-min");
    await Plotly.downloadImage(plotRef.current, {
      format: "png",
      width: 1200,
      height: 600,
      filename: title.toLowerCase().replace(/\s+/g, "-"),
    });
  }, [title]);

  const axisDefaults = {
    gridcolor: "#e8e8e8",
    gridwidth: 1,
    zeroline: false,
  };

  const mergedLayout: Partial<Plotly.Layout> = {
    font: { family: "Inter, system-ui, sans-serif", size: 12, color: "#7b7b7b" },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    margin: { t: 8, r: 16, b: 40, l: 56 },
    showlegend: false,
    autosize: true,
    ...layout,
    xaxis: { ...axisDefaults, ...layout?.xaxis },
    yaxis: { ...axisDefaults, ...layout?.yaxis },
  };

  return (
    <div className="rounded-lg border border-chroma-border bg-white p-6 shadow-sm">
      <div className="flex items-center justify-between mb-4">
        <span className="text-xs text-chroma-muted-fg uppercase tracking-wider">
          {title}
        </span>
        <button
          onClick={handleExport}
          className="text-xs text-chroma-muted-fg hover:text-chroma-fg transition-colors cursor-pointer px-2 py-1 rounded border border-chroma-border hover:bg-chroma-muted"
        >
          Export PNG
        </button>
      </div>
      <Plot
        ref={plotRef}
        data={data}
        layout={mergedLayout}
        config={{ responsive: true, displayModeBar: false }}
        useResizeHandler
        style={{ width: "100%", height: "300px" }}
      />
    </div>
  );
}
