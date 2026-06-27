"use client";

import { useCallback, useRef } from "react";
import {
  LineChart, Line, BarChart, Bar, ComposedChart, Scatter,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from "recharts";

interface ChartSeries {
  name?: string;
  x: (number | string)[];
  y: number[];
  color?: string;
  dots?: boolean;
}

interface ChartCardProps {
  title: string;
  series: ChartSeries[];
  xLabel?: string;
  yLabel?: string;
  showLegend?: boolean;
}

/* eslint-disable @typescript-eslint/no-explicit-any */

function toRecords(series: ChartSeries[]): any[] {
  const maxLen = Math.max(...series.map((s) => s.x.length), 0);
  const records: any[] = [];
  for (let i = 0; i < maxLen; i++) {
    const rec: any = {};
    for (const s of series) {
      const key = s.name || "value";
      rec["x_" + key] = s.x[i] ?? null;
      rec["y_" + key] = s.y[i] ?? null;
    }
    records.push(rec);
  }
  return records;
}

function isNumeric(arr: (number | string)[]): boolean {
  return arr.length > 0 && typeof arr[0] === "number";
}

function DetectChart(series: ChartSeries[]): "line" | "bar" {
  // If any series has x values as strings → bar chart
  for (const s of series) {
    if (s.x.length > 0 && typeof s.x[0] === "string") return "bar";
  }
  return "line";
}

const COLORS = ["#141414", "#ef4444", "#4ade80", "#d4d4d4", "#f59e0b"];

export default function ChartCard({ title, series, xLabel, yLabel, showLegend }: ChartCardProps) {
  const ref = useRef<HTMLDivElement>(null);

  const handleExport = useCallback(async () => {
    const svg = ref.current?.querySelector("svg");
    if (!svg) return;
    const svgData = new XMLSerializer().serializeToString(svg);
    const canvas = document.createElement("canvas");
    const ctx = canvas.getContext("2d");
    const img = new window.Image();
    img.onload = () => {
      canvas.width = img.width * 2;
      canvas.height = img.height * 2;
      ctx!.scale(2, 2);
      ctx!.drawImage(img, 0, 0);
      canvas.toBlob((blob) => {
        if (blob) {
          const url = URL.createObjectURL(blob);
          const a = document.createElement("a");
          a.href = url;
          a.download = title.toLowerCase().replace(/\s+/g, "-") + ".png";
          a.click();
          URL.revokeObjectURL(url);
        }
      });
    };
    img.src = "data:image/svg+xml;base64," + btoa(unescape(encodeURIComponent(svgData)));
  }, [title]);

  const chartType = DetectChart(series);
  const data = toRecords(series);

  const axisProps = {
    tick: { fontSize: 11, fill: "#7b7b7b", fontFamily: "Inter, system-ui, sans-serif" },
    axisLine: { stroke: "#e8e8e8" },
    tickLine: { stroke: "#e8e8e8" },
  };

  const renderChart = () => {
    if (chartType === "bar") {
      return (
        <BarChart data={data}>
          <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
          <XAxis dataKey={"x_" + (series[0]?.name || "value")} {...axisProps} />
          <YAxis {...axisProps} />
          <Tooltip
            contentStyle={{
              fontFamily: "Inter, system-ui, sans-serif",
              fontSize: 12,
              borderRadius: 0,
              border: "1px solid #e8e8e8",
            }}
          />
          {showLegend && <Legend />}
          {series.map((s, i) => (
            <Bar
              key={s.name || i}
              dataKey={"y_" + (s.name || i)}
              fill={s.color || COLORS[i % COLORS.length]}
              radius={0}
            />
          ))}
        </BarChart>
      );
    }

    // Line or composed (scatter + line) chart
    return (
      <ComposedChart data={data}>
        <CartesianGrid strokeDasharray="3 3" stroke="#e8e8e8" />
        <XAxis
          dataKey={"x_" + (series[0]?.name || "value")}
          {...axisProps}
          type={isNumeric(series[0]?.x || []) ? "number" : "category"}
          domain={isNumeric(series[0]?.x || []) ? ["auto", "auto"] : undefined}
        />
        <YAxis {...axisProps} domain={["auto", "auto"]} />
        <Tooltip
          contentStyle={{
            fontFamily: "Inter, system-ui, sans-serif",
            fontSize: 12,
            borderRadius: 0,
            border: "1px solid #e8e8e8",
          }}
        />
        {showLegend && <Legend />}
        {series.map((s, i) => {
          const color = s.color || COLORS[i % COLORS.length];
          const key = "y_" + (s.name || i);
          if (s.dots) {
            return (
              <Scatter
                key={s.name || i}
                dataKey={key}
                fill={color}
                stroke="none"
                name={s.name || ""}
                data={data.map((d) => ({ [key]: d[key] }))}
                shape="circle"
              />
            );
          }
          return (
            <Line
              key={s.name || i}
              dataKey={key}
              stroke={color}
              strokeWidth={s.dots ? 0 : 1.5}
              dot={s.dots ? { r: 2, fill: color } : false}
              name={s.name || ""}
              connectNulls={false}
            />
          );
        })}
      </ComposedChart>
    );
  };

  return (
    <div className="bento-card">
      <div className="flex items-center justify-between mb-4">
        <span className="bento-label">{title}</span>
        <button
          onClick={handleExport}
          className="text-xs text-chroma-muted-fg hover:text-chroma-fg transition-colors cursor-pointer"
        >
          Export PNG
        </button>
      </div>
      <div ref={ref} style={{ width: "100%", height: "280px" }}>
        <ResponsiveContainer width="100%" height="100%">
          {renderChart()}
        </ResponsiveContainer>
      </div>
    </div>
  );
}
