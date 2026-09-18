# -*- coding: utf-8 -*-
# streamlit_app.py
import io
import time
import imageio
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import xarray as xr
from PIL import Image

st.set_page_config(page_title="Ocean Data Viewer", layout="wide")

file1 = "sst.day.mean.2024.nc"
file2 = "bathymetry.nc"


@st.cache_data
def load_datasets():
    ds1 = xr.open_dataset(file1)
    ds2 = xr.open_dataset(file2)
    return ds1, ds2


ds1, ds2 = load_datasets()

lat = ds1["lat"].values
lon = ds1["lon"].values
time_vals = ds1["time"].values
sst = ds1["sst"]

# Handle NetCDF fill/missing values
missing_val = sst.attrs.get(
    "missing_value", sst.attrs.get("_FillValue", -9.969209968386869e36)
)
sst = sst.where(sst != missing_val)

# Prepare coastline contour
bath = ds2["bathymetry"].squeeze()
bath_step = max(1, len(bath["lat"]) // 360)
bath_sub = bath.isel(lat=slice(None, None, bath_step), lon=slice(None, None, bath_step))

# === Precompute Sphere Coordinates for 3D Globe ===
# Subsample grid for responsive 3D rendering
globe_stride_lat = max(1, len(lat) // 90)
globe_stride_lon = max(1, len(lon) // 180)

lat_globe = lat[::globe_stride_lat]
lon_globe = lon[::globe_stride_lon]

# Convert lon (0 to 360 or -180 to 180) and lat to radians
phi = np.radians(lat_globe)
theta = np.radians(lon_globe)
theta_grid, phi_grid = np.meshgrid(theta, phi)

# Parametric equations of a unit sphere
R = 1.0
x_sphere = R * np.cos(phi_grid) * np.cos(theta_grid)
y_sphere = R * np.cos(phi_grid) * np.sin(theta_grid)
z_sphere = R * np.sin(phi_grid)


# === Helper: Generate GIF bytes ===
def generate_gif(sst_data, dates_list, step=10, fps=5):
    """Generates an animated GIF in memory using Plotly static frames."""
    images = []
    indices = list(range(0, len(dates_list), step))

    progress_bar = st.sidebar.progress(0)
    status_text = st.sidebar.empty()

    for idx_i, idx in enumerate(indices):
        status_text.text(f"Rendering frame {idx_i + 1}/{len(indices)}...")
        frame = sst_data.isel(time=idx).squeeze().values

        fig_frame = px.imshow(
            frame,
            origin="lower",
            x=lon,
            y=lat,
            color_continuous_scale="RdBu_r",
            zmin=-2,
            zmax=35,
        )
        fig_frame.update_layout(
            title=f"SST - {dates_list[idx]}",
            margin=dict(l=10, r=10, t=40, b=10),
            xaxis=dict(showticklabels=False),
            yaxis=dict(showticklabels=False),
        )

        # Convert figure to static PNG bytes (requires kaleido: pip install kaleido)
        # If kaleido is unavailable, falls back to raw PIL drawing
        try:
            img_bytes = fig_frame.to_image(format="png", width=600, height=350)
            images.append(imageio.imread(img_bytes))
        except Exception:
            # Fallback: Normalize SST array to an 8-bit heatmap directly
            norm_frame = np.clip((frame - (-2)) / (35 - (-2)), 0, 1)
            norm_frame = np.nan_to_num(norm_frame, nan=0.0)
            img_arr = (norm_frame * 255).astype(np.uint8)
            img = Image.fromarray(np.flipud(img_arr)).resize((600, 350))
            images.append(np.array(img))

        progress_bar.progress((idx_i + 1) / len(indices))

    status_text.empty()
    progress_bar.empty()

    gif_buffer = io.BytesIO()
    imageio.mimsave(gif_buffer, images, format="GIF", fps=fps, loop=0)
    return gif_buffer.getvalue()


# === Sidebar Controls ===
st.sidebar.title("Navigation & Time")
dates = [str(d)[:10] for d in time_vals]

selected_idx = st.sidebar.slider("Select Time Step", 0, len(dates) - 1, value=0)
current_date = dates[selected_idx]
st.sidebar.write(f"**Selected Date:** {current_date}")

play = st.sidebar.checkbox("Auto-play Timeline")

# === Sidebar GIF Exporter ===
st.sidebar.markdown("---")
st.sidebar.subheader("Export Animation")
gif_stride = st.sidebar.slider("Sample interval (days)", 1, 30, 7)
gif_fps = st.sidebar.slider("GIF Frame Rate (FPS)", 1, 15, 5)

if st.sidebar.button("Generate GIF File"):
    with st.spinner("Compiling GIF frames..."):
        gif_data = generate_gif(sst, dates, step=gif_stride, fps=gif_fps)
        st.sidebar.success("GIF Generated Successfully!")
        st.sidebar.download_button(
            label="Download SST Animation GIF",
            data=gif_data,
            file_name=f"sst_animation_2024.gif",
            mime="image/gif",
        )

# === Slicing Current Display Frame ===
sst_frame = sst.isel(time=selected_idx).squeeze()
stride_2d = max(1, len(lat) // 360)
sst_plot = sst_frame.isel(lat=slice(None, None, stride_2d), lon=slice(None, None, stride_2d))

# === Main Interface Tabs ===
tab1, tab2 = st.tabs(["2D Scaled Map", "3D Interactive Globe"])

with tab1:
    # 2D Map with correct geographical scale
    fig_2d = px.imshow(
        sst_plot.values,
        origin="lower",
        x=sst_plot["lon"].values,
        y=sst_plot["lat"].values,
        color_continuous_scale="RdBu_r",
        labels={"color": "SST (deg C)"},
        zmin=-2,
        zmax=35,
    )

    fig_2d.add_trace(
        go.Contour(
            z=bath_sub.values,
            x=bath_sub["lon"].values,
            y=bath_sub["lat"].values,
            contours=dict(start=0, end=0, size=1, coloring="none"),
            line=dict(color="black", width=1.0),
            showscale=False,
            name="Coastline",
            hoverinfo="skip",
        )
    )

    fig_2d.update_layout(
        title=f"Sea Surface Temperature (2D) - {current_date}",
        xaxis=dict(
            title="Longitude",
            range=[float(np.min(lon)), float(np.max(lon))],
            constrain="domain",
        ),
        yaxis=dict(
            title="Latitude",
            range=[float(np.min(lat)), float(np.max(lat))],
            scaleanchor="x",
            scaleratio=1,
        ),
        margin=dict(l=20, r=20, t=40, b=20),
        height=620,
    )

    st.plotly_chart(fig_2d, use_container_width=True)

with tab2:
    # 3D Globe Projection
    sst_globe = (
        sst_frame.isel(
            lat=slice(None, None, globe_stride_lat),
            lon=slice(None, None, globe_stride_lon),
        )
        .values
    )

    fig_globe = go.Figure(
        data=[
            go.Surface(
                x=x_sphere,
                y=y_sphere,
                z=z_sphere,
                surfacecolor=sst_globe,
                colorscale="RdBu_r",
                cmin=-2,
                cmax=35,
                colorbar=dict(title="SST (deg C)", len=0.7),
                hoverinfo="none",
            )
        ]
    )

    fig_globe.update_layout(
        title=f"Sea Surface Temperature (3D Globe) - {current_date}",
        scene=dict(
            xaxis=dict(showbackground=False, showgrid=False, zeroline=False, visible=False),
            yaxis=dict(showbackground=False, showgrid=False, zeroline=False, visible=False),
            zaxis=dict(showbackground=False, showgrid=False, zeroline=False, visible=False),
            aspectmode="data",
            camera=dict(eye=dict(x=1.6, y=1.6, z=0.8)),
        ),
        margin=dict(l=10, r=10, t=40, b=10),
        height=650,
    )

    st.plotly_chart(fig_globe, use_container_width=True)

# Auto-play loop
if play and selected_idx < len(dates) - 1:
    time.sleep(0.15)
    st.experimental_rerun() if hasattr(st, "experimental_rerun") else st.rerun()