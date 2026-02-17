"""Filtering utilities for MERFISH metadata + expression tables."""

from __future__ import annotations

import pandas as pd


def filter_cells(
    df: pd.DataFrame,
    regions: list[str],
    classes: list[str],
    gene_thresholds: dict[str, float],
) -> pd.DataFrame:
    out = df

    if regions:
        out = out[out["region"].isin(regions)]

    if classes:
        out = out[out["cell_class"].isin(classes)]

    for gene, threshold in gene_thresholds.items():
        if gene in out.columns:
            out = out[out[gene].fillna(float("-inf")) >= threshold]

    return out.copy()


def summarize_gene_expression(df: pd.DataFrame, genes: list[str], group_col: str) -> pd.DataFrame:
    keep = [g for g in genes if g in df.columns]
    if not keep:
        return pd.DataFrame()

    return (
        df.groupby(group_col, dropna=False)[keep]
        .mean(numeric_only=True)
        .reset_index()
        .sort_values(group_col)
    )
