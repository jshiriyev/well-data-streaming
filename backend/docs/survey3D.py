import numpy as np
import plotly.graph_objects as go

# --- Mock trajectories ---
depth = np.linspace(0, 3000, 50)

def make_traj(x0, y0, azim_deg, kick_off=1000, build_rate=3):
    x, y, z = [x0], [y0], [0]
    for d in depth[1:]:
        if d < kick_off:
            x.append(x0); y.append(y0)
        else:
            ang = np.radians(azim_deg)
            step = (d - kick_off)/200 * build_rate
            x.append(x0 + step*np.cos(ang))
            y.append(y0 + step*np.sin(ang))
        z.append(d)
    return np.array(x), np.array(y), np.array(z)

wells = {
    "Well-A": make_traj(0, 0, 0),
    "Well-B": make_traj(50, 0, 90),
    "Well-C": make_traj(-30, -30, 45),
}

# --- Find minimum distances ---
def min_dist(w1, w2):
    x1,y1,z1 = w1; x2,y2,z2 = w2
    dmin = 1e9; pair = None
    for i in range(len(z1)):
        for j in range(len(z2)):
            d = np.sqrt((x1[i]-x2[j])**2 + (y1[i]-y2[j])**2 + (z1[i]-z2[j])**2)
            if d < dmin:
                dmin = d; pair = (x1[i],y1[i],z1[i], x2[j],y2[j],z2[j])
    return dmin, pair

pairs = [("Well-A","Well-B"), ("Well-A","Well-C"), ("Well-B","Well-C")]
closest = {p: min_dist(wells[p[0]], wells[p[1]]) for p in pairs}

# --- Build 3D figure ---
fig = go.Figure()

# Well trajectories
for name, (x,y,z) in wells.items():
    fig.add_trace(go.Scatter3d(
        x=x, y=y, z=z, mode="lines",
        name=name, hovertemplate=f"{name}<br>East:%{{x:.1f}}<br>North:%{{y:.1f}}<br>Depth:%{{z:.0f}}"
    ))

# Closest approach lines
for (w1,w2), (dmin, (x1,y1,z1,x2,y2,z2)) in closest.items():
    fig.add_trace(go.Scatter3d(
        x=[x1,x2], y=[y1,y2], z=[z1,z2],
        mode="lines+text", line=dict(dash="dash"),
        text=[None, f"{w1}–{w2}: {dmin:.1f} m"],
        textposition="top center", showlegend=False
    ))

fig.update_layout(
    title="Well Proximity Plot (3D, interactive)",
    scene=dict(
        xaxis_title="East (m)", yaxis_title="North (m)", zaxis_title="Depth (m)",
        zaxis=dict(autorange="reversed")  # depth increases downward
    ),
    margin=dict(l=0, r=0, b=0, t=40)
)

fig.show()
