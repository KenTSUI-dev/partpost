import os
import numpy as np
import xarray as xr
import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString

# Map file extensions to Fiona/GDAL drivers
DRIVER_MAP = {
    ".shp": "ESRI Shapefile",
    ".gpkg": "GPKG",
    ".json": "GeoJSON",
    ".geojson": "GeoJSON",
    ".geojsonl": "GeoJSONSeq",
    ".sqlite": "SQLite",
    ".gml": "GML",
    ".kml": "KML",
}

def export_gdf(gdf, output_path):
    """
    Exports a GeoDataFrame to the specified file format based on extension.
    """
    ext = os.path.splitext(output_path)[1].lower()
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    print(f"💾 Saving to {output_path}...")

    # === Handle Tabular Formats ===
    if ext == ".csv":
        gdf.to_csv(output_path, index=False)
        print("✅ CSV saved.")
        return
    elif ext == ".xlsx":
        # Convert datetime objects to string for Excel to avoid timezone issues or formatting quirks
        df_copy = pd.DataFrame(gdf).copy()
        for col in df_copy.columns:
            if pd.api.types.is_datetime64_any_dtype(df_copy[col]):
                df_copy[col] = df_copy[col].astype(str)
        df_copy.to_excel(output_path, index=False)
        print("✅ Excel saved.")
        return

    # === Handle Spatial Formats ===
    driver = DRIVER_MAP.get(ext)

    if not driver:
        # Fallback: let geopandas guess or raise error
        print(f"⚠️ Unknown extension {ext}, attempting default save...")
        gdf.to_file(output_path)
        return

    # Special handling for Shapefiles (datetime to string)
    if driver == "ESRI Shapefile":
        # Create a shallow copy to modify columns without affecting original GDF
        gdf_export = gdf.copy()
        for col in gdf_export.columns:
            if pd.api.types.is_datetime64_any_dtype(gdf_export[col]):
                gdf_export[col] = gdf_export[col].astype(str)
        gdf_export.to_file(output_path, driver=driver)
    else:
        # KML usually requires specific libkml support in GDAL,
        # but standard KML driver works for simple geometries.
        gdf.to_file(output_path, driver=driver)

    print(f"✅ Saved successfully using driver: {driver}")

def ncTrk2line(nc_file, output_path, downscale_hours=1.0):
    """
    Convert a particle tracking NetCDF file into lines representing individual particles.

    Parameters
    ----------
    nc_file : str
        Path to the input NetCDF file.
    output_path : str
        Path to the output file (e.g., .shp, .gpkg, .geojson).
    downscale_hours : float, optional
        Time sampling interval in hours. Default is 1.0.
    """
    downscale_seconds = downscale_hours * 3600

    # === Load NetCDF ===
    if not os.path.isfile(nc_file):
        raise FileNotFoundError(f"NetCDF file not found: {nc_file}")
    ds = xr.open_dataset(nc_file, decode_times=True)
    print(f"📂 Loaded NetCDF: {os.path.basename(nc_file)}")

    # === Extract core variables ===
    lon = ds["particles_x_coordinate"]
    lat = ds["particles_y_coordinate"]
    time = ds["time"]
    fill_val = lon.attrs.get("_FillValue", -999.0)
    time_values = time.data

    # === Compute dataset temporal resolution ===
    if np.issubdtype(time_values.dtype, np.datetime64):
        dt_seconds = np.diff(time_values) / np.timedelta64(1, "s")
    else:
        # Handle cases where time might not be decoded to datetime64 automatically
        dt_seconds = np.diff([t.timestamp() for t in time_values])

    median_dt = float(np.median(dt_seconds))
    step = max(1, int(round(downscale_seconds / median_dt)))

    print(
        f"⏱ Native timestep ≈ {median_dt:.1f}s → downscaling every {step}-th record "
        f"(~{downscale_hours:.2f} hr interval)"
    )

    # === Downscale ===
    lon_sub = lon[::step, :].values.astype(float)
    lat_sub = lat[::step, :].values.astype(float)
    time_sub = pd.to_datetime(time_values[::step]).round("s")
    n_time, n_particles = lon_sub.shape
    print(f"📉 Downscaled dimensions: {n_time} timesteps × {n_particles} particles")

    # === Mask invalid values ===
    lon_sub[lon_sub == fill_val] = np.nan
    lat_sub[lat_sub == fill_val] = np.nan

    # === Build LineStrings per particle ===
    lines = []
    valid_pids = []
    times_start = []
    times_end = []

    for pid in range(n_particles):
        x = lon_sub[:, pid]
        y = lat_sub[:, pid]

        # Skip if all NaN
        if np.all(np.isnan(x)) or np.all(np.isnan(y)):
            continue

        coords = np.column_stack((x, y))
        mask = np.isfinite(coords).all(axis=1)
        coords = coords[mask]

        if len(coords) > 1:  # need at least two points to form a line
            lines.append(LineString(coords))
            valid_pids.append(pid)
            times_start.append(pd.to_datetime(time_sub[mask][0]).round("s"))
            times_end.append(pd.to_datetime(time_sub[mask][-1]).round("s"))

    print(f"🛠 Created {len(lines)} valid particle tracks")

    if not lines:
        print("⚠️ No valid particle tracks found. Skipping export.")
        return None

    # === Create GeoDataFrame ===
    gdf = gpd.GeoDataFrame(
        {
            "par_id": valid_pids,
            "time_start": pd.to_datetime(times_start).astype("datetime64[ns]"),
            "time_end": pd.to_datetime(times_end).astype("datetime64[ns]"),
        },
        geometry=lines,
        crs="EPSG:4326",
    )

    # === Export ===
    export_gdf(gdf, output_path)
    return gdf

def ncTrk2pt(nc_file, output_path, downscale_hours=1.0):
    """
    Convert a particle tracking NetCDF file to a downscaled point file.

    Parameters
    ----------
    nc_file : str
        Path to the input NetCDF file.
    output_path : str
        Path to the output file (e.g., .shp, .gpkg, .csv).
    downscale_hours : float, optional
        Time sampling interval in hours. Default is 1.0.
    """
    downscale_seconds = downscale_hours * 3600

    # === Load NetCDF ===
    if not os.path.isfile(nc_file):
        raise FileNotFoundError(f"NetCDF file not found: {nc_file}")
    ds = xr.open_dataset(nc_file, decode_times=True)
    print(f"📂 Loaded NetCDF: {os.path.basename(nc_file)}")

    # === Extract coordinate variables ===
    lon = ds["particles_x_coordinate"]
    lat = ds["particles_y_coordinate"]
    time = ds["time"]
    fill_val = lon.attrs.get("_FillValue", -999.0)

    # === Get decoded time values ===
    time_values = time.data

    # === Determine sampling step ===
    if np.issubdtype(time_values.dtype, np.datetime64):
        time_diffs = np.diff(time_values) / np.timedelta64(1, "s")
    else:
        time_diffs = np.diff([t.timestamp() for t in time_values])

    median_dt = float(np.median(time_diffs))
    step = max(1, int(round(downscale_seconds / median_dt)))
    print(
        f"⏱ Native timestep ≈ {median_dt:.1f}s → downscaling every {step}-th record "
        f"(~{downscale_hours:.2f} hr interval)"
    )

    # === Downscale ===
    lon_sub = lon[::step, :].values.astype(float)
    lat_sub = lat[::step, :].values.astype(float)
    time_sub = pd.to_datetime(time_values[::step]).round("s")
    n_time, n_particles = lon_sub.shape
    print(f"📉 Downscaled to {n_time} timesteps × {n_particles} particles")

    # === Mask invalid values ===
    lon_sub[lon_sub == fill_val] = np.nan
    lat_sub[lat_sub == fill_val] = np.nan
    valid_mask = np.isfinite(lon_sub) & np.isfinite(lat_sub)

    # === Flatten arrays and build table ===
    rows, cols = np.where(valid_mask)
    x = lon_sub[rows, cols]
    y = lat_sub[rows, cols]
    pids = cols.astype(int)
    t_vals = pd.to_datetime(time_sub[rows]).astype("datetime64[ns]")

    print(f"🛠 Preparing {len(x)} valid point records")

    if len(x) == 0:
        print("⚠️ No valid points found. Skipping export.")
        return None

    # === Create GeoDataFrame ===
    df = pd.DataFrame({
        "par_id": pids,
        "time": t_vals,
        "lon": x,
        "lat": y
    })

    gdf = gpd.GeoDataFrame(
        df[["par_id", "time"]],
        geometry=gpd.points_from_xy(df.lon, df.lat),
        crs="EPSG:4326"
    )

    # === Export ===
    export_gdf(gdf, output_path)
    return gdf
