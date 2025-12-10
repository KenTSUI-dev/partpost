# partpost

**partpost** is a specialized CLI tool designed to process Delft3D FM Particle Tracking output NetCDF files. It allows users to export particle track data to various spatial and tabular formats.

## Supported Formats

- **Spatial:** ESRI Shapefile (`.shp`), GPKG (`.gpkg`), GeoJSON (`.json`, `.geojson`), GeoJSONSeq (`.geojsonl`), SQLite (`.sqlite`), GML (`.gml`), KML (`.kml`)
- **Tabular:** CSV (`.csv`), Excel (`.xlsx`)

## Installation

You can install `partpost` using Conda.

### Option 1: Create a new environment

This is the recommended approach to avoid conflicts.

1.  Ensure you have `conda` installed (e.g., Anaconda or Miniconda).
2.  Navigate to the directory containing `environment.yml`.
3.  Run the following command:

    ```bash
    conda env create -f environment.yml
    ```

4.  Activate the environment:

    ```bash
    conda activate partpost
    ```

### Option 2: Install into an existing environment

If you already have a working environment and want to add `partpost` to it:

1.  Activate your environment:
    ```bash
    conda activate my_env
    ```
2.  Install the required dependencies (if not already present):
    ```bash
    conda install -c conda-forge netcdf4 xarray dask bottleneck geopandas openpyxl
    ```
3.  Install the package in editable mode:
    ```bash
    pip install -e .
    ```


## Usage

The tool runs via the command line using a JSON configuration file.

```bash
partpost config.json

```

### Configuration File (`config.json`)

The configuration file can contain a single task object, or a list of task objects.

**Example `config.json`:**

```json
[
  {
    "input_nc": "D:/model_output/marine-refuse_trk.nc",
    "output_path": "D:/gis_data/particles_hourly.shp",
    "mode": "point",
    "downscale_hour": 1.0
  },
  {
    "input_nc": "D:/model_output/marine-refuse_trk.nc",
    "output_path": "D:/gis_data/tracks_summary.gpkg",
    "mode": "line",
    "downscale_hour": 2.0
  },
  {
    "input_nc": "D:/model_output/marine-refuse_trk.nc",
    "output_path": "D:/gis_data/particles_raw.csv",
    "mode": "point",
    "downscale_hour": 0.5
  }
]

```

### Parameters

| Parameter | Type | Description |
| --- | --- | --- |
| `input_nc` | string | Absolute path to the input NetCDF file. |
| `output_path` | string | Absolute path to the output file. The format is determined by the file extension (e.g., `.shp`, `.gpkg`, `.csv`). |
| `mode` | string | `point` for instantaneous locations, `line` for particle tracks. |
| `downscale_hour` | float | Time sampling interval in hours. Default is `1.0`. Use `0.5` for 30 minutes. |

### Notes on Shapefiles
When exporting to ESRI Shapefile format, partpost explicitly converts all datetime fields to strings. This prevents compatibility issues with GIS software that may not correctly interpret Shapefile date/time fields.