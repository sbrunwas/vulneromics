# vulneromics

vulneromics integrates open datasets—from MERFISH single-cell maps to IBL Neuropixels recordings—to identify molecular and state-dependent signatures of vulnerability in the mouse default mode network, linking gene expression, arousal modulation, and network resilience.

This repository includes a Streamlit dashboard for exploring Allen Institute MERFISH mouse brain data in CCF space.

## App features

- Supports **Allen ABC cache-based loading** via `abc_atlas_access` (recommended for Allen-hosted data workflows).
- Supports direct local CSV/Parquet loading as a fallback.
- Loads metadata (cell id, region, class, CCF xyz) and expression (wide or long format).
- Filters by region, cell class, and per-gene thresholds.
- Visualizes filtered cells in 2D and 3D CCF coordinates (with Streamlit fallback charts when Plotly is unavailable).
- Compares grouped mean expression (region/class), including adrenergic/cholinergic receptor panels.

## Repository structure

```text
.
├── app.py                  # Streamlit entrypoint
└── vulneromics/
    ├── config.py           # Defaults (column names, receptor panel)
    ├── data_loader.py      # Cached, column-pruned data loading
    ├── filters.py          # Filtering + grouped summaries
    └── plotting.py         # Plotly plotting helpers
```

## Quickstart (Python 3.11)

```bash
python -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install streamlit pandas numpy pyarrow
pip install "abc_atlas_access[notebooks] @ git+https://github.com/alleninstitute/abc_atlas_access.git"
# optional for interactive 3D/bar charts
pip install plotly
streamlit run app.py
```

## Allen ABC cache usage

The app's **Allen ABC cache** mode is designed around the standard pattern:

```python
from pathlib import Path
from abc_atlas_access.abc_atlas_cache.abc_project_cache import AbcProjectCache

download_base = Path('../../data/abc_atlas')
abc_cache = AbcProjectCache.from_cache_dir(download_base)
abc_cache.current_manifest
```

In the sidebar, provide:
- cache directory (`download_base`)
- metadata file path (relative to cache dir or absolute)
- expression file path (relative to cache dir or absolute)

The app will attempt to resolve those paths against the cache root.


## Deployment troubleshooting

If you still see an old error after updating code (for example, `No module named 'plotly'` or `No module named 'abc_atlas_access'`), your runtime may still be serving an older commit.

- Confirm deployed revision: `git rev-parse --short HEAD`
- Restart the Streamlit process/service after pulling latest changes
- Recreate the virtual environment dependencies if needed

## Scalability notes

- Uses `streamlit` caching for metadata, expression subsets, and manifest lookup.
- Reads only required columns from CSV/Parquet.
- Loads only selected genes from long-format expression files.
- Samples 3D scatter plots to max 30k cells for responsiveness.

## Allen tutorial references

- https://alleninstitute.github.io/abc_atlas_access/notebooks/merfish_tutorial_part_1.html
- https://alleninstitute.github.io/abc_atlas_access/notebooks/merfish_tutorial_part_2a.html
- https://alleninstitute.github.io/abc_atlas_access/notebooks/merfish_tutorial_part_2b.html
- https://alleninstitute.github.io/abc_atlas_access/notebooks/merfish_imputed_genes_example.html
- https://alleninstitute.github.io/abc_atlas_access/notebooks/cluster_groups_and_embeddings_tutorial.html
- https://alleninstitute.github.io/abc_atlas_access/notebooks/cluster_neighborhood_gallery.html
- https://alleninstitute.github.io/abc_atlas_access/notebooks/ccf_and_parcellation_annotation_tutorial.html
- https://alleninstitute.github.io/abc_atlas_access/notebooks/merfish_ccf_registration_tutorial.html
