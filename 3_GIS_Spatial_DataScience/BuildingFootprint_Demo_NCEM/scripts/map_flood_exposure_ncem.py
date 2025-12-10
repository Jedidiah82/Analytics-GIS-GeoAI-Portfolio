import os
import geopandas as gpd
import matplotlib.pyplot as plt
import contextily as ctx
from matplotlib_scalebar.scalebar import ScaleBar
from shapely.geometry import box
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D


BUILDINGS_CLEAN_PATH = "data_clean/buildings_cleaned.gpkg"
FLOOD_BUILDINGS_PATH = "hazards/buildings_in_floodzones.gpkg"
FLOOD_POLY_PATH = "hazards/flood_fema_nfhl.gpkg"
OUTPUT_PNG = "figures/flood_exposure_map_ncem.png"
OUTPUT_PDF = "figures/flood_exposure_map_ncem.pdf"

# Your AOI name for title
COUNTY_NAME = "Wake County, NC"


def main():
    print("[*] Loading buildings and flood layers...")

    if not os.path.exists(BUILDINGS_CLEAN_PATH):
        raise FileNotFoundError(f"Missing {BUILDINGS_CLEAN_PATH}")
    if not os.path.exists(FLOOD_BUILDINGS_PATH):
        raise FileNotFoundError(f"Missing {FLOOD_BUILDINGS_PATH}")
    if not os.path.exists(FLOOD_POLY_PATH):
        raise FileNotFoundError(f"Missing {FLOOD_POLY_PATH}")

    # All cleaned buildings (AOI)
    buildings_all = gpd.read_file(BUILDINGS_CLEAN_PATH)

    # Buildings intersecting flood zones
    flooded_buildings = gpd.read_file(FLOOD_BUILDINGS_PATH)

    # FEMA flood polygons
    flood_polys = gpd.read_file(FLOOD_POLY_PATH)

    print("[*] Reprojecting to Web Mercator (EPSG:3857)...")
    target_crs = "EPSG:3857"
    if buildings_all.crs is None:
        raise ValueError("buildings_cleaned.gpkg has no CRS; please set one in GIS.")

    buildings_all = buildings_all.to_crs(target_crs)
    flooded_buildings = flooded_buildings.to_crs(target_crs)
    flood_polys = flood_polys.to_crs(target_crs)

    # Define AOI extent (buffer around flooded buildings or all buildings)
    if len(flooded_buildings) > 0:
        aoi_bounds = flooded_buildings.total_bounds  # [minx, miny, maxx, maxy]
    else:
        aoi_bounds = buildings_all.total_bounds

    minx, miny, maxx, maxy = aoi_bounds
    # Buffer by 5% for nicer framing
    dx = maxx - minx
    dy = maxy - miny
    minx -= dx * 0.05
    maxx += dx * 0.05
    miny -= dy * 0.05
    maxy += dy * 0.05

    bbox = box(minx, miny, maxx, maxy)

    # Clip layers to AOI bbox (for faster plotting)
    buildings_clip = buildings_all[buildings_all.intersects(bbox)]
    flooded_clip = flooded_buildings[flooded_buildings.intersects(bbox)]
    flood_clip = flood_polys[flood_polys.intersects(bbox)]

    print("[*] Creating NCEM-style map...")
    fig, ax = plt.subplots(1, 1, figsize=(10, 10), dpi=300)

    # Plot FEMA flood polygons (light blue)
    if len(flood_clip) > 0:
        flood_clip.plot(
            ax=ax,
            facecolor="#7fbfff",
            edgecolor="#2b7bb9",
            alpha=0.3,
            linewidth=0.5,
            zorder=1,
        )

    # Plot all buildings (background)
    if len(buildings_clip) > 0:
        buildings_clip.plot(
            ax=ax,
            color="#b3b3b3",
            markersize=1,
            linewidth=0.1,
            zorder=2,
        )

    # Plot flooded buildings (on top)
    if len(flooded_clip) > 0:
        flooded_clip.plot(
            ax=ax,
            color="#d73027",
            markersize=2,
            linewidth=0.1,
            zorder=3,
        )

    # Basemap
    print("[*] Adding basemap...")
    # Choose an NCEM-style basemap
    basemap = ctx.providers.CartoDB.Voyager # clean, modern look
    # Alternative options:
    # basemap = ctx.providers.Esri.WorldGrayCanvas
    # basemap = ctx.providers.OpenStreetMap.Mapnik

    ctx.add_basemap(
        ax,
        crs=target_crs,
        source=basemap,
        alpha=0.8,
        zorder=0,
    )

    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)
    ax.set_axis_off()

    # Title & subtitle
    ax.set_title(
        f"{COUNTY_NAME} — Building Exposure in FEMA Flood Zones\n"
        "Demo Analysis — Not for Operational Use",
        fontsize=12,
        fontweight="bold",
        loc="left",
    )

    # North arrow
    print("[*] Adding north arrow and scalebar...")
    ax.annotate(
        "N",
        xy=(0.95, 0.15),
        xytext=(0.95, 0.25),
        arrowprops=dict(facecolor="black", width=2, headwidth=8),
        ha="center",
        va="center",
        fontsize=10,
        xycoords=ax.transAxes,
    )

    # Scalebar (1 unit = 1 meter in EPSG:3857)
    scalebar = ScaleBar(
        dx=1,
        units="m",
        dimension="si-length",
        location="lower left",
        box_alpha=0.7,
        pad=0.5,
    )
    ax.add_artist(scalebar)

    # Custom legend (no relying on collections)
    legend_handles = []

    legend_handles.append(
        mpatches.Patch(
            facecolor="#7fbfff", edgecolor="#2b7bb9", alpha=0.4, label="FEMA Flood Zone"
        )
    )
    legend_handles.append(
        Line2D(
            [0],
            [0],
            marker="s",
            color="w",
            markerfacecolor="#b3b3b3",
            markersize=6,
            label="All Buildings",
        )
    )
    legend_handles.append(
        Line2D(
            [0],
            [0],
            marker="s",
            color="w",
            markerfacecolor="#d73027",
            markersize=6,
            label="Buildings in Flood Zone",
        )
    )

    ax.legend(
        handles=legend_handles,
        loc="upper right",
        frameon=True,
        framealpha=0.9,
        fontsize=8,
        title="Legend",
    )

    # Attribution
    fig.text(
        0.01,
        0.01,
        "Data: Microsoft Building Footprints, FEMA NFHL | Map: Godwin E. Akpan (Demo)",
        fontsize=6,
    )

    # Ensure figures/ exists
    os.makedirs("figures", exist_ok=True)

    print(f"[*] Saving map to {OUTPUT_PNG} and {OUTPUT_PDF}...")
    plt.savefig(OUTPUT_PNG, bbox_inches="tight", dpi=300)
    plt.savefig(OUTPUT_PDF, bbox_inches="tight")
    plt.close()

    print("[SUCCESS] NCEM-style flood exposure map created.")


if __name__ == "__main__":
    main()
