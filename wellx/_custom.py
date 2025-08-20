# app.py
# Streamlit Well Plotter: build a custom multi-plot dashboard from a "well" instance.
# Run: streamlit run app.py
# Notes:
# - If your environment already has a variable/module exposing `well`, set WELL_IMPORT_MODE below.
# - Otherwise, upload a pickled well object (.pkl) from the sidebar.
# - The app scans the well object to find pandas DataFrames and numeric columns for plotting.

import io
import inspect
import json
import sys
import types
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

# -----------------------
# Config: how to find your `well` by default
# -----------------------
# Option A: "import" -> we import from a module path you specify in the sidebar (e.g., mypkg.my_well:well)
# Option B: "none"   -> user must upload a pickle of the well object
DEFAULT_WELL_IMPORT_MODE = "none"  # "import" or "none"
st.set_page_config(page_title="Well Plot Builder", layout="wide")

# -----------------------
# Helpers to discover DataFrames inside an arbitrary object
# -----------------------
def _is_df(obj: Any) -> bool:
    return isinstance(obj, pd.DataFrame)

def _is_series(obj: Any) -> bool:
    return isinstance(obj, pd.Series)

def _walk_object_for_dfs(obj: Any, prefix: str = "well") -> Dict[str, pd.DataFrame]:
    """
    Recursively walk attributes / mappings / sequences in `obj`
    to collect pandas DataFrames. Returns a dict mapping a label path -> DataFrame.
    """
    found: Dict[str, pd.DataFrame] = {}

    # Direct DF
    if _is_df(obj):
        found[prefix] = obj
        return found

    # Series (convert to a DF for convenience)
    if _is_series(obj):
        found[prefix] = obj.to_frame(name=getattr(obj, "name", "series"))
        return found

    # Mappings (dict-like)
    if isinstance(obj, dict):
        for k, v in obj.items():
            label = f"{prefix}.{k}"
            if _is_df(v):
                found[label] = v
            elif _is_series(v):
                found[label] = v.to_frame(name=str(k))
            else:
                # avoid recursing into very large byte arrays / primitives
                if _is_container_like(v):
                    found.update(_walk_object_for_dfs(v, prefix=label))
        return found

    # Objects: scan attributes
    # Avoid standard library heavy objects and callables
    if hasattr(obj, "__dict__"):
        for name, value in vars(obj).items():
            if name.startswith("_"):
                continue
            label = f"{prefix}.{name}"
            if _is_df(value):
                found[label] = value
            elif _is_series(value):
                found[label] = value.to_frame(name=name)
            else:
                if _is_container_like(value):
                    found.update(_walk_object_for_dfs(value, prefix=label))
        return found

    # Sequences/iterables of DFs
    if isinstance(obj, (list, tuple)):
        for i, v in enumerate(obj):
            label = f"{prefix}[{i}]"
            if _is_df(v):
                found[label] = v
            elif _is_series(v):
                found[label] = v.to_frame(name=f"series_{i}")
            else:
                if _is_container_like(v):
                    found.update(_walk_object_for_dfs(v, prefix=label))
        return found

    # Fallback: nothing
    return found

def _is_container_like(x: Any) -> bool:
    if _is_df(x) or _is_series(x):
        return True
    # Avoid recursing into strings/bytes/numbers
    if isinstance(x, (str, bytes, bytearray, memoryview, np.ndarray)):
        return False
    # Recurse into dicts, lists, tuples, and objects with __dict__
    return isinstance(x, (dict, list, tuple)) or hasattr(x, "__dict__")

def _numeric_columns(df: pd.DataFrame) -> List[str]:
    return [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

def _all_columns(df: pd.DataFrame) -> List[str]:
    return list(df.columns)

def _datetime_like(series: pd.Series) -> bool:
    return pd.api.types.is_datetime64_any_dtype(series) or pd.api.types.is_period_dtype(series) or pd.api.types.is_timedelta64_dtype(series)

def _infer_x_candidates(df: pd.DataFrame) -> List[str]:
    # Prefer datetime columns, then index (if datetime), else any column
    cols = []
    dt_cols = [c for c in df.columns if _datetime_like(df[c])]
    cols.extend(dt_cols)
    if isinstance(df.index, pd.DatetimeIndex):
        cols.append("__index__")
    # Also common names
    for c in ["depth", "DEPT", "md", "MD", "time", "Time", "DATE", "date"]:
        if c in df.columns and c not in cols:
            cols.append(c)
    # Fallback to all columns
    for c in df.columns:
        if c not in cols:
            cols.append(c)
    return cols

# -----------------------
# Layout/plot config state
# -----------------------
@dataclass
class SubplotConfig:
    df_key: Optional[str] = None
    x_col: Optional[str] = None
    y_cols: Tuple[str, ...] = tuple()
    plot_type: str = "line"  # line | scatter | step
    log_x: bool = False
    log_y: bool = False
    resample_rule: str = ""  # e.g., '1D', 'H' (if datetime)
    agg: str = "mean"  # mean, sum, min, max, median
    filter_expr: str = ""  # pandas-query string

DEFAULT_PLOT_TYPES = ["line", "scatter", "step"]
DEFAULT_AGGS = ["mean", "sum", "min", "max", "median"]

def _ensure_session():
    if "grid_rows" not in st.session_state:
        st.session_state.grid_rows = 2
    if "grid_cols" not in st.session_state:
        st.session_state.grid_cols = 2
    if "subplot_cfgs" not in st.session_state:
        st.session_state.subplot_cfgs = {}  # idx -> SubplotConfig
    if "well" not in st.session_state:
        st.session_state.well = None
    if "df_map" not in st.session_state:
        st.session_state.df_map = {}

_ensure_session()

# -----------------------
# Sidebar: bring in well
# -----------------------
st.sidebar.header("Well Source")

import_mode = st.sidebar.selectbox(
    "How do you want to provide the well?",
    options=["none (upload)", "import module path"],
    index=0 if DEFAULT_WELL_IMPORT_MODE == "none" else 1,
)

if import_mode == "import module path":
    module_path = st.sidebar.text_input(
        "Module path (format: module.submodule:var_name)",
        value="my_package.my_well:well",
        help="Example: mypkg.objects:well_obj  → imports 'well_obj' from module 'mypkg.objects'",
    )
    if st.sidebar.button("Import well"):
        try:
            mod_str, var_name = module_path.split(":")
            mod = __import__(mod_str, fromlist=["*"])
            well_obj = getattr(mod, var_name)
            st.session_state.well = well_obj
            st.success("Imported well from module path.")
        except Exception as e:
            st.error(f"Import failed: {e}")

else:
    uploaded = st.sidebar.file_uploader("Upload pickled well (.pkl)", type=["pkl", "pickle"])
    if uploaded is not None:
        try:
            import pickle
            well_obj = pickle.load(uploaded)
            st.session_state.well = well_obj
            st.success("Loaded well from uploaded pickle.")
        except Exception as e:
            st.error(f"Failed to load pickle: {e}")

# If not provided yet, offer a tiny mock helper
with st.sidebar.expander("No well? Create a small demo"):
    if st.button("Create demo well"):
        class DemoWell:
            def __init__(self):
                idx = pd.date_range("2023-01-01", periods=200, freq="D")
                df_prod = pd.DataFrame(
                    {
                        "oil_bopd": np.random.gamma(20, 5, size=len(idx)),
                        "water_bwpd": np.random.gamma(5, 3, size=len(idx)),
                        "gas_mscfd": np.random.gamma(15, 8, size=len(idx)),
                    },
                    index=idx,
                )
                df_prod.index.name = "date"
                depth = np.linspace(1000, 3000, 300)
                df_logs = pd.DataFrame(
                    {
                        "DEPT": depth,
                        "GR": np.clip(np.random.normal(75, 15, len(depth)), 0, 150),
                        "RHOB": np.clip(np.random.normal(2.4, 0.1, len(depth)), 1.8, 3.0),
                        "NPHI": np.clip(np.random.normal(0.25, 0.08, len(depth)), 0, 0.6),
                    }
                )
                self.dataframe = df_prod
                self.logs = df_logs
                self.curves = {"static": df_logs, "production": df_prod}

        st.session_state.well = DemoWell()
        st.success("Demo well created.")

# -----------------------
# Discover dataframes
# -----------------------
st.sidebar.markdown("---")
if st.session_state.well is not None:
    df_map = _walk_object_for_dfs(st.session_state.well, prefix="well")
    # De-duplicate identical objects by id
    canonical: Dict[int, str] = {}
    unique_df_map: Dict[str, pd.DataFrame] = {}
    for k, df in df_map.items():
        ptr = id(df)
        if ptr in canonical:
            continue
        canonical[ptr] = k
        unique_df_map[k] = df.copy()
    st.session_state.df_map = unique_df_map

if not st.session_state.df_map:
    st.info("Provide a well object (import or upload) to start. Then I’ll scan it for DataFrames.")
else:
    with st.sidebar.expander("Data sources found", expanded=False):
        for name, df in st.session_state.df_map.items():
            st.caption(f"• {name}  — shape {df.shape}")

# -----------------------
# Presets: Save/Load layout
# -----------------------
st.sidebar.markdown("---")
st.sidebar.subheader("Layout Presets")
preset_upload = st.sidebar.file_uploader("Load preset (.json)", type=["json"], key="preset_upload")
if preset_upload is not None:
    try:
        preset = json.load(preset_upload)
        st.session_state.grid_rows = int(preset["rows"])
        st.session_state.grid_cols = int(preset["cols"])
        st.session_state.subplot_cfgs = {
            int(k): SubplotConfig(**v) for k, v in preset.get("subplot_cfgs", {}).items()
        }
        st.success("Preset loaded.")
    except Exception as e:
        st.error(f"Failed to load preset: {e}")

def _download_preset_button():
    out = {
        "rows": st.session_state.grid_rows,
        "cols": st.session_state.grid_cols,
        "subplot_cfgs": {
            idx: vars(cfg) for idx, cfg in st.session_state.subplot_cfgs.items()
        },
    }
    st.download_button(
        "💾 Download current preset",
        data=json.dumps(out, indent=2),
        file_name="well_plot_layout.json",
        mime="application/json",
    )

# -----------------------
# Main UI: Grid controls
# -----------------------
st.title("🛢️ Well Plot Builder")
st.caption("Pick a grid layout, then configure each subplot. Works with most well object shapes.")

with st.container():
    col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 1])
    with col_a:
        st.number_input("Rows", 1, 6, key="grid_rows")
    with col_b:
        st.number_input("Cols", 1, 6, key="grid_cols")
    with col_c:
        share_x = st.checkbox("Share x-axis (by type)", value=False)
    with col_d:
        _download_preset_button()

total_plots = st.session_state.grid_rows * st.session_state.grid_cols

# Ensure configs exist
for i in range(total_plots):
    if i not in st.session_state.subplot_cfgs:
        st.session_state.subplot_cfgs[i] = SubplotConfig()

# Trim configs if user reduced grid size
for i in sorted(list(st.session_state.subplot_cfgs.keys()), reverse=True):
    if i >= total_plots:
        del st.session_state.subplot_cfgs[i]

# -----------------------
# Subplot configuration + rendering
# -----------------------
def _apply_filter_and_resample(df: pd.DataFrame, cfg: SubplotConfig) -> pd.DataFrame:
    work = df.copy()
    # Filter
    if cfg.filter_expr.strip():
        try:
            work = work.query(cfg.filter_expr)
        except Exception as e:
            st.warning(f"Filter ignored (error: {e})")
    # Resample (only if datetime index or datetime x is selected and we set index before resampling)
    if cfg.resample_rule and cfg.x_col in (work.columns.tolist() + ["__index__"]):
        # Identify x series
        if cfg.x_col == "__index__":
            x_series = work.index
        else:
            x_series = work[cfg.x_col]
        if _datetime_like(pd.Series(x_series)):
            # set index to x for resample
            try:
                temp = work.set_index(x_series)
                if cfg.agg in DEFAULT_AGGS:
                    agg_fn = cfg.agg
                else:
                    agg_fn = "mean"
                work = temp.resample(cfg.resample_rule).agg(agg_fn)
                # preserve x as index
                work.index.name = cfg.x_col if cfg.x_col != "__index__" else work.index.name
                return work
            except Exception as e:
                st.warning(f"Resample ignored (error: {e})")
    return work

def _get_x_y(df: pd.DataFrame, cfg: SubplotConfig) -> Tuple[pd.Series, Dict[str, pd.Series], str]:
    # Resolve X
    if cfg.x_col == "__index__":
        x = df.index
        x_name = df.index.name or "index"
    else:
        x = df[cfg.x_col] if cfg.x_col in df.columns else pd.Series(np.arange(len(df)), name="index")
        x_name = cfg.x_col or "index"

    ys: Dict[str, pd.Series] = {}
    for col in cfg.y_cols:
        if col in df.columns:
            ys[col] = df[col]
    return x, ys, x_name

def _render_subplot(i: int, df_map: Dict[str, pd.DataFrame], share_x_hint: Optional[str] = None):
    cfg: SubplotConfig = st.session_state.subplot_cfgs[i]
    with st.expander(f"Subplot {i+1} • settings", expanded=(i == 0)):
        df_key = st.selectbox(
            "Data source",
            options=["— select —"] + list(df_map.keys()),
            index=(list(df_map.keys()).index(cfg.df_key) + 1) if cfg.df_key in df_map else 0,
            key=f"dfkey_{i}",
        )
        if df_key != "— select —":
            cfg.df_key = df_key
            df = df_map[df_key].copy()

            # Candidate x and y columns
            x_opts = _infer_x_candidates(df)
            num_cols = _numeric_columns(df)
            all_cols = _all_columns(df)

            # Pick x
            x_idx = x_opts.index(cfg.x_col) if cfg.x_col in x_opts else 0
            cfg.x_col = st.selectbox("X axis", options=x_opts, index=x_idx, key=f"x_{i}")

            # Pick y (multi-select numeric)
            default_y = [c for c in cfg.y_cols if c in num_cols]
            if not default_y and num_cols:
                default_y = [num_cols[0]]
            cfg.y_cols = tuple(
                st.multiselect("Y column(s)", options=num_cols, default=default_y, key=f"y_{i}")
            )

            # Plot type
            cfg.plot_type = st.selectbox("Plot type", DEFAULT_PLOT_TYPES, index=DEFAULT_PLOT_TYPES.index(cfg.plot_type) if cfg.plot_type in DEFAULT_PLOT_TYPES else 0, key=f"type_{i}")

            # Query filter
            cfg.filter_expr = st.text_input(
                "Filter (pandas query, optional)", value=cfg.filter_expr, placeholder="e.g., GR < 80 and DEPT.between(1500, 2500)",
                key=f"filter_{i}",
            )

            # Resample
            cols = st.columns(3)
            with cols[0]:
                cfg.resample_rule = st.text_input("Resample rule (optional)", value=cfg.resample_rule, placeholder="e.g., 1D, 1H, 10min", key=f"rs_{i}")
            with cols[1]:
                cfg.agg = st.selectbox("Aggregation", DEFAULT_AGGS, index=DEFAULT_AGGS.index(cfg.agg) if cfg.agg in DEFAULT_AGGS else 0, key=f"agg_{i}")
            with cols[2]:
                cfg.log_x = st.checkbox("log X", value=cfg.log_x, key=f"logx_{i}")
                cfg.log_y = st.checkbox("log Y", value=cfg.log_y, key=f"logy_{i}")

            # Apply transform for preview table
            preview_df = _apply_filter_and_resample(df, cfg)
            st.dataframe(preview_df.head(10), use_container_width=True)

    # Render chart if configured
    if cfg.df_key and cfg.df_key in df_map and cfg.y_cols:
        work = _apply_filter_and_resample(df_map[cfg.df_key], cfg)
        x, ys, x_name = _get_x_y(work, cfg)

        # Build a tidy frame for plotly
        plot_df_rows = []
        for col, s in ys.items():
            # Align lengths if resampled changed index
            try:
                if len(s) != len(x):
                    s = s.reindex(work.index) if cfg.x_col == "__index__" else s
            except Exception:
                pass
            plot_df_rows.append(pd.DataFrame({x_name: x, "value": s, "series": col}))
        if not plot_df_rows:
            st.warning("Nothing to plot yet—choose at least one Y column.")
            return
        tidy = pd.concat(plot_df_rows, ignore_index=True)

        # Draw
        if cfg.plot_type == "scatter":
            fig = px.scatter(tidy, x=x_name, y="value", color="series")
        elif cfg.plot_type == "step":
            # Workaround: line_shape="hv" as a step-like
            fig = px.line(tidy, x=x_name, y="value", color="series")
            fig.update_traces(line_shape="hv")
        else:
            fig = px.line(tidy, x=x_name, y="value", color="series")

        # Log scales
        fig.update_layout(
            xaxis_type="log" if cfg.log_x else "linear",
            yaxis_type="log" if cfg.log_y else "linear",
            margin=dict(l=10, r=10, t=10, b=10),
            height=350,
        )

        # Share x across subplots if desired (heuristic: same x dtype)
        if share_x_hint:
            fig.update_xaxes(matches=share_x_hint)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("Select a data source and at least one Y column to render this subplot.")

# -----------------------
# Render the grid
# -----------------------
# Heuristic: determine a "share_x" name by chosen x dtype in first configured subplot
share_x_name = None
if share_x:
    for i in range(total_plots):
        cfg = st.session_state.subplot_cfgs[i]
        if cfg.df_key and cfg.x_col:
            # Identify dtype bucket: datetime / numeric / other
            df = st.session_state.df_map[cfg.df_key]
            if cfg.x_col == "__index__":
                x_series = df.index.to_series()
            else:
                x_series = df[cfg.x_col] if cfg.x_col in df.columns else pd.Series(dtype=float)
            if _datetime_like(x_series):
                share_x_name = "x_datetime"
            elif pd.api.types.is_numeric_dtype(x_series):
                share_x_name = "x_numeric"
            else:
                share_x_name = "x_other"
            break

rows = st.session_state.grid_rows
cols = st.session_state.grid_cols

for r in range(rows):
    columns = st.columns(cols)
    for c in range(cols):
        i = r * cols + c
        with columns[c]:
            _render_subplot(i, st.session_state.df_map, share_x_hint=share_x_name)

# -----------------------
# Footer tips
# -----------------------
st.markdown("---")
with st.expander("Tips & Examples"):
    st.markdown(
        """
- **Depth plots**: pick `DEPT` (or `depth`) as X and e.g. `GR`, `RHOB`, `NPHI` as Y with `step` or `line`.
- **Production over time**: if your production DataFrame has a DatetimeIndex, set X to `__index__` and choose `oil_bopd`, `water_bwpd`, etc.
- **Resampling**: For daily production → monthly, set *Resample rule* to `1M` and Aggregation to `sum` or `mean`.
- **Filter**: Use pandas query syntax, e.g. `DEPT >= 1500 and DEPT <= 2500` or `GR < 80`.
- **Presets**: Design once, click **Download current preset**, and load it next time.
        """
    )
