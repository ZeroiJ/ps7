export interface UploadResponse {
  job_id: string;
  filename: string;
  rows: number;
  columns: string[];
  preview: Record<string, unknown>[];
  message: string;
}

// ── New Step Types (6-step pipeline) ──

export interface FeaturesData {
  physics: number[];   // [period, depth, duration, snr, sde]
  stats: number[];     // [skewness, kurtosis, std, mad]
  diagnostics: number[]; // [odd_even_diff, secondary_eclipse_depth]
}

export interface FeaturesResponse {
  session_id: string;
  step: 3;
  features: FeaturesData;
}

export interface ClassificationResponse {
  session_id: string;
  step: 4;
  verdict: string;
  confidence: number;
  class_probs: Record<string, number>;
}

export interface ParametersResponse {
  session_id: string;
  step: 5;
  planet_radius_rearth: number;
  orbital_distance: number;
  equilibrium_temperature: number;
  orbital_period_days: number;
  transit_depth_pct: number;
  transit_duration_hours: number;
}

export interface TLSResult {
  period: number;
  sde: number;
  depth: number;
  duration: number;
  snr: number;
  t0?: number;
}

export interface ClassificationResult {
  predicted_class: string;
  confidence: number;
  class_probs: Record<string, number>;
}

export interface PreprocessedData {
  n_points: number;
  n_points_raw?: number;
  time_span: number;
  flux_median?: number;
  flux_std?: number;
  flux_range?: [number, number];
  outliers_removed?: number;
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
  parameters: {
    planet_radius_rearth: number;
    semi_major_axis_au: number;
    equilibrium_temp_k: number;
    orbital_period_days: number;
    transit_depth_ppm: number;
    duration_hrs: number;
  };
  plots: PlotData;
}

export interface OutputResponse {
  session_id: string;
  step: 6;
  target_name: string;
  preprocessed: PreprocessedData;
  tls_result: TLSResult;
  features: { physics: number[]; stats: number[]; diagnostics: number[] };
  classification: ClassificationResult;
  parameters: PipelineResult["parameters"];
  plots: PlotData;
}

export type AppState =
  | "idle"
  | "uploading"
  | "previewing"
  | "processing"
  | "results"
  | "error";
