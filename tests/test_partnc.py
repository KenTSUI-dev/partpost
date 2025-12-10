from partpost.proc import ncTrk2line, ncTrk2pt, export_gdf

if __name__ == "__main__":
    nc_file = r"D:\temp\319_WQMD_WQMG_Marine_Refuse_Tracking\20250922\marine-refuse_trk.nc"
    output_shp = r"D:\temp\319_WQMD_WQMG_Marine_Refuse_Tracking\20250922\20250922_MRCAS_points.shp"
    output_line_shp = r"D:\temp\319_WQMD_WQMG_Marine_Refuse_Tracking\20250922\20250922_MRCAS_lines.shp"

    nc_file = r"D:\temp\319_WQMD_WQMG_Marine_Refuse_Tracking\20240405\marine-refuse_trk.nc"
    output_shp = r"D:\temp\319_WQMD_WQMG_Marine_Refuse_Tracking\20240405\20240405_MRCAS_points.shp"
    output_line_shp = r"D:\temp\319_WQMD_WQMG_Marine_Refuse_Tracking\20240405\20240405_MRCAS_lines.shp"
    # downscale_seconds = 1800 → every 30 mins; 3600 → every 1 hour
    ncTrk2pt(nc_file, output_shp, downscale_hours=1)
    ncTrk2line(nc_file, output_line_shp, downscale_hours=1)