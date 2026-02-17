#!/usr/bin/env bash
set -euo pipefail

python -m pip install --upgrade pip
python -m pip install streamlit pandas numpy pyarrow
python -m pip install "abc_atlas_access[notebooks] @ git+https://github.com/alleninstitute/abc_atlas_access.git"
# Optional interactive plotting backend used by the app if available.
python -m pip install plotly
