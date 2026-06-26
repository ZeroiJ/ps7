"""Pydantic models for ExoVetter API request/response schemas."""

from pydantic import BaseModel
from typing import Optional, List, Dict, Any


class UploadResponse(BaseModel):
    """Response returned after a successful file upload."""
    job_id: str
    filename: str
    rows: int
    columns: List[str]
    preview: List[Dict[str, Any]]
    message: str


class PlotData(BaseModel):
    """Chart data for the frontend visualizations."""
    raw_flux: Dict[str, List[float]]       # {time: [...], flux: [...]}
    cleaned_flux: Dict[str, List[float]]    # {time: [...], flux: [...]}
    periodogram: Dict[str, List[float]]     # {period: [...], power: [...]}
    folded_curve: Dict[str, List[float]]    # {phase: [...], flux: [...]}
    classification_bars: Dict[str, Any]     # {labels: [...], probs: [...], predicted: str}


class PipelineResult(BaseModel):
    """Full pipeline output for a single target."""
    target_name: str
    preprocessed: Dict[str, Any]
    tls_result: Dict[str, float]
    features: Dict[str, List[float]]
    classification: Dict[str, Any]
    parameters: Dict[str, Any]
    plots: PlotData


class ProcessResponse(BaseModel):
    """Response from the /process endpoint."""
    status: str  # 'done', 'processing', 'error'
    result: Optional[PipelineResult] = None
    error: Optional[str] = None
    progress: Optional[int] = None


class ErrorResponse(BaseModel):
    """Structured error envelope used across all endpoints."""
    error: bool = True
    code: str
    message: str
    suggestion: Optional[str] = None
