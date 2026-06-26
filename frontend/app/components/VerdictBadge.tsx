"use client";

const verdictConfig: Record<
  string,
  { label: string; bg: string; text: string }
> = {
  planet: {
    label: "Planet Candidate",
    bg: "bg-chroma-success/15",
    text: "text-green-700",
  },
  eb: {
    label: "Eclipsing Binary",
    bg: "bg-chroma-warning/15",
    text: "text-yellow-700",
  },
  eclipsing_binary: {
    label: "Eclipsing Binary",
    bg: "bg-chroma-warning/15",
    text: "text-yellow-700",
  },
  blend: {
    label: "Blend",
    bg: "bg-chroma-warning/15",
    text: "text-yellow-700",
  },
  candidate: {
    label: "Planet Candidate",
    bg: "bg-chroma-success/15",
    text: "text-green-700",
  },
  weak_signal: {
    label: "Weak Signal",
    bg: "bg-chroma-warning/15",
    text: "text-yellow-700",
  },
  fp: {
    label: "False Positive",
    bg: "bg-chroma-error/15",
    text: "text-red-700",
  },
  false_positive: {
    label: "False Positive",
    bg: "bg-chroma-error/15",
    text: "text-red-700",
  },
};

interface VerdictBadgeProps {
  verdict: string;
}

export default function VerdictBadge({ verdict }: VerdictBadgeProps) {
  const config = verdictConfig[verdict?.toLowerCase()] || verdictConfig.fp;

  return (
    <span
      className={`inline-flex items-center px-3 py-1 rounded-full text-sm font-medium ${config.bg} ${config.text}`}
    >
      {config.label}
    </span>
  );
}

