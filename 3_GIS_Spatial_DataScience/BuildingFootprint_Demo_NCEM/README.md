![GIS](https://img.shields.io/badge/GIS-ArcGIS%20Pro-blue)
![Python](https://img.shields.io/badge/Python-GeoPandas-green)
![Project Status](https://img.shields.io/badge/Status-Planned-yellow)


# 🏠 Building Footprint Extraction Demo — NC Emergency Management (NCEM)

This project outlines a planned GIS workflow for **extracting, cleaning, validating, and analyzing building footprints** for hazard exposure modeling.  
It simulates the type of spatial data engineering used by **North Carolina Emergency Management (NCEM)**, NC Floodplain Mapping, and local/state emergency response teams.

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

**© 2025 — Godwin Etim Akpan**
GIS • Spatial Data Science • Emergency Management • Remote Sensing

