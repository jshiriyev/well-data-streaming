# streamlit_app.py
"""
Minimal Streamlit demo for the Survey class.

Features
--------
- Load Survey from CSV (smart constructor selection) or generate a synthetic Survey.
- Downsample for UI responsiveness.
- Plot plan view (DX vs DY) and section view (MD vs TVD).
- Download the downsampled arrays as CSV.

Expected CSV columns (any one of these sets):
  (A) MD, TVD
  (B) MD, INC, AZI               [angles in degrees]
  (C) MD, DX, DY, TVD
Optional tie-in for (B): xhead, yhead, datum (scalars; if absent defaults to 0).
"""

import io
import numpy as np
import pandas as pd
import streamlit as st
import plotly.graph_objects as go

from wellx.items import Survey  # <- your class from the code you shared


st.set_page_config(page_title="Survey Viewer", layout="wide")

# ------------------------ Sidebar controls ------------------------
st.sidebar.header("Data source")
mode = st.sidebar.radio("Choose input", ["Upload CSV", "Generate synthetic"], index=0)

st.sidebar.header("Downsampling")
max_pts = st.sidebar.slider("Max points for plotting", min_value=100, max_value=5000, value=1000, step=100)

invert_tvd = st.sidebar.checkbox("Invert TVD axis (depth down)", value=True)

st.sidebar.markdown("---")
st.sidebar.caption("Tip: Use smaller 'Max points' for very large surveys.")

# ------------------------ Load / Build Survey ------------------------
def build_survey_from_csv(df: pd.DataFrame) -> Survey:
    cols = {c.lower(): c for c in df.columns}  # case-flexible
    have = set(cols)

    def col(name):  # fetch with case insensitivity
        return df[cols[name]]

    # Constructor selection in priority order
    if {"md", "dx", "dy", "tvd"} <= have:
        return Survey.from_md_xyz(col("md").to_numpy(float),
                                  col("dx").to_numpy(float),
                                  col("dy").to_numpy(float),
                                  col("tvd").to_numpy(float))
    if {"md", "inc", "azi"} <= have:
        x0 = float(col("xhead").iloc[0]) if "xhead" in have else 0.0
        y0 = float(col("yhead").iloc[0]) if "yhead" in have else 0.0
        z0 = float(col("datum").iloc[0])  if "datum"  in have else 0.0
        return Survey.from_md_inc_azi(col("md").to_numpy(float),
                                      col("inc").to_numpy(float),
                                      col("azi").to_numpy(float),
                                      xhead=x0, yhead=y0, datum=z0)
    if {"md", "tvd"} <= have:
        return Survey.from_md_tvd(col("md").to_numpy(float),
                                  col("tvd").to_numpy(float))
    raise ValueError("CSV must contain either (MD,TVD) or (MD,INC,AZI) or (MD,DX,DY,TVD).")


def generate_synthetic_survey() -> Survey:
    st.sidebar.header("Synthetic parameters")
    n = st.sidebar.slider("Stations (N)", 5, 2000, 201, step=1)
    md_end = st.sidebar.number_input("MD end", value=1500.0, min_value=100.0)
    inc_deg = st.sidebar.number_input("Constant INC (deg)", value=30.0, min_value=0.0, max_value=180.0)
    azi_deg = st.sidebar.number_input("Constant AZI (deg, 0=N,90=E)", value=90.0, min_value=0.0, max_value=360.0)
    x0 = st.sidebar.number_input("xhead", value=0.0)
    y0 = st.sidebar.number_input("yhead", value=0.0)
    z0 = st.sidebar.number_input("datum (TVD at MD=0)", value=0.0)

    MD = np.linspace(0.0, float(md_end), int(n))
    INC = np.full_like(MD, float(inc_deg))
    AZI = np.full_like(MD, float(azi_deg))
    # Anchor the first station at 0 inclination/azi for a gentle tie-in if preferred:
    INC[0] = INC[0]  # leave as-is; adjust if you want a vertical tie-in: INC[0]=0

    return Survey.from_md_inc_azi(MD, INC, AZI, xhead=x0, yhead=y0, datum=z0)


# Build survey
survey = None
error = None

if mode == "Upload CSV":
    st.title("Survey Viewer — CSV")
    uploaded = st.file_uploader("Upload CSV with columns (see header for options)", type=["csv"])
    if uploaded:
        try:
            df = pd.read_csv(uploaded)
            survey = build_survey_from_csv(df)
            st.success("Survey loaded from CSV.")
        except Exception as e:
            error = str(e)
else:
    st.title("Survey Viewer — Synthetic")
    try:
        survey = generate_synthetic_survey()
        st.success("Synthetic survey generated.")
    except Exception as e:
        error = str(e)

if error:
    st.error(error)

if survey is None:
    st.stop()

# ------------------------ Downsample for plotting ------------------------
downs = survey.downsample(max_pts)
# downs returns a tuple skipping Nones in order (MD, TVD, DX, DY, INC, AZI)
# Let's rebuild dict with names to make usage clear:
names = ["MD", "TVD", "DX", "DY", "INC", "AZI"]
vals = {}
i = 0
for nm in names:
    arr = getattr(survey, nm, None)
    if arr is not None:
        vals[nm] = downs[i]
        i += 1
    else:
        vals[nm] = None

# ------------------------ Metrics ------------------------
c1, c2, c3, c4 = st.columns(4)
c1.metric("Stations (downsampled)", len(vals["MD"]) if vals["MD"] is not None else 0)
c2.metric("MD end", f'{survey.MD[-1]:.1f}')
c3.metric("TVD end", f'{survey.TVD[-1]:.1f}' if survey.TVD is not None else "N/A")
if survey.DX is not None and survey.DY is not None:
    c4.metric("Closure (E,N)", f'({survey.DX[-1]:.1f}, {survey.DY[-1]:.1f})')
else:
    c4.metric("Closure (E,N)", "N/A")

# ------------------------ Plots ------------------------
plot_cols = st.columns(2)

# Plan view
with plot_cols[0]:
    st.subheader("Plan View (DX vs DY)")
    if vals["DX"] is not None and vals["DY"] is not None:
        fig_plan = go.Figure()
        fig_plan.add_trace(go.Scatter(x=vals["DX"], y=vals["DY"], mode="lines+markers", name="Trajectory"))
        fig_plan.update_layout(xaxis_title="DX (Easting)", yaxis_title="DY (Northing)", height=450)
        st.plotly_chart(fig_plan, use_container_width=True)
    else:
        st.info("DX/DY not available for this survey (provide MD/INC/AZI or MD,DX,DY,TVD).")

# Section view
with plot_cols[1]:
    st.subheader("Section View (MD vs TVD)")
    if vals["MD"] is not None and vals["TVD"] is not None:
        fig_sec = go.Figure()
        fig_sec.add_trace(go.Scatter(x=vals["MD"], y=vals["TVD"], mode="lines+markers", name="TVD"))
        fig_sec.update_layout(xaxis_title="MD", yaxis_title="TVD (down +)",
                              height=450,
                              yaxis=dict(autorange="reversed" if invert_tvd else True))
        st.plotly_chart(fig_sec, use_container_width=True)
    else:
        st.info("MD/TVD not available for this survey.")

# ------------------------ Download (downsampled) ------------------------
st.subheader("Download downsampled survey")
out = pd.DataFrame({k: v for k, v in vals.items() if v is not None})
csv_bytes = out.to_csv(index=False).encode("utf-8")
st.download_button("Download CSV", data=csv_bytes, file_name="survey_downsampled.csv", mime="text/csv")

# ------------------------ Raw table (optional) ------------------------
with st.expander("Show downsampled table"):
    st.dataframe(out, use_container_width=True)
