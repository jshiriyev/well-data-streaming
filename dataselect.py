import numpy as np
import pandas as pd

import plotly.graph_objects as go

from scipy.stats import linregress

import streamlit as st

def plot_measured(frame,figure=None):

	if figure is None:
		figure = go.Figure()

	observed = go.Scatter(
		x = frame["x"],
		y = frame["y"],
		mode = 'markers',
		# marker = dict(opacity=opacity),
		)

	figure.add_trace(observed)

	return figure

def plot_computed(frame,figure=None):

	if figure is None:
		figure = go.Figure()

	forecast = go.Scatter(
		x = frame['x'],
		y = frame['y'],
		mode = 'lines',
		line = dict(color="red"),
		)

	figure.add_trace(forecast)

	return figure

def optimize(frame,indices=None):

	if indices:
		frame = frame.iloc[indices,:]

	x,y = frame['x'],frame['y']

	r = linregress(x,y)

	xfit = np.linspace(0.5,6.5)

	return pd.DataFrame(dict(x=xfit,y=r.slope*xfit+r.intercept))

measured = pd.DataFrame(dict(x=[1,2,3,4,5,6],y=[1.1,1.9,3.1,4.75,5.05,6]))

if "events" in st.session_state:
	indices = st.session_state.events.selection["point_indices"]
else:
	indices = None

computed = optimize(measured,indices)

figure = go.Figure()

figure = plot_measured(measured,figure)
figure = plot_computed(computed,figure)

st.plotly_chart(figure,on_select="rerun",key="events")