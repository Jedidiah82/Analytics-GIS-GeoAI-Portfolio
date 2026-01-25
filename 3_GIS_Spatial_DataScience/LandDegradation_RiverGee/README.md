# 🌿 Land Degradation & Productivity Assessment — River Gee County, Liberia (2001–2015)

![SDG 15.3](https://img.shields.io/badge/SDG-15.3%20Land%20Degradation%20Neutrality-2E7D32)
![Remote Sensing](https://img.shields.io/badge/Remote%20Sensing-Landsat%20%7C%20NDVI-1976D2)
![GIS Analysis](https://img.shields.io/badge/GIS-Trends.Earth%20%7C%20ArcGIS-6A1B9A)
![Policy Use](https://img.shields.io/badge/Use-Policy%20%26%20Decision--Support-455A64)
![Environment](https://img.shields.io/badge/Domain-Environmental%20Monitoring-00897B)

**SDG 15.3 Pilot Project | Independent GIS Research (2019)**  
**Tools:** Trends.Earth, ArcGIS, Remote Sensing  

---

## Overview
This project presents a **remote sensing–driven assessment of land degradation and land productivity trends** in River Gee County, Liberia, supporting national implementation of **SDG 15.3 (Land Degradation Neutrality)**.

Using Earth observation data and the **Trends.Earth** analytical framework, spatial and temporal patterns of degradation were quantified between **2001 and 2015** in one of Liberia’s least-documented regions.

---

## Analytical Workflow

```mermaid
flowchart LR
    A[Satellite Data<br/>Landsat Time Series] --> B[Preprocessing<br/>Cloud Masking & Normalization]
    B --> C[Vegetation Index<br/>NDVI Computation]
    C --> D[Temporal Analysis<br/>2001–2015 Trends]
    D --> E[Land Productivity Assessment<br/>Trends.Earth]
    E --> F["Land Degradation Classification<br/>Improved | Stable | Degraded"]
    F --> G[Spatial Hotspot Identification]
    G --> H[Policy-Ready Maps & Indicators<br/>SDG 15.3 Reporting]
```
*Figure: End-to-end analytical workflow illustrating how satellite observations were transformed into SDG 15.3–aligned land degradation indicators for policy and decision support.*

---

## Key Outputs

### Land Degradation Status
![Land degradation status in River Gee County](figures/land_degradation_status.png)

*Classification of land as Improved, Stable, or Degraded based on SDG 15.3 indicators.*

---

### Land Productivity Trends
![Land productivity trends in River Gee County](figures/land_productivity_trends.png)

*Spatial patterns of increasing, stable, and declining land productivity.*

---

## Analytical Workflow
- Satellite data preprocessing (cloud masking, reflectance normalization)
- NDVI time-series analysis
- Land productivity trajectory assessment
- Change detection (2001 → 2015)
- SDG 15.3 indicator computation using Trends.Earth
- Cartographic synthesis for policy communication

---

## Impact
- Demonstrated the feasibility of **sub-national SDG 15.3 monitoring** using open geospatial tools
- Identified **degradation hotspots** to support conservation and land management planning
- Findings were presented to **local policymakers**, including the Senator of River Gee County
- Contributed to policy dialogue with **Conservation International** and partners

---

## Limitations & Future Work
- Incorporate higher-resolution Sentinel-2 imagery
- Integrate rainfall, soil, and socio-economic covariates
- Extend analysis to national-scale SDG reporting

---

## Author
**Godwin Etim Akpan**  
GIS & Remote Sensing Specialist  
Environmental Analytics • SDG Monitoring • Spatial Decision Support
