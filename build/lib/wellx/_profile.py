import plotly.graph_objects as go

from .items import Well

def profile3D(*args:Well,zstretch:int=2):
	
	fig = go.Figure()

	for well in args:

		fig.add_trace(go.Scatter3d(
			x=well.survey['X'],
			y=well.survey['Y'],
			z=well.survey['TVD'],
			mode="lines",
			name="",
			hovertemplate=f"{well.name}<br>East:%{{x:.1f}}<br>North:%{{y:.1f}}<br>Depth:%{{z:.1f}}"
		))

	fig.update_layout(
		title='Well Profile (3D)',
		height=750,
		scene=dict(
			xaxis_title="East (m)",
			yaxis_title="North (m)",
			zaxis_title="Depth (m)",
			zaxis=dict(autorange="reversed"),
        	aspectratio=dict(x=1, y=1, z=zstretch)    # stretch z-axis relative to x,y
		),
		margin=dict(l=0,r=0,b=0,t=40)
	)

	return fig