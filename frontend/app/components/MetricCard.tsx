"use client";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
}

export default function MetricCard({ label, value, unit }: MetricCardProps) {
  return (
    <div className="flex flex-col gap-1 p-5 rounded-lg border border-chroma-border bg-white">
      <span className="text-2xl font-semibold text-chroma-fg tracking-tight font-mono">
        {typeof value === "number" ? value.toLocaleString() : value}
        {unit && (
          <span className="text-sm font-normal text-chroma-muted-fg ml-1">
            {unit}
          </span>
        )}
      </span>
      <span className="text-xs text-chroma-muted-fg uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}
