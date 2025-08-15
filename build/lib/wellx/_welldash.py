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

from .items import Well

class WellDash:
	
	@staticmethod
	def render_sidebar(well:Well):
		"""Render sidebar with well information and controls"""
		st.sidebar.header("🛢️ Well Information")

		st.sidebar.info(f"""
			**Well Name:** {well.name}  
			**Field:** {well.field}  
			**Operator:** {well.operator}  
			**Country:** {well.country}
			""")
		
		st.sidebar.divider()
		
		# Analysis options
		st.sidebar.header("⚙️ Analysis Options")
		analysis_period = st.sidebar.selectbox(
			"Analysis Period",
			["All data","Last 30 days","Last 90 days","Last 6 months","Last year"]
		)
		
		return analysis_period
	
	@staticmethod
	def render_header(well:Well):
		"""Render main header"""
		
		col1, col2, col3 = st.columns([2, 1, 1])
		
		with col1:
			st.title(f"🛢️ {well.name}")
			st.caption(f"{well.field} | {well.operator}")
	
	@staticmethod
	def render_construction(well:Well):

		st.header("🏗️ Well Construction")
			
		col1, col2 = st.columns(2)
		
		with col1:
			st.subheader("Well Details")
			# well_data = st.session_state.well_data
			
			# construction_info = pd.DataFrame([
			# 	['Spud Date', well_data['spud_date']],
			# 	['Completion Date', well_data['completion_date']],
			# 	['Total Depth', f"{well_data['total_depth']} ft"],
			# 	['Casing Size', well_data['casing_size']],
			# 	['Status', well_data['current_status']]
			# ], columns=['Parameter', 'Value'])
			
			# st.dataframe(construction_info, use_container_width=True, hide_index=True)
		
		with col2:
			st.subheader("Completion Schematic")
			# st.info("Upload completion diagram or well schematic here")
			# completion_file = st.file_uploader("Upload Completion Diagram", type=['pdf', 'png', 'jpg'])

	@staticmethod
	def render_production(well:Well):
		"""Render production analysis tab"""
		st.header("📈 Production Analytics")
		
		# production_data = st.session_state.production_data
		
		# Key metrics
		col1, col2, col3, col4 = st.columns(4)
		
		# latest_data = production_data.iloc[-1]
		
		# with col1:
		# 	st.metric(
		# 		"Oil Rate", 
		# 		f"{latest_data['oil_rate']:.1f} bbl/d",
		# 		delta=f"{latest_data['oil_rate'] - production_data.iloc[-30]['oil_rate']:.1f}"
		# 	)
		
		# with col2:
		# 	st.metric(
		# 		"Gas Rate", 
		# 		f"{latest_data['gas_rate']:.0f} Mcf/d",
		# 		delta=f"{latest_data['gas_rate'] - production_data.iloc[-30]['gas_rate']:.0f}"
		# 	)
		
		# with col3:
		# 	st.metric(
		# 		"Water Cut", 
		# 		f"{latest_data['water_cut']*100:.1f}%",
		# 		delta=f"{(latest_data['water_cut'] - production_data.iloc[-30]['water_cut'])*100:.1f}%"
		# 	)
		
		# with col4:
		# 	st.metric(
		# 		"Pressure", 
		# 		f"{latest_data['pressure']:.0f} psi",
		# 		delta=f"{latest_data['pressure'] - production_data.iloc[-30]['pressure']:.0f}"
		# 	)
		
		# Production trends
		col1, col2 = st.columns(2)
		
		# with col1:
		# 	fig = make_subplots(
		# 		rows=2, cols=1,
		# 		subplot_titles=('Production Rates', 'Pressure & Temperature'),
		# 		vertical_spacing=0.1
		# 	)
			
		# 	# Production rates
		# 	fig.add_trace(
		# 		go.Scatter(x=production_data['date'], y=production_data['oil_rate'], 
		# 				  name='Oil Rate', line=dict(color='green')), row=1, col=1
		# 	)
		# 	fig.add_trace(
		# 		go.Scatter(x=production_data['date'], y=production_data['gas_rate']/10, 
		# 				  name='Gas Rate (÷10)', line=dict(color='blue')), row=1, col=1
		# 	)
		# 	fig.add_trace(
		# 		go.Scatter(x=production_data['date'], y=production_data['water_rate'], 
		# 				  name='Water Rate', line=dict(color='red')), row=1, col=1
		# 	)
			
		# 	# Pressure and temperature
		# 	fig.add_trace(
		# 		go.Scatter(x=production_data['date'], y=production_data['pressure'], 
		# 				  name='Pressure', line=dict(color='purple')), row=2, col=1
		# 	)
			
		# 	fig.update_layout(height=600, title_text="Production Trends")
		# 	st.plotly_chart(fig, use_container_width=True)
		
		# with col2:
		# 	# Decline curve analysis
		# 	fig = px.scatter(
		# 		production_data, 
		# 		x='date', 
		# 		y='oil_rate',
		# 		title='Oil Rate Decline Analysis',
		# 		trendline='ols'
		# 	)
		# 	fig.update_layout(height=300)
		# 	st.plotly_chart(fig, use_container_width=True)
			
		# 	# Water cut analysis
		# 	fig = px.line(
		# 		production_data, 
		# 		x='date', 
		# 		y='water_cut',
		# 		title='Water Cut Trend',
		# 		labels={'water_cut': 'Water Cut (fraction)'}
		# 	)
		# 	fig.update_layout(height=300)
		# 	st.plotly_chart(fig, use_container_width=True)
	
	@staticmethod
	def render_intervention(well:Well):
		"""Render intervention analysis tab"""
		st.header("🔧 Intervention Analysis")
		
		# intervention_data = st.session_state.intervention_data
		
		col1, col2 = st.columns(2)
		
		# with col1:
		# 	st.subheader("Intervention History")
		# 	st.dataframe(intervention_data, use_container_width=True)
			
		# 	# Total costs
		# 	total_cost = intervention_data['cost'].sum()
		# 	st.metric("Total Intervention Cost", f"${total_cost:,.0f}")
			
		# with col2:
		# 	# Cost by intervention type
		# 	fig = px.pie(
		# 		intervention_data, 
		# 		values='cost', 
		# 		names='type',
		# 		title='Intervention Costs by Type'
		# 	)
		# 	st.plotly_chart(fig, use_container_width=True)
			
		# 	# Timeline
		# 	fig = px.timeline(
		# 		intervention_data,
		# 		x_start='date',
		# 		x_end='date',
		# 		y='type',
		# 		color='cost',
		# 		title='Intervention Timeline'
		# 	)
		# 	st.plotly_chart(fig, use_container_width=True)

	@staticmethod
	def render_reservoir(well:Well):
		"""Render reservoir analysis tab"""
		st.header("🗻 Reservoir Analysis")
		
		# formation_data = st.session_state.formation_data
		
		col1, col2 = st.columns(2)
		
		# with col1:
		# 	st.subheader("Formation Properties")
		# 	st.dataframe(formation_data, use_container_width=True)
			
		# 	# Porosity vs Permeability
		# 	fig = px.scatter(
		# 		formation_data, 
		# 		x='porosity', 
		# 		y='permeability',
		# 		size='net_pay',
		# 		color='formation',
		# 		title='Porosity vs Permeability',
		# 		labels={'porosity': 'Porosity (%)', 'permeability': 'Permeability (mD)'}
		# 	)
		# 	st.plotly_chart(fig, use_container_width=True)
		
		# with col2:
		# 	# Formation tops visualization
		# 	fig = go.Figure()
			
		# 	for _, row in formation_data.iterrows():
		# 		fig.add_trace(go.Bar(
		# 			x=[row['formation']],
		# 			y=[row['net_pay']],
		# 			name=row['formation'],
		# 			text=f"{row['depth']} ft",
		# 			textposition='auto'
		# 		))
			
		# 	fig.update_layout(
		# 		title='Net Pay by Formation',
		# 		xaxis_title='Formation',
		# 		yaxis_title='Net Pay (ft)',
		# 		showlegend=False
		# 	)
		# 	st.plotly_chart(fig, use_container_width=True)
			
		# 	# Reservoir quality index
		# 	formation_data['rqi'] = formation_data['permeability'] * formation_data['porosity'] / 100
			
		# 	fig = px.bar(
		# 		formation_data, 
		# 		x='formation', 
		# 		y='rqi',
		# 		title='Reservoir Quality Index',
		# 		color='rqi',
		# 		color_continuous_scale='viridis'
		# 	)
		# 	st.plotly_chart(fig, use_container_width=True)
	
	@staticmethod
	def render_fluid_analysis(well:Well):
		"""Render advanced analysis tab"""
		st.header("🧪 Advanced Analysis")
		
		col1, col2 = st.columns(2)
		
		# with col1:
		# 	st.subheader("Core Analysis Upload")
		# 	core_file = st.file_uploader("Upload Core Analysis", type=['csv', 'xlsx', 'las'])
			
		# 	st.subheader("Fluid Analysis Upload")
		# 	fluid_file = st.file_uploader("Upload Fluid Analysis", type=['csv', 'xlsx'])
			
		# with col2:
		# 	st.subheader("Well Logs Upload")
		# 	log_file = st.file_uploader("Upload Well Logs", type=['las', 'csv'])
			
		# 	st.subheader("Formation Tops")
		# 	tops_file = st.file_uploader("Upload Formation Tops", type=['csv', 'xlsx'])
		
		# # PVT Analysis section
		# st.subheader("PVT Analysis")
		
		# # Sample PVT data
		# pvt_data = pd.DataFrame({
		# 	'pressure': np.linspace(1000, 3000, 20),
		# 	'oil_fvf': 1.2 + 0.0002 * np.linspace(1000, 3000, 20),
		# 	'gas_fvf': 0.8 + 0.0001 * np.linspace(1000, 3000, 20),
		# 	'solution_gor': 500 + 0.1 * np.linspace(1000, 3000, 20)
		# })
		
		# fig = make_subplots(
		# 	rows=2, cols=2,
		# 	subplot_titles=('Oil FVF', 'Gas FVF', 'Solution GOR', 'Viscosity'),
		# 	vertical_spacing=0.1
		# )
		
		# fig.add_trace(go.Scatter(x=pvt_data['pressure'], y=pvt_data['oil_fvf'], name='Oil FVF'), row=1, col=1)
		# fig.add_trace(go.Scatter(x=pvt_data['pressure'], y=pvt_data['gas_fvf'], name='Gas FVF'), row=1, col=2)
		# fig.add_trace(go.Scatter(x=pvt_data['pressure'], y=pvt_data['solution_gor'], name='Solution GOR'), row=2, col=1)
		
		# fig.update_layout(height=600, title_text="PVT Properties")
		# st.plotly_chart(fig, use_container_width=True)
	
	@staticmethod
	def run(well:Well):
		"""Main application runner"""
		# Render sidebar
		analysis_period = self.render_sidebar(well)
		
		# Render header
		self.render_header(well)
		
		# Main tabs
		tab1, tab2, tab3, tab4, tab5 = st.tabs([
			"📊 Construction",
			"📈 Production", 
			"🔧 Interventions",
			"🗻 Reservoir", 
			"🧪 Fluid Analysis"
		])
		
		with tab1:
			self.render_construction(well)
			
		with tab2:
			self.render_production(well)
			
		with tab3:
			self.render_intervention(well)
		
		with tab4:
			self.render_reservoir(well)
			
		with tab5:
			self.render_fluid_analysis(well)