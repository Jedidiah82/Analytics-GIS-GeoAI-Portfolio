![GIS](https://img.shields.io/badge/GIS-ArcGIS%20Pro-blue)
![Python](https://img.shields.io/badge/Python-GeoPandas-green)
![Project Status](https://img.shields.io/badge/Status-Planned-yellow)


# 🏠 Automated Building Exposure Pipeline — NC Emergency Management (NCEM) Use-Case
_A Python-based GeoAI workflow for extracting, validating, and modeling hazard exposure for critical infrastructure._

This project presents a completed portfolio demonstration of a reproducible GIS workflow for acquiring, cleaning, validating and analysing building footprints for flood-hazard exposure assessment in Wake County, North Carolina. It simulates spatial data-engineering methods relevant to emergency-management and infrastructure-resilience applications. It was not commissioned by NC Emergency Management and is not intended for operational use.

---

## 🎯 Project Purpose
To build a reproducible workflow for:

1. Acquiring building footprint data from open sources  
2. Cleaning and validating geometry using GIS and Python  
3. Applying spatial QA/QC controls  
4. Modeling hazard exposure using flood, surge, wildfire, and tornado datasets  

This will serve as a portfolio-ready NCEM use-case demonstration.

---

## 🛠️ Planned Data Sources

| Dataset | Description | Source |
|---------|-------------|--------|
| **Microsoft US Building Footprints** | High-accuracy building polygons | https://github.com/microsoft/USBuildingFootprints |
| **OpenStreetMap Buildings** | Crowd-sourced footprints | https://osmdata.openstreetmap.de |
| **NAIP Imagery** | Visual QA/QC | USDA NRCS |
| **Landsat / Sentinel-2** | Land cover validation | USGS / ESA |
| **LiDAR (Optional)** | Deriving building heights | NC Spatial Data Portal |

---

## 📌 Planned Workflow

### **1. Data Acquisition**
- Select a North Carolina county AOI (Wake, Johnston, Brunswick, etc.)  
- Download Microsoft/OSM footprints  
- Load datasets in ArcGIS Pro, QGIS, or Python  

---

### **2. Data Cleaning**
Planned GIS/Python cleaning includes:

- Removing sliver polygons  
- Dissolving multipart buildings  
- Standardizing fields: `bldg_id`, `stories_est`, etc.  
- Removing artifacts <20–30 m²  
- Computing area and perimeter fields  

---

### **3. Spatial QA/QC**
Quality checks will include:

- Validating geometry  
- Checking overlaps with hydrology and roads  
- Identifying improbable shapes  
- Comparing target tiles with NAIP imagery  

Deliverables:
- `buildings_qaqc_report.md`  
- Before/after screenshots  

---

### **4. Hazard Exposure Analysis**
Cleaned footprints will be intersected with:

| Hazard | Dataset |
|--------|---------|
| **Flood Zones** | FEMA NFHL |
| **Storm Surge** | NOAA SLOSH |
| **Wildfire Risk** | NC Forest Service |
| **Tornado Tracks** | NOAA SPC |

Expected outputs:

- % of buildings in hazard zones  
- Exposure heatmaps  
- Statistics by census tract or county  

---

## 🧪 Example Python Snippet (Planned)

```python
import geopandas as gpd

# Load raw footprints
buildings = gpd.read_file("data_raw/microsoft_footprints.geojson")

# Remove tiny polygons (<30 m²)
buildings["area_m2"] = buildings.geometry.area
buildings = buildings[buildings["area_m2"] > 30]

# Fix invalid geometries
buildings = buildings.buffer(0)

# Save cleaned dataset
buildings.to_file("data_clean/buildings_cleaned.gpkg", driver="GPKG")

print("Cleaned building dataset saved!")
```

---

# 💡 Why This Project Matters
Building footprint processing is essential for:

- Emergency preparedness and response
- Flood and storm surge exposure modeling
- Damage assessment workflows
- Community vulnerability scoring
- Hazard mitigation planning

Relevant to employers such as:

- NCEM
- NC Floodplain Mapping Program
- NC DEQ
- Local EOCs
- Environmental & engineering consulting firms

---

# ✨ Future Enhancements
- LiDAR-based height estimation
- Deep learning–based building classification
- Parcel attribute integration
- Publishing cleaned footprints to ArcGIS Online
- Web dashboard for real-time hazard exposure

## Maps Included
![Flood Exposure Map NCEM](flood_exposure_map_ncem.png)

**© 2025 — Godwin Etim Akpan**
GIS • Spatial Data Science • Emergency Management • Remote Sensing

