"use client";

interface MetricCardProps {
  label: string;
  value: string | number;
  unit?: string;
}

export default function MetricCard({ label, value, unit }: MetricCardProps) {
  return (
    <div className="bento-card flex flex-col items-center justify-center text-center py-5">
      <span className="text-xl font-semibold tracking-tight font-mono text-chroma-fg">
        {typeof value === "number" ? value.toLocaleString() : value}
        {unit && (
          <span className="text-sm font-normal text-chroma-muted-fg ml-1">
            {unit}
          </span>
        )}
      </span>
      <span className="text-xs text-chroma-muted-fg mt-1.5 uppercase tracking-wider">
        {label}
      </span>
    </div>
  );
}
