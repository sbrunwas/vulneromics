"""Plotting helpers for spatial and gene-expression views."""

from __future__ import annotations

import pandas as pd


class PlotBackendUnavailableError(ImportError):
    """Raised when an optional plotting backend is unavailable."""


def _px():
    try:
        import plotly.express as px
    except ModuleNotFoundError as exc:
        raise PlotBackendUnavailableError(
            "plotly is not installed. Install with `pip install plotly` for interactive Plotly charts."
        ) from exc
    return px


def scatter_2d(df: pd.DataFrame, color_by: str = "cell_class"):
    px = _px()
    return px.scatter(
        df,
        x="x",
        y="y",
        color=color_by,
        hover_data=["cell_id", "region", "cell_class"],
        opacity=0.6,
        title="2D CCF view (x, y)",
    )


def scatter_3d(df: pd.DataFrame, color_by: str = "cell_class"):
    px = _px()
    return px.scatter_3d(
        df,
        x="x",
        y="y",
        z="z",
        color=color_by,
        hover_data=["cell_id", "region", "cell_class"],
        opacity=0.5,
        title="3D CCF view",
    )


def gene_comparison_bar(summary_df: pd.DataFrame, group_col: str):
    px = _px()
    long_df = summary_df.melt(id_vars=[group_col], var_name="gene", value_name="mean_expression")
    return px.bar(
        long_df,
        x="gene",
        y="mean_expression",
        color=group_col,
        barmode="group",
        title="Mean expression comparison",
    )
