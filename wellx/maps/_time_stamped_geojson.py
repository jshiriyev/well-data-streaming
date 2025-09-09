from folium.plugins import TimestampedGeoJson

import pandas as pd

def TimeStampedGeojson(wells:pd.DataFrame,rates:pd.DataFrame,color:str,**kwargs):
    """
    If df has a 'stamps' column (list of ISO date strings) it will be used verbatim.
    Otherwise, stamps are generated monthly from 'start' to 'end' (inclusive).
    Each stamp is emitted as its own Feature with a single 'time' (not 'times').
    
    """
    # def norm(s):
    #     # strict -> raise on bad; normalize to full ISO, Zulu
    #     return (pd.to_datetime(str(s).strip(), errors="raise")
    #               .strftime("%Y-%m-%d"))

    date_keys = sorted(rates["date"].dt.strftime("%Y-%m-01").unique().tolist())
    date_to_idx = {d:i for i,d in enumerate(date_keys)}

    # For each well, store list of date indices where that well has data
    idxs_by_well = (
        rates
          .assign(date_idx=lambda d: d["date"].dt.strftime("%Y-%m-01").map(date_to_idx))
          .groupby("well")["date_idx"]
          .apply(lambda s: sorted(set(int(x) for x in s if pd.notnull(x))))
          .to_dict()
    )

    features = []

    rate_wells = rates.well.unique().tolist()
    rate_dates = rates.date.unique()

    for index, r in wells.iterrows():

        if r['well'] in rate_wells:
        
            stamps = rate_dates[idxs_by_well[r['well']]].strftime("%Y-%m-%d").tolist()

            # clean = sorted({ norm(s) for s in stamps })
            # one feature per stamp with a single 'time'
            for s in stamps:
                features.append({
                    "type": "Feature",
                    "geometry": {"type": "Point", "coordinates": [r["lon"], r["lat"]]},
                    "properties": {
                        "time": s, # 👈 single instant only
                        "popup": f'{r["well"]}',
                        "icon": "circle",
                        "iconstyle": {
                            "fillColor": color, "fillOpacity": 0.8,
                            "stroke": "false", "radius": 7
                        },
                        "style": {"color": color}
                    },
                })

    return TimestampedGeoJson(
        {"type": "FeatureCollection", "features": features},
        period="P1M",               # monthly frames on the slider
        transition_time=200,
        duration="PT1S",
        add_last_point=False,
        auto_play=False,
        loop=False,
        loop_button=False,
        date_options="DD-MM-YYYY",
        time_slider_drag_update=False,
        **kwargs
    )