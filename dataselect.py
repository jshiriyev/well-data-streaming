import numpy as np
import pandas as pd

import plotly.graph_objects as go

from scipy.stats import linregress

import streamlit as st

from streamlit_plotly_events import plotly_events

# OPTIMIZATION FUNCTION

def optimize(frame,myevent=None):

	if myevent is not None:
		frame = frame.iloc[myevent.selection['point_indices'],:]

	print(frame)

	x,y = frame['x'],frame['y']

	r = linregress(x,y)

	xfit = np.linspace(0.5,6.5)

	return pd.DataFrame(dict(x=xfit,y=r.slope*xfit+r.intercept))

# PRESENTING ORIGINAL DATA

data = dict(x=[1,2,3,4,5,6],y=[1.1,1.9,3.1,4.75,5.05,6])

frame = pd.DataFrame(data)

fig = go.Figure()

observed = go.Scatter(
	x = frame["x"],
	y = frame["y"],
	mode = 'markers',
	# marker = dict(opacity=opacity),
	)

fig.add_trace(observed)

# SELECTING DATA

fit = optimize(frame)

forecast = go.Scatter(
	x = fit['x'],
	y = fit['y'],
	mode = 'lines',
	line = dict(color="red"),
	)

fig.add_trace(forecast)

st.plotly_chart(fig,key="myevent",on_select='rerun')

st.write(st.session_state.myevent)