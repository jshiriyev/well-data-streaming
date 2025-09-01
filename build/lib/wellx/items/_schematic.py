import pandas as pd

import plotly.graph_objects as go

import numpy as np

def schematic(frame:pd.DataFrame):
	# Work on a single well (or group by well if multiple)
	
	well = frame["well"].iloc[0]

	dff = frame.sort_values(["top_md_m","outer_diam_in"], ascending=[True, False]).reset_index(drop=True)

	# Compute width scaling: normalize OD to a visual width
	max_od = dff["outer_diam_in"].max()

	def x_bounds(od):
		# center around x=lane; width scaled by OD
		width = 0.6 * (od / max_od)   # scale factor
		return -width/2.0,width/2.0

	fig = go.Figure()

	# For readability, we put each string_id into its own "lane"
	lanes = {sid: i for i, sid in enumerate(dff["string_id"].unique())}

	# Draw segments
	for _, r in dff.iterrows():
		lane = lanes[r["string_id"]]
		x0, x1 = x_bounds(r["outer_diam_in"])
		y0, y1 = r["top_md_m"], r["bottom_md_m"]

		for x,y in [[[x0,x0],[y0,y1]],[[x1,x1],[y0,y1]]]:
			fig.add_trace(go.Scatter(
				x=x,y=y,
				mode="lines",
				line=dict(color='black'),
				name=f'{r["string_id"]}',
				hovertemplate=(
					f"{r['string_id']}<br>"
					f"{r['kind']}, {r['section']}<br>"
					f"OD: {r['outer_diam_in']:.3f}\" | ID: {r['inner_diam_in']:.3f}\" | Wt: {r['weight_lbft']:.1f} lb/ft<br>"
					f"MD: {y0:.0f} → {y1:.0f} m<br>"
					f"Cement top: {r['cement_top_md_m'] if not np.isnan(r['cement_top_md_m']) else '—'} m<br>"
					f"Shoe: {r['shoe_md_m'] if not np.isnan(r['shoe_md_m']) else '—'} m<br>"
					f"Hanger: {r['hanger_md_m'] if not np.isnan(r['hanger_md_m']) else '—'} m<br>"
					f"Crossover: {r['crossover_md_m'] if not np.isnan(r['crossover_md_m']) else '—'} m<br>"
					f"{r['grade']} / {r['connection']}<extra></extra>"
				),
			))

		# Cement top line (optional)
		if not np.isnan(r["cement_top_md_m"]) and r["cement_top_md_m"] > r["top_md_m"]:

			y00, y01 = y1, r["cement_top_md_m"]

			for x in [[x0,x0-0.01],[x1, x1 + 0.01]]:

				x00, x01 = x

				fig.add_shape(
					type="rect", x0=x00, x1=x01, y0=y00, y1=y01,
					line=dict(color="black"),
					# fillcolor="white",
				)

				spacing = 50

				for y in np.arange(y01, y00-spacing, spacing):
				    fig.add_trace(go.Scatter(
				        x=[x01,x00], y=[y, y+spacing],
				        mode="lines", line=dict(color="black", width=1),
				        showlegend=False,
				        hoverinfo="skip",
				    ))

		# Shoe marker
		if not np.isnan(r["shoe_md_m"]):

			y = r["shoe_md_m"]

			# Coordinates of right-angle triangle (right-facing)

			for x in [[x0,x0-0.015],[x1,x1+0.015]]:

				x00, y00 = x[0], y
				x01, y01 = x[1], y
				x02, y02 = x[0], y - 50

				fig.add_shape(
					type="path",
					path=f"M {x00} {y00} L {x01} {y01} L {x02} {y02} Z",
					fillcolor="black",
					line=dict(color="black"),
				) 

		# Hanger marker
		# if not np.isnan(r["hanger_md_m"]):
		# 	fig.add_trace(go.Scatter(
		# 		x=[x1 + 0.05], y=[r["hanger_md_m"]],
		# 		mode="text", text=["Hanger →"], showlegend=False
		# 	))

		# Crossover marker
		# if not np.isnan(r["crossover_md_m"]):
		# 	fig.add_trace(go.Scatter(
		# 		x=[x0 - 0.05], y=[r["crossover_md_m"]],
		# 		mode="text", text=["← Crossover"], showlegend=False
		# 	))

	# Lane labels on top
	# for sid, lane in lanes.items():
	# 	fig.add_trace(go.Scatter(
	# 		x=[lane], y=[-50], mode="text",
	# 		text=[sid], showlegend=False
	# 	))

	# Axes / layout
	fig.update_layout(
		width=650,
		height=1000,
		autosize=True,
		showlegend=False,
		xaxis_title="",
		yaxis_title="Measured Depth (m)",
		yaxis=dict(autorange="reversed", zeroline=False, showgrid=True),
		xaxis=dict(zeroline=False, showgrid=False),
		margin=dict(l=40, r=40, t=60, b=40),
		template="plotly_white"
	)

	# # Tight x-range around lanes
	# fig.update_xaxes(range=[-0.5, 1])

	return fig

if __name__ == "__main__":

	import numpy as np

	data = [
		# well, string_id, segment_id, kind, section, top_md_m, bottom_md_m, outer_diam_in, inner_diam_in,
		# weight_lbft, grade, connection, hole_diam_in, cement_top_md_m, shoe_md_m, hanger_md_m, crossover_md_m, comments
		("GUN-142","COND-1", 1, "casing", "conductor",	0,   60, 20.0, 18.75,  94.0, "K55", "Welded", 26.0,   0,   60, np.nan, np.nan, "Conductor pipe"),
		("GUN-142","SURF-1", 1, "casing", "surface",	  0,  500, 13.375,12.347, 68.0, "K55", "Buttress",17.5, 100,  500, np.nan, np.nan, "Surface casing"),
		("GUN-142","INT-1",  1, "casing", "intermediate", 0, 1800, 9.625,  8.835, 47.0, "L80", "Buttress",12.25, 300, 1800, np.nan, np.nan, "Intermediate casing"),

		# Tapered production string: PRD-1 has two segments with different ODs in the SAME string
		("GUN-142","PRD-1",  2, "casing", "production",1800, 2900, 7.0,	6.366, 32.0, "P110","Premium", 8.5, 1300, 2900, np.nan, 1800,   "Lower tapered section (after crossover)"),

		# Liner hung below: smaller yet
		("GUN-142","LIN-1",  1, "liner",  "production",2900, 3600, 5.5,	4.950, 20.0, "P110","Premium", 6.0, np.nan, 3600, 2900, np.nan, "5-1/2\" liner hung at ~2900 m"),
	]

	cols = ["well","string_id","segment_id","kind","section","top_md_m","bottom_md_m",
		"outer_diam_in","inner_diam_in","weight_lbft","grade","connection","hole_diam_in",
		"cement_top_md_m","shoe_md_m","hanger_md_m","crossover_md_m","comments"]

	casing_df = pd.DataFrame(data, columns=cols)

	# Optional: enforce types you’ll likely rely on in extraction
	num_cols = ["segment_id","top_md_m","bottom_md_m","outer_diam_in","inner_diam_in",
				"weight_lbft","hole_diam_in","cement_top_md_m","shoe_md_m","hanger_md_m","crossover_md_m"]

	casing_df[num_cols] = casing_df[num_cols].apply(pd.to_numeric, errors="coerce")

	# Sanity checks (useful for extraction/modeling)
	assert (casing_df["bottom_md_m"] >= casing_df["top_md_m"]).all(), "bottom_md_m must be >= top_md_m"
	assert casing_df.sort_values(["outer_diam_in","bottom_md_m"], ascending=[False,True]).shape[0] == casing_df.shape[0]

	# casing_df.to_csv("output.csv", index=False) 

	fig = schematic(casing_df)

	fig.show()
