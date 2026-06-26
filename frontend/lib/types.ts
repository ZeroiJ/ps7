export interface UploadResponse {
  job_id: string;
  filename: string;
  rows: number;
  columns: string[];
  preview: Record<string, unknown>[];
  message: string;
}

export interface TLSResult {
  period: number;
  sde: number;
  depth: number;
  duration: number;
  snr: number;
}

export interface ClassificationResult {
  predicted_class: string;
  confidence: number;
  class_probs: Record<string, number>;
}

export interface PreprocessedData {
  n_points: number;
  time_span: number;
  flux_range: [number, number];
}

export interface PlotData {
  raw_flux: { time: number[]; flux: number[] };
  cleaned_flux: { time: number[]; flux: number[] };
  periodogram: { frequency: number[]; power: number[] };
  folded_curve: { phase: number[]; flux: number[]; model: number[] };
  classification_bars: { classes: string[]; probabilities: number[] };
}

export interface PipelineResult {
  target_name: string;
  preprocessed: PreprocessedData;
  tls_result: TLSResult;
  features: { physics: number[]; stats: number[]; diagnostics: number[] };
  classification: ClassificationResult;
  parameters: { planet_radius_rearth?: number; [key: string]: unknown };
  plots: PlotData;
}

export interface ProcessResponse {
  status: "done" | "processing" | "error";
  result?: PipelineResult;
  error?: string;
  progress?: number;
}

export type AppState =
  | "idle"
  | "uploading"
  | "previewing"
  | "processing"
  | "results"
  | "error";
