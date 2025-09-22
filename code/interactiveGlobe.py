# -*- coding: utf-8 -*-
"""
Visualize Sea Surface Temperature (SST) on a globe
"""


import xarray as xr
import numpy as np
import plotly.graph_objects as go

# === Load SST data ===
ds = xr.open_dataset("sst.day.mean.2024.nc")
sst = ds["sst"].isel(time=0)   # pick one day

lats = np.deg2rad(sst['lat'].values)   # convert to radians
lons = np.deg2rad(sst['lon'].values)
temps = sst.values

# === Convert to spherical coordinates ===
# Sphere radius
R = 1.0
lon2d, lat2d = np.meshgrid(lons, lats)

X = R * np.cos(lat2d) * np.cos(lon2d)
Y = R * np.cos(lat2d) * np.sin(lon2d)
Z = R * np.sin(lat2d)

# === Build interactive globe ===
fig = go.Figure()

fig.add_trace(go.Surface(
    x=X, y=Y, z=Z,
    surfacecolor=temps,
    colorscale="RdBu_r",
    cmin=-2, cmax=35,
    colorbar=dict(title="SST (degC)"),
    showscale=True
))

# Layout for globe view (center on Indian Ocean ~80°E, 0°N)
fig.update_layout(
    title="Sea Surface Temperature on 3D Globe (Indian Ocean centered)",
    scene=dict(
        xaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
        yaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
        zaxis=dict(showbackground=False, showgrid=False, showticklabels=False),
        aspectmode="data",
        camera=dict(eye=dict(x=2, y=1.5, z=1))  # adjust for Indian Ocean view
    )
)

fig.show()
