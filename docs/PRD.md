# Product Requirements Document — Data Upload & Analysis Web App

> **Style Reference**: Chroma (trychroma.com) — ultra-minimalist, typography-forward, black & white with grays

---

## 1. Product Overview

### 1.1 Vision
A single-page web application where users upload data files (CSV, JSON, NPZ) and instantly receive processed results — transit detection analysis, feature extraction, and classification output — visualized through clean, interactive charts and cards.

### 1.2 Target Users
Data science students, hackathon teams, researchers. Specifically the ISRO BAH Challenge 7 team for demo purposes, but designed generically enough to accept any columnar data.

### 1.3 Core Value Proposition
"Upload data → Get results. No sign-up, no config, no tutorials."

---

## 2. User Flow

```
Landing Page
    │
    ├── [Hero Section] One-liner + CTA button
    │
    ├── [Upload Zone] Drag-and-drop or click to upload
    │     │
    │     ├── Supported: .csv, .json, .npz
    │     ├── File size limit: 200 MB
    │     └── Visual preview of first 5 rows after upload
    │
    ├── [Processing] Animated progress bar with step labels
    │     ├── Step 1/5: Loading & Validating
    │     ├── Step 2/5: Cleaning & Normalizing
    │     ├── Step 3/5: Running Analysis
    │     ├── Step 4/5: Extracting Features
    │     └── Step 5/5: Generating Results
    │
    ├── [Results Dashboard]
    │     ├── Summary Card (key metrics in bold)
    │     ├── Chart 1: Raw vs Cleaned overlay
    │     ├── Chart 2: Periodogram / Power spectrum
    │     ├── Chart 3: Folded light curve
    │     ├── Chart 4: Classification confidence bars
    │     ├── Download all results as .zip button
    │     └── Export individual charts as PNG
    │
    └── [Footer] Minimal — logo + "Built for BAH 2026"
```

---

## 3. Feature Requirements

### P0 (Must Have)
| ID | Feature | Acceptance Criteria |
|----|---------|-------------------|
| F1 | Drag-and-drop file upload | User can drag a .csv/.json/.npz onto a dashed zone; file appears with name + size + type |
| F2 | Automatic CSV parsing | Detects delimiter, header row, column types. Shows first 5 rows as preview table |
| F3 | NPZ file support | Reads `.npz` files, lists available array keys, lets user pick time & flux columns |
| F4 | Processing pipeline | Runs the 6-step exoplanet pipeline automatically after upload |
| F5 | Results display | Shows classification verdict (Planet/EB/Blend/FP), confidence, key metrics |
| F6 | Charts | Shows at least 3 visualization plots (cleaned curve, periodogram, folded transit) |
| F7 | Download results | "Download All" button that zips output charts + metrics JSON |

### P1 (Should Have)
| ID | Feature | Acceptance Criteria |
|----|---------|-------------------|
| F8 | Sample data button | "Try with sample data" loads a pre-packaged TOI light curve |
| F9 | Dark mode toggle | Switches color scheme; respects system preference |
| F10 | Custom column mapping | User can map which column is time, which is flux |
| F11 | Result comparison | Side-by-side comparison of two uploaded files |
| F12 | Error recovery | Invalid file format shows clear error message + suggestion |

### P2 (Nice to Have)
| ID | Feature | Acceptance Criteria |
|----|---------|-------------------|
| F13 | Session history | Results persist in localStorage; user can revisit last 5 analyses |
| F14 | Share link | Generates a shareable URL with base64-encoded results |
| F15 | Batch upload | Upload multiple files; process in queue; compare results table |

---

## 4. Page Structure

### 4.1 Navigation Bar
- Logo (wordmark) on left
- **No navigation links** (single-page app)
- Theme toggle (light/dark) on right, minimal icon
- Fixed top, 73px height, transparent bg, 1px bottom border

### 4.2 Hero Section
- One-line heading: "Upload. Analyze. Discover."
- Subtitle: "Drop a light curve and get instant transit analysis — no sign-up required."
- Two CTA buttons: "Upload your data" (primary, black bg) and "Try sample" (secondary, outline)
- Below: stat strip with 3 metrics (supported formats, max file size, processing time)

### 4.3 Upload Zone
- Dashed border container, centered
- Shows file icon (SVG) + "Drop your file here" text
- After upload: file name, size, type badge, row count appear
- Preview table (first 5 rows, scrollable)
- Column mapping UI if NPZ (dropdown for time/flux keys)

### 4.4 Processing Indicator
- Stepped progress bar (5 steps)
- Each step lights up with checkmark when complete
- Total elapsed time shown
- If processing takes >5s, show a subtle "This may take a moment" message

### 4.5 Results Section
- **Header**: Verdict badge (green "PLANET CONFIRMED" / yellow "CANDIDATE" / red "FALSE POSITIVE")
- **Key Metrics Row**: 4 metric cards in a row (Period, Depth, SNR, Confidence)
- **Chart Grid**: 2×2 grid of interactive Plotly charts
  - Top-left: Raw vs detrended flux overlay
  - Top-right: Periodogram (TLS power spectrum)
  - Bottom-left: Folded light curve with transit model
  - Bottom-right: Classification probability bars
- **Download Bar**: "Download All Results" button + "Export Chart" per chart

### 4.6 Footer
- Logo + "BAH 2026 — Challenge 7" text
- Thin separator line
- Small copyright text

---

## 5. Design Principles

1. **Zero friction to start** — No login, no config, upload and go
2. **Beautiful defaults** — Charts look publication-ready without user tweaking
3. **Progressive disclosure** — Show summary first, details on hover/click
4. **Every number has context** — No bare metrics without a tooltip or label explaining what they mean

---

## 6. Error States

| Scenario | Handling |
|----------|----------|
| Wrong file type | Show red toast: "Unsupported format. Accepted: CSV, JSON, NPZ" |
| File too large | Show red toast: "File over 200 MB limit" |
| Corrupt CSV | Show alert: "Could not parse. Check your file is valid CSV" |
| Pipeline crash | Show alert with error message + "Try sample data" fallback button |
| No results (empty file) | Show "No analyzable data found in file" |
