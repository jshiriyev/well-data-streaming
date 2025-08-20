import base64

from datetime import datetime, timedelta

import io

import numpy as np
import pandas as pd

import plotly.express as px
import plotly.graph_objects as go

from plotly.subplots import make_subplots

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

import streamlit as st

import prodpy

from .items import Well

from .items._profile import well_3D_profile, well_schematic

from ._custom import _render_subplot

class WellStream:
	
	@staticmethod
	def render_summary(well:Well):
		"""Render sidebar with well information and controls"""

		st.header("🛢️ Well Information")

		st.info(f"""
			**Well Name:** {well.name}  
			**Field:** {well.field}  
			**Operator:** {well.operator}  
			**Country:** {well.country}
			""")
	
	@staticmethod
	def render_review_header(well:Well):
		"""Render main header"""
		
		col1, col2, col3 = st.columns([2, 1, 1])
		
		with col1:
			st.title(f"🛢️ {well.name}")
			st.caption(f"{well.field} | {well.operator}")
	
	@staticmethod
	def render_review_construction(well:Well):

		st.header("🏗️ Well Construction")
			
		col1, col2 = st.columns(2)
		
		with col1:

			st.subheader("3D Well Profile")

			fig = well_3D_profile(
				well.survey,
				well.perfs.base.iloc[-1],
				well.perfs.top.iloc[0],
				zmultp=2
			)

			st.plotly_chart(fig, use_container_width=True)		
			# st.dataframe(construction_info, use_container_width=True, hide_index=True)
		
		with col2:

			st.subheader("Completion Schematic")
			fig = well_schematic(well.layout)
			st.plotly_chart(fig, use_container_width=True)
			# st.info("Upload completion diagram or well schematic here")
			# completion_file = st.file_uploader("Upload Completion Diagram", type=['pdf', 'png', 'jpg'])

	@staticmethod
	def render_review_production(well:Well):
		"""Render production analysis tab"""
		st.header("📈 Production Analytics")
		
		# Key metrics
		col1, col2, col3, col4 = st.columns(4)
		
		with col1:
			st.metric(
				"Oil Rate", 
				f"{well.rates.orate.iloc[-1]:.1f} ton/gün",
				delta=f"{well.rates.orate.iloc[-1] - well.rates.orate.iloc[-2]:.1f}"
			)
		
		with col2:
			st.metric(
				"Gas Rate", 
				f"{well.rates.grate.iloc[-1]:.0f} km3/gün",
				delta=f"{well.rates.grate.iloc[-1] - well.rates.grate.iloc[-2]:.0f}"
			)
		
		with col3:
			st.metric(
				"Water Cut", 
				f"{well.rates.wrate.iloc[-1]:.1f} m3/gün",
				delta=f"{(well.rates.wrate.iloc[-1] - well.rates.wrate.iloc[-2]):.1f}"
			)
		
		with col4:
			st.metric(
				"Choke", 
				f"{well.rates.choke.iloc[-1]:.0f} mm",
				delta=f"{well.rates.choke.iloc[-1] - well.rates.choke.iloc[-2]:.0f}"
			)
		
		# # Production trends
		col1,col2 = st.columns(2)
		
		with col1:
			fig = prodpy.stream.plot2(well.rates)
			st.plotly_chart(fig, use_container_width=True)

		with col2:
			fig = prodpy.stream.plot3(well.tops,well.perfs)
			st.plotly_chart(fig, use_container_width=True)
	
	@staticmethod
	def render_review_intervention(well:Well):
		"""Render intervention analysis tab"""
		st.header("🔧 Intervention Record")
		
		col1, col2 = st.columns(2)
		
		with col1:
			st.subheader("Intervention History")
			st.dataframe(well.perfs, use_container_width=True)

	@staticmethod
	def render_review_reservoir(well:Well):
		"""Render reservoir analysis tab"""
		formation_data = well.reservoir

		st.header("🗻 Reservoir Description")
		
		col1, col2 = st.columns(2)
		
		with col1:
			st.subheader("Formation Properties")
			st.dataframe(formation_data, use_container_width=True)
			
			# Porosity vs Permeability
			fig = px.scatter(
				formation_data, 
				x='phie', y='perme',
				size='netflag',
				size_max=80,
				color='formation',
				title='Porosity vs Permeability',
				labels={'phie': 'Porosity (-)', 'perme': 'Permeability (mD)'},
				color_discrete_sequence=px.colors.qualitative.Set2
			)

			st.plotly_chart(fig, use_container_width=True)
		
		with col2:
			# Formation tops visualization
			fig = go.Figure()

			palette = px.colors.qualitative.Set2
			formations = formation_data["formation"].unique()
			color_map = {f: palette[i % len(palette)] for i, f in enumerate(formations)}

			for _, row in formation_data.iterrows():
				fig.add_trace(go.Bar(
					x=[row['formation']],
					y=[row['netflag']],
					name=row['formation'],
					marker_color=color_map[row["formation"]],   # <-- custom color
					textposition='auto'
				))

			fig.update_layout(
				title='Net Pay by Formation',
				xaxis_title='Formation',
				yaxis_title='Net Pay (m)',
				showlegend=False
			)
			st.plotly_chart(fig, use_container_width=True)
			
			# Reservoir quality index
			formation_data['rqi'] = formation_data['perme'] * formation_data['phie'] / 100
			
			fig = px.bar(
				formation_data, 
				x='formation', 
				y='rqi',
				title='Reservoir Quality Index',
				color='rqi',
				color_continuous_scale='viridis'
			)

			fig.update_layout(yaxis_title='RQI',coloraxis_showscale=False)

			st.plotly_chart(fig, use_container_width=True)
	
	@staticmethod
	def render_review_fluid_analysis(well:Well):
		"""Render advanced analysis tab"""
		st.header("🧪 Fluid Analysis")
		
		col1, col2 = st.columns(2)
	
	@staticmethod
	def render_custom_summary():

		if "grid_rows" not in st.session_state:
			st.session_state.grid_rows = 2
		if "grid_cols" not in st.session_state:
			st.session_state.grid_cols = 2
		if "subplot_cfgs" not in st.session_state:
	        st.session_state.subplot_cfgs = {}

		st.number_input("Rows", 1, 6, key="grid_rows")
        st.number_input("Cols", 1, 6, key="grid_cols")

	@staticmethod
	def render_custom_header(well:Well):

		st.title("🛢️ Well Plot Builder")
		st.caption("Pick a grid layout, then configure each subplot. Works with most well object shapes.")

		rows = st.session_state.grid_rows
		cols = st.session_state.grid_cols

		for r in range(rows):
			columns = st.columns(cols)
			for c in range(cols):
				i = r * cols + c
				with columns[c]:
					WellStream.render_custom_subplot(i, st.session_state.df_map)

	@staticmethod
	def render_custom_subplot(i: int, df_map: Dict[str, pd.DataFrame], share_x_hint: Optional[str] = None):

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

	@staticmethod
	def run(well:Well):
		"""Main application runner"""
		
		with st.sidebar:
			WellStream.render_review_summary(well)
		
		# Render header
		WellStream.render_review_header(well)
		
		# Main tabs
		tab1, tab2, tab3, tab4, tab5 = st.tabs([
			"📊 Construction",
			"📈 Production", 
			"🔧 Interventions",
			"🗻 Reservoir", 
			"🧪 Fluid Analysis"
		])
		
		with tab1:
			WellStream.render_review_construction(well)
			
		with tab2:
			WellStream.render_review_production(well)
			
		with tab3:
			WellStream.render_review_intervention(well)
		
		with tab4:
			WellStream.render_review_reservoir(well)
			
		with tab5:
			WellStream.render_review_fluid_analysis(well)