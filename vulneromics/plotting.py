"""Plotting helpers for spatial and gene-expression views."""

from __future__ import annotations

import pandas as pd
import plotly.express as px


def scatter_2d(df: pd.DataFrame, color_by: str = "cell_class"):
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
    long_df = summary_df.melt(id_vars=[group_col], var_name="gene", value_name="mean_expression")
    return px.bar(
        long_df,
        x="gene",
        y="mean_expression",
        color=group_col,
        barmode="group",
        title="Mean expression comparison",
    )
