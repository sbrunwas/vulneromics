from __future__ import annotations

import streamlit as st

from vulneromics.config import DEFAULT_RECEPTOR_PANEL
from vulneromics.data_loader import (
    AbcAtlasAccessUnavailableError,
    DataSchemaError,
    get_abc_cache_manifest,
    load_expression_subset,
    load_metadata,
    resolve_abc_file_path,
)
from vulneromics.filters import filter_cells, summarize_gene_expression
from vulneromics.plotting import (
    PlotBackendUnavailableError,
    gene_comparison_bar,
    scatter_2d,
    scatter_3d,
)

st.set_page_config(page_title="vulneromics MERFISH explorer", layout="wide")
st.title("vulneromics · Allen MERFISH explorer")

st.markdown(
    """
This app is configured for **Allen ABC Atlas access only** via `abc_atlas_access` cache workflows.
"""
)

with st.sidebar:
    st.header("Allen ABC data source")
    cache_dir = st.text_input(
        "ABC cache directory",
        value="../../data/abc_atlas",
        help="Example: AbcProjectCache.from_cache_dir(Path('../../data/abc_atlas')).",
    )

    show_manifest = st.checkbox("Show abc_cache.current_manifest", value=True)
    if show_manifest:
        try:
            st.code(get_abc_cache_manifest(cache_dir))
        except AbcAtlasAccessUnavailableError as exc:
            st.error(str(exc))
            st.stop()
        except Exception as exc:  # noqa: BLE001
            st.warning(f"Unable to read current manifest from cache: {exc}")

    metadata_rel = st.text_input(
        "Metadata file path (relative to cache dir or absolute)",
        value="metadata/WMB-taxonomy/cluster_to_cluster_annotation_membership_pivoted.csv",
    )
    expression_rel = st.text_input(
        "Expression file path (relative to cache dir or absolute)",
        value="expression/merfish_expression.parquet",
    )

    st.header("Gene panel")
    default_genes = st.multiselect(
        "Suggested receptor genes",
        options=DEFAULT_RECEPTOR_PANEL,
        default=["Adra2a", "Adrb1", "Chrm1", "Chrna4"],
    )
    extra_genes_raw = st.text_input("Additional genes (comma-separated)", "Arc,Gne,Rab15")
    extra_genes = [g.strip() for g in extra_genes_raw.split(",") if g.strip()]
    selected_genes = list(dict.fromkeys([*default_genes, *extra_genes]))

try:
    metadata_path = resolve_abc_file_path(cache_dir, metadata_rel)
except FileNotFoundError as exc:
    st.error(f"Metadata path could not be resolved from ABC cache: {exc}")
    st.stop()

expression_path = ""
if expression_rel:
    try:
        expression_path = resolve_abc_file_path(cache_dir, expression_rel)
    except FileNotFoundError as exc:
        st.warning(f"Expression path could not be resolved from ABC cache: {exc}")

try:
    metadata = load_metadata(metadata_path)
except (FileNotFoundError, DataSchemaError, ValueError) as exc:
    st.error(f"Could not load metadata: {exc}")
    st.stop()

expression = None
if expression_path:
    try:
        expression = load_expression_subset(expression_path, tuple(selected_genes))
    except FileNotFoundError:
        st.warning("Expression file not found. Continuing with metadata-only mode.")
    except Exception as exc:  # noqa: BLE001
        st.warning(f"Expression load failed. Continuing with metadata-only mode. Details: {exc}")

merged = metadata
if expression is not None and not expression.empty:
    merged = metadata.merge(expression, on="cell_id", how="left")

with st.sidebar:
    st.header("Filters")
    region_options = sorted(merged["region"].dropna().unique().tolist())
    class_options = sorted(merged["cell_class"].dropna().unique().tolist())

    regions = st.multiselect("Brain regions", region_options, default=[])
    cell_classes = st.multiselect("Cell classes", class_options, default=[])

    st.caption("Gene thresholds")
    gene_thresholds: dict[str, float] = {}
    for gene in selected_genes:
        if gene in merged.columns and merged[gene].notna().any():
            min_val = float(merged[gene].min(skipna=True))
            max_val = float(merged[gene].max(skipna=True))
            default_val = float(merged[gene].quantile(0.5))
            gene_thresholds[gene] = st.slider(
                f"{gene} ≥",
                min_value=min_val,
                max_value=max_val if max_val > min_val else min_val + 1.0,
                value=default_val,
            )

filtered = filter_cells(merged, regions, cell_classes, gene_thresholds)

left, right = st.columns([1, 1])
with left:
    st.metric("Cells after filters", f"{len(filtered):,}")
with right:
    st.metric("Unique regions", f"{filtered['region'].nunique():,}")

if filtered.empty:
    st.info("No cells match the active filters.")
    st.stop()

color_by = st.selectbox("Color points by", ["cell_class", "region"], index=0)

plot_tab, compare_tab, table_tab = st.tabs(["Spatial plots", "Gene comparison", "Data preview"])
with plot_tab:
    c1, c2 = st.columns(2)
    sampled = filtered.sample(min(len(filtered), 30_000))

    try:
        c1.plotly_chart(scatter_2d(filtered, color_by=color_by), use_container_width=True)
        c2.plotly_chart(scatter_3d(sampled, color_by=color_by), use_container_width=True)
        st.caption("3D plot is sampled to max 30k cells for responsiveness.")
    except PlotBackendUnavailableError as exc:
        st.warning(f"{exc} Falling back to native Streamlit charts.")
        c1.scatter_chart(filtered, x="x", y="y", color=color_by, size=None)
        c2.scatter_chart(sampled, x="x", y="z", color=color_by, size=None)
        st.caption("Fallback view: 2D projections (x,y) and (x,z). Install plotly for interactive 3D.")

with compare_tab:
    if selected_genes:
        group_col = st.radio("Group means by", ["cell_class", "region"], horizontal=True)
        summary = summarize_gene_expression(filtered, selected_genes, group_col)
        if summary.empty:
            st.info("No selected genes available in current dataset.")
        else:
            try:
                st.plotly_chart(gene_comparison_bar(summary, group_col), use_container_width=True)
            except PlotBackendUnavailableError as exc:
                st.warning(f"{exc} Showing table-only fallback.")
            st.dataframe(summary, use_container_width=True)
    else:
        st.info("Select at least one gene to compare expression.")

with table_tab:
    st.dataframe(filtered.head(2000), use_container_width=True)
