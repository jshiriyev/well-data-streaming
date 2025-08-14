import datetime

# import numpy as np
import pandas as pd

# import plotly.graph_objects as go

# from scipy.stats import linregress

import prodpy as pp

import streamlit as st

# def plot_measured(frame,figure=None):

# 	if figure is None:
# 		figure = go.Figure()

# 	observed = go.Scatter(
# 		x = frame["x"],
# 		y = frame["y"],
# 		mode = 'markers',
# 		# marker = dict(opacity=opacity),
# 		)

# 	figure.add_trace(observed)

# 	return figure

# def plot_computed(frame,figure=None):

# 	if figure is None:
# 		figure = go.Figure()

# 	forecast = go.Scatter(
# 		x = frame['x'],
# 		y = frame['y'],
# 		mode = 'lines',
# 		line = dict(color="red"),
# 		)

# 	figure.add_trace(forecast)

# 	return figure

# def optimize(frame,indices=None):

# 	if indices is not None:
# 		frame = frame.iloc[indices,:]

# 	if frame.shape[0]<2:
# 		return pd.DataFrame(dict(x=[],y=[]))

# 	x,y = frame['x'],frame['y']

# 	r = linregress(x,y)
		
# 	xfit = np.linspace(0.5,6.5)

# 	return pd.DataFrame(dict(x=xfit,y=r.slope*xfit+r.intercept))

#################################################################

dates = [
	datetime.date(2024,1,1),
	datetime.date(2024,2,1),
	datetime.date(2024,3,1),
	datetime.date(2024,4,1),
	datetime.date(2024,5,1),
	datetime.date(2024,6,1),
	]

rates = [1.1,1.9,3.1,4.75,5.05,6]

frame = pd.DataFrame(dict(dates=dates,rates=rates))

diamond = pp.decline.Diamond(datehead='dates',ratehead='rates')

# if "events" in st.session_state:
# 	indices = st.session_state.events.selection["point_indices"]
# else:
# 	indices = None

figure,model = diamond(frame,
	analysis = dict(fitlims=((datetime.date(2023,1,1),datetime.date(2025,1,1)),)))

# computed = optimize(frame,indices)

# figure = go.Figure()

# figure = plot_measured(frame,figure)
# figure = plot_computed(computed,figure)

# st.plotly_chart(figure,on_select="rerun",key="events")