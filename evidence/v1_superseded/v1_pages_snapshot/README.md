# Keystroke Observatory

> **Interactive dashboard for 136M keystroke typing dynamics analysis**  
> 157,314 sessions · 157K participants · 114.7M keystrokes · Publication-ready

[![PyPI](https://img.shields.io/pypi/v/keystroke-observatory)](https://pypi.org/project/keystroke-observatory/)
[![Python](https://img.shields.io/pypi/pyversions/keystroke-observatory)](https://pypi.org/project/keystroke-observatory/)
[![License](https://img.shields.io/pypi/l/keystroke-observatory)](LICENSE)
[![DOI](https://img.shields.io/badge/DOI-10.5281/zenodo.xxxxxx-blue)](https://doi.org/10.5281/zenodo.xxxxxx)

## Overview

The **Keystroke Observatory** is a research-grade interactive dashboard for exploring typing dynamics from the largest public keystroke dataset (136M keystrokes). It enables scientists to:

- **Explore distributions** of WPM, IKI (inter-key intervals), error rates, hold durations
- **Compare participants** across 157K unique typists
- **Analyze error patterns** with taxonomy (substitution/insertion/deletion/transposition)
- **Inspect individual sessions** with synchronized IKI/hold/error timelines
- **Export publication-ready figures** (SVG/PNG/CSV) for Nature/Science submissions

## Quick Start

### Install from PyPI (recommended)

```bash
pip install keystroke-observatory
keystroke-observatory serve
```

This opens the dashboard at `http://localhost:8080/pages/index.html` in your browser.

### Develop from Source

```bash
git clone https://github.com/limen-research/keystroke-observatory.git
cd keystroke-observatory
npm install
npm run build
keystroke-observatory serve
```

## Dashboard Features

### Global KPIs (Always Visible)
| Metric | Value |
|--------|-------|
| Sessions | 157,314 |
| Participants | 157,314 |
| Total Keystrokes | 114.7M |
| Total Characters | 110.9M |
| Mean WPM | 42.6 |
| Mean Error Rate | 1.4% |
| Mean IKI | 385 ms |

### Interactive Panels

| Panel | Description | Export |
|-------|-------------|--------|
| **Distributions** | Histograms for WPM, IKI, Error Rate, Hold Time | SVG/PNG/CSV |
| **Participant Atlas** | Sortable table with sparklines, 157K rows | CSV |
| **Error Anatomy** | Taxonomy + confusion matrix + positional bias | SVG/PNG |
| **Session Timeline** | Synchronized IKI/Hold/Error trace per session | SVG/PNG |
| **Correlations** | WPM vs Error, IKI vs WPM, Duration vs WPM | SVG/PNG/CSV |

### Linked Brushing
Click any participant → filters all panels to their sessions.  
Brush histogram → highlights matching sessions in atlas.  
All interactions are **reactive and instantaneous** (DuckDB WASM in browser).

## Data Source

The dashboard uses the **Keystroke Dynamics Dataset** (136M keystrokes):
- **Source**: [Original dataset citation]
- **Size**: 163,111 TSV files → 157,314 valid sessions
- **Processing**: Lossless Parquet conversion (16.4 MB, zero nulls)
- **Columns**: 25 metrics per session (WPM, IKI percentiles, error breakdown, letter frequencies, etc.)

## Scientific Context

This dashboard supports the **LIMEN Protocol v1.24** (Nature/NHB-level research):
- **Phase I**: Confirmatory run complete (π_d = 0.2036, 3 hypotheses confirmed)
- **Phase II**: Pre-registration pending — keyboard channel estimation
- **Measurement Model B**: Orthographic noise as structured perturbation
- **Key Question**: Are model errors visible to their own confidence, modulated by orthographic depth?

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Browser (Client)                         │
├─────────────────────────────────────────────────────────────────┤
│  Observable Framework  │  Observable Plot  │  DuckDB WASM      │
│  (Reactive UI)         │  (D3-based viz)   │  (SQL on Parquet) │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Static Files (dist/)                         │
│  index.html + JS bundles + keystroke_session_stats.parquet     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Python CLI (keystroke-observatory)           │
│  pip install keystroke-observatory → serve → open browser      │
└─────────────────────────────────────────────────────────────────┘
```

**Zero server required** — deploys to GitHub Pages, Netlify, Vercel, or any static host.

## Commands

```bash
# Serve locally (opens browser automatically)
keystroke-observatory serve

# Serve on custom port
keystroke-observatory serve --port 3000

# Serve without opening browser
keystroke-observatory serve --no-browser

# Build dashboard from source
keystroke-observatory build

# Open built dashboard directly
keystroke-observatory open
```

## Publication Export

Every chart supports one-click export:
- **SVG** — Vector, publication-ready (Nature/Science)
- **PNG** — Raster, high-DPI
- **CSV** — Raw data for re-analysis

```javascript
// In browser console
Plot.toSVG(chart)    // Returns SVG string
Plot.toPNG(chart)    // Returns blob
Plot.toCSV(data)     // Returns CSV string
```

## Deployment

### GitHub Pages (Free)
```bash
npm run build
# Push dist/ to gh-pages branch
```

### Netlify / Vercel (Free)
```bash
# Connect repository, build command: npm run build, output: dist/
```

### Docker (Self-hosted)
```dockerfile
FROM python:3.11-slim
RUN pip install keystroke-observatory
EXPOSE 8080
CMD ["keystroke-observatory", "serve", "--no-browser"]
```

## Requirements

- **Python**: ≥3.10 (for CLI wrapper only)
- **Node.js**: ≥18 (for building from source)
- **Browser**: Modern (ES2022, WASM, SharedArrayBuffer)

The dashboard runs **entirely in the browser** — no Python runtime needed for viewing.

## Citation

```bibtex
@software{keystroke_observatory_2026,
  title = {Keystroke Observatory: Interactive Dashboard for 136M Keystroke Typing Dynamics},
  author = {LIMEN Research},
  year = {2026},
  version = {1.0.0},
  url = {https://github.com/limen-research/keystroke-observatory},
  doi = {10.5281/zenodo.xxxxxx}
}
```

## License

MIT License — see [LICENSE](LICENSE) for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes (dashboard: `src/`, data: `scripts/`)
4. Run `npm run build` and verify
5. Submit PR with description of scientific motivation

## Related Work

- **LIMEN Protocol v1.24**: Orthographic channels & input noise as structured perturbation
- **Shannon Scaling Law**: Information-theoretic framework for human-LLM interaction noise
- **Phase I Confirmation**: π_d = 0.2036, three hypotheses confirmed

---

**Built for reproducible, publication-grade typing dynamics research.**  
Questions? Open an issue or contact research@limen.org