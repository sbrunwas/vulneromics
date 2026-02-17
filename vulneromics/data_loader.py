"""Data loading helpers focused on scalable MERFISH exploration workflows."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pyarrow.dataset as ds
import streamlit as st

from vulneromics.config import (
    DEFAULT_CELL_ID_CANDIDATES,
    DEFAULT_CLASS_COLUMN_CANDIDATES,
    DEFAULT_COORD_COLUMN_CANDIDATES,
    DEFAULT_REGION_COLUMN_CANDIDATES,
)


class DataSchemaError(ValueError):
    """Raised when expected columns are missing from input data."""


class AbcAtlasAccessUnavailableError(ImportError):
    """Raised when abc_atlas_access is not installed."""


def _read_table(path: Path, columns: list[str] | None = None) -> pd.DataFrame:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return pd.read_csv(path, usecols=columns)

    if suffix in {".parquet", ".pq"}:
        table = ds.dataset(path.as_posix(), format="parquet").to_table(columns=columns)
        return table.to_pandas()

    raise ValueError(f"Unsupported file extension for {path}. Expected CSV or Parquet.")


def _pick_first_available(columns: list[str], candidates: tuple[str, ...], label: str) -> str:
    for name in candidates:
        if name in columns:
            return name
    raise DataSchemaError(f"Could not find a {label} column. Tried: {candidates}")


def _pick_coord_columns(columns: list[str]) -> tuple[str, str, str]:
    for triplet in DEFAULT_COORD_COLUMN_CANDIDATES:
        if all(col in columns for col in triplet):
            return triplet
    raise DataSchemaError(
        "Could not find xyz coordinate columns. "
        f"Tried: {DEFAULT_COORD_COLUMN_CANDIDATES}"
    )


@st.cache_data(show_spinner=False)
def get_abc_cache_manifest(cache_dir: str) -> str:
    """Return a simple string representation of the current Allen ABC manifest."""

    try:
        from abc_atlas_access.abc_atlas_cache.abc_project_cache import AbcProjectCache
    except ModuleNotFoundError as exc:
        raise AbcAtlasAccessUnavailableError(
            "`abc_atlas_access` is not installed. Install with:\n"
            "pip install \"abc_atlas_access[notebooks] @ "
            "git+https://github.com/alleninstitute/abc_atlas_access.git\""
        ) from exc

    abc_cache = AbcProjectCache.from_cache_dir(Path(cache_dir))
    return str(abc_cache.current_manifest)


@st.cache_data(show_spinner=False)
def resolve_abc_file_path(cache_dir: str, relative_or_absolute_path: str) -> str:
    """Resolve a dataset path entered by the user against the Allen cache root."""

    candidate = Path(relative_or_absolute_path)
    if candidate.is_absolute() and candidate.exists():
        return candidate.as_posix()

    root = Path(cache_dir)
    resolved = root / candidate
    if resolved.exists():
        return resolved.as_posix()

    raise FileNotFoundError(
        f"Could not resolve '{relative_or_absolute_path}' inside cache dir '{cache_dir}'."
    )


@st.cache_data(show_spinner=False)
def peek_columns(path: str) -> list[str]:
    p = Path(path)
    if p.suffix.lower() == ".csv":
        return list(pd.read_csv(p, nrows=1).columns)

    if p.suffix.lower() in {".parquet", ".pq"}:
        return ds.dataset(p.as_posix(), format="parquet").schema.names

    raise ValueError(f"Unsupported file extension for {path}. Expected CSV or Parquet.")


@st.cache_data(show_spinner="Loading metadata...")
def load_metadata(path: str) -> pd.DataFrame:
    p = Path(path)
    columns = peek_columns(path)
    cell_id = _pick_first_available(columns, DEFAULT_CELL_ID_CANDIDATES, "cell id")
    region = _pick_first_available(columns, DEFAULT_REGION_COLUMN_CANDIDATES, "region")
    cell_class = _pick_first_available(columns, DEFAULT_CLASS_COLUMN_CANDIDATES, "cell class")
    x_col, y_col, z_col = _pick_coord_columns(columns)

    selected = [cell_id, region, cell_class, x_col, y_col, z_col]
    df = _read_table(p, selected).rename(
        columns={
            cell_id: "cell_id",
            region: "region",
            cell_class: "cell_class",
            x_col: "x",
            y_col: "y",
            z_col: "z",
        }
    )

    return df.dropna(subset=["cell_id", "x", "y", "z"]).copy()


@st.cache_data(show_spinner="Loading expression for selected genes...")
def load_expression_subset(path: str, genes: tuple[str, ...]) -> pd.DataFrame:
    p = Path(path)
    genes = tuple(sorted(set(g for g in genes if g)))
    if not genes:
        return pd.DataFrame(columns=["cell_id"])

    columns = peek_columns(path)

    # Long format: one row per (cell, gene)
    if {"cell_id", "gene", "expression"}.issubset(columns):
        dset = ds.dataset(p.as_posix(), format="parquet" if p.suffix.lower() != ".csv" else "csv")
        expr = dset.to_table(
            columns=["cell_id", "gene", "expression"],
            filter=ds.field("gene").isin(list(genes)),
        ).to_pandas()

        if expr.empty:
            return pd.DataFrame(columns=["cell_id", *genes])

        wide = (
            expr.pivot_table(index="cell_id", columns="gene", values="expression", aggfunc="mean")
            .reset_index()
            .rename_axis(None, axis=1)
        )
        return wide

    # Wide format: one row per cell, one column per gene
    cell_id_col = _pick_first_available(columns, DEFAULT_CELL_ID_CANDIDATES, "cell id")
    available = [g for g in genes if g in columns]
    if not available:
        return pd.DataFrame(columns=["cell_id", *genes])

    selected = [cell_id_col, *available]
    wide = _read_table(p, selected).rename(columns={cell_id_col: "cell_id"})

    missing = [g for g in genes if g not in available]
    for gene in missing:
        wide[gene] = pd.NA

    return wide[["cell_id", *genes]]
