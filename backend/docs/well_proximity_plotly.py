import numpy as np
import pandas as pd
import itertools
import plotly.graph_objects as go
import plotly.express as px
import plotly.io as pio
import argparse
from pathlib import Path

from wellx import Well

def load_surveys(path: str, sheet: str | None = None, colmap: dict | None = None) -> pd.DataFrame:
	"""
	Load well survey table from CSV or Excel.
	Required logical columns: well, MD, TVD, X, Y.
	You can pass a colmap to map your actual column names to these keys.
	"""
	path = Path(path)
	if path.suffix.lower() in {".xlsx", ".xls"}:
		df = pd.read_excel(path, sheet_name=sheet or 0)
	else:
		df = pd.read_csv(path)

	df.columns = [c.strip() for c in df.columns]

	if colmap is None:
		candidates = {
			'well': ['well','Well','WELL','WELL_NAME'],
			'MD':   ['MD','Md','measured_depth','MD_m','MD (m)'],
			'TVD':  ['TVD','Tvd','TVD_m','TVD (m)','Z','Depth'],
			'X':	['X','E','East','EAST','EASTING'],
			'Y':	['Y','N','North','NORTH','NORTHING'],
		}
		colmap = {}
		for k, opts in candidates.items():
			for o in opts:
				if o in df.columns:
					colmap[k] = o
					break

	required = ['well','MD','TVD','X','Y']
	missing = [k for k in required if k not in colmap]
	if missing:
		raise ValueError(f"Missing column mappings for: {missing}")

	sdf = df[[colmap['well'], colmap['MD'], colmap['TVD'], colmap['X'], colmap['Y']]].copy()
	sdf.columns = ['well','MD','TVD','X','Y']
	for c in ['MD','TVD','X','Y']:
		sdf[c] = pd.to_numeric(sdf[c], errors='coerce')
	sdf = sdf.dropna(subset=['well','MD','TVD','X','Y'])
	return sdf.sort_values(['well','MD']).reset_index(drop=True)

def build_wells(df: pd.DataFrame):
	wells = {}
	for w, g in df.groupby('well', sort=False):
		wells[w] = (g['X'].to_numpy(), g['Y'].to_numpy(), g['TVD'].to_numpy())
	return wells



if __name__ == "__main__":

	import pandas as pd

	from wellx.items import Survey

	survey = pd.read_csv("G:\\My Drive\\Modeling Repository\\01_Well_Data_Streaming_(WellStream)\\db\\trj\\141.txt",sep=r'\s+')
	s2 = pd.read_csv("G:\\My Drive\\Modeling Repository\\01_Well_Data_Streaming_(WellStream)\\db\\trj\\142.txt",sep=r'\s+')

	survey['X'],survey['Y'],_ = Survey.minimum_curvature(
		survey['MD'].to_numpy(),
		survey['INCL'].to_numpy(),
		survey['AZ'].to_numpy()
		)

	print(s2)

	s2['X'],s2['Y'],_ = Survey.minimum_curvature(
		s2['MD'].to_numpy(),
		s2['INCL'].to_numpy(),
		s2['AZ'].to_numpy()
		)

	# df = load_surveys("surveys_template.csv")

	# wells = build_wells(survey)

	fig3d = proximity_plot_3d(survey,s2)

	fig3d.show()