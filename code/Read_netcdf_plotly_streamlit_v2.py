# -*- coding: utf-8 -*-
# streamlit_app.py
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import xarray as xr

# === Page configuration ===
st.set_page_config(page_title="Ocean Data Viewer", layout="wide")

# === File paths ===
file1 = "sst.day.mean.2024.nc"
file2 = "bathymetry.nc"


# === Load datasets with caching ===
@st.cache_data
def load_datasets():
    ds1 = xr.open_dataset(file1)
    ds2 = xr.open_dataset(file2)
    return ds1, ds2


ds1, ds2 = load_datasets()

# Extract coordinates and variables
lat = ds1["lat"].values
lon = ds1["lon"].values
time_vals = ds1["time"].values
sst = ds1["sst"]

# Handle standard NetCDF missing/fill values
missing_val = sst.attrs.get(
    "missing_value", sst.attrs.get("_FillValue", -9.969209968386869e36)
)
sst = sst.where(sst != missing_val)

# === Sidebar controls ===
st.sidebar.title("Controls")
dates = [str(d)[:10] for d in time_vals]
date_str = st.sidebar.selectbox("Select Date", dates, index=0)
date_sel = np.datetime64(date_str)

# Slice and squeeze out any singleton dimensions
sst_slice = sst.sel(time=date_sel).squeeze()

# === Bathymetry setup ===
bath = ds2["bathymetry"].squeeze()

# Decimate bathymetry for smoother rendering if grid resolution is high
bath_step = max(1, len(bath["lat"]) // 360)
bath_sub = bath.isel(lat=slice(None, None, bath_step), lon=slice(None, None, bath_step))

# === Plot SST with bathymetry contour ===
fig = px.imshow(
    sst_slice.values,
    origin="lower",
    x=lon,
    y=lat,
    color_continuous_scale="RdBu_r",
    labels={"color": "SST (deg C)"},
    aspect="auto",
    zmin=-2,
    zmax=35,
)

fig.update_layout(
    title=f"Sea Surface Temperature on {date_str}",
    xaxis_title="Longitude",
    yaxis_title="Latitude",
    margin=dict(l=20, r=20, t=50, b=20),
)

# Overlay coastline (bathymetry = 0 m contour)
fig.add_trace(
    go.Contour(
        z=bath_sub.values,
        x=bath_sub["lon"].values,
        y=bath_sub["lat"].values,
        contours=dict(start=0, end=0, size=1, coloring="none"),
        line=dict(color="black", width=1.2),
        showscale=False,
        name="Coastline",
        hoverinfo="skip",
    )
)

# === Render in Streamlit ===
st.plotly_chart(fig, use_container_width=True)
