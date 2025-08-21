import pandas as pd

import plotly.graph_objects as go

import numpy as np

def _create_sphere_mesh(xc:float=0, yc:float=0, zc:float=0, radius:float=1, nodes:float=50, zmultp:float=1.,**kwargs):
	"""Return the coordinates for plotting a sphere centered at (x,y,z)"""
	d = np.pi/nodes

	theta, phi = np.mgrid[0:np.pi+d:d, 0:2*np.pi:d]

	x = xc + radius * np.cos(phi)*np.sin(theta)
	y = yc + radius * np.sin(phi)*np.sin(theta)
	z = zc + radius * np.cos(theta) * zmultp

	x,y,z = np.vstack([x.ravel(), y.ravel(), z.ravel()])

	return go.Mesh3d(x=x,y=y,z=z,**kwargs)

	return points

def _create_disk_mesh(xc:float=0, yc:float=0, zc:float=0, radius:float=1, nodes:float=50, **kwargs):

	theta = np.linspace(0, 2 * np.pi, nodes, endpoint=False)

	x = np.r_[0.0, radius*np.cos(theta)]
	y = np.r_[0.0, radius*np.sin(theta)]
	z = np.r_[0.0, np.zeros_like(theta)]

	i = np.zeros(nodes, dtype=np.int32)			  # center index 0
	j = np.arange(1, nodes+1, dtype=np.int32)		# 1..n
	k = np.r_[np.arange(2, nodes+1), 1].astype(np.int32)  # 2..n, wrap to 1

	return go.Mesh3d(x=x,y=y,z=z,i=i,j=j,k=k,**kwargs)

def profile3D(survey:pd.DataFrame,*args:float,zmultp:int=None):
	
	fig = go.Figure()

	fig.add_trace(go.Scatter3d(
		x=survey['X'],
		y=survey['Y'],
		z=survey['TVD'],
		mode="lines",
		# line=dict(color='black'),
		name="",
		hovertemplate=f"East:%{{x:.1f}}<br>North:%{{y:.1f}}<br>Depth:%{{z:.1f}}"
	))

	xmin,xmax = survey['X'].min(),survey['X'].max()
	ymin,ymax = survey['Y'].min(),survey['Y'].max()
	zmin,zmax = survey['TVD'].min(),survey['TVD'].max()

	hmin,hmax = min(xmin,ymin),max(xmax,ymax)

	fig_zmultp = (zmax-zmin)/(hmax-hmin) if zmultp is None else zmultp

	tic_zmultp = 1. if zmultp is None else (zmax-zmin)/(hmax-hmin)/zmultp

	for md in args:

		xc = np.interp(md, survey['MD'], survey['X'])
		yc = np.interp(md, survey['MD'], survey['Y'])
		zc = np.interp(md, survey['MD'], survey['TVD'])

		fig.add_trace(_create_sphere_mesh(
			xc=xc,yc=yc,zc=zc,radius=10,zmultp=tic_zmultp,
			color='blue',opacity=0.80,alphahull=0
			)
		)

	fig.update_layout(
		height=1000,
		scene=dict(
			xaxis=dict(range=[hmin, hmax]),
			yaxis=dict(range=[hmin, hmax]),
			xaxis_title="East (m)",
			yaxis_title="North (m)",
			zaxis_title="Depth (m)",
			zaxis=dict(autorange="reversed"),
			aspectmode='manual',
			aspectratio=dict(x=1, y=1, z=fig_zmultp)	# stretch z-axis relative to x,y
		),
		margin=dict(l=0,r=0,b=0,t=40)
	)

	return fig
