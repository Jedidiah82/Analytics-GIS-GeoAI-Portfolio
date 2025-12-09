---
title: "Lassa Fever GeoAI Forecasting — Liberia (2016–2026)"
author: "Godwin Etim Akpan"
affiliation: "Public Health Informatics | GeoAI | Spatial Epidemiology"
version: "1.0"
last_updated: "2025-01-01"

description: |
  A fully reproducible spatio-temporal forecasting pipeline combining
  national time series (ARIMA, Prophet, STL) with county-level GeoAI (XGBoost).
  Includes hotspot mapping, animations, and manuscript-ready outputs.

datasets:
  - name: "Lassa Fever line list (mocked)"
    type: "CSV"
    source: "MoH/NPHIL (not included publicly — synthetic template only)"

models:
  - ARIMA
  - Prophet
  - STL decomposition
  - XGBoost regression (GeoAI)

dependencies:
  python: ">=3.10"
  packages:
    - pandas
    - numpy
    - scikit-learn
    - xgboost
    - prophet
    - geopandas
    - matplotlib

reproducibility:
  requires:
    - Jupyter Lab
    - Mock datasets provided in data_template/
    - Shapefiles stored in shapefiles/
  run:
    - "Open 05_Reproducibility_Notebook.ipynb and run all cells"

license: "MIT License (repo)"
---


# 🦠 Lassa Fever GeoAI Forecasting — Liberia (2016–2026)

A fully reproducible **spatio-temporal forecasting pipeline** for Lassa fever in Liberia, integrating:

- 📈 National time series (ARIMA, Prophet, STL)  
- 🤖 GeoAI county-level forecasting (XGBoost)  
- 🗺 Spatial hotspot mapping with GeoPandas  
- 🎥 Animated forecast maps (2023–2026)  
- 📄 Draft academic manuscript (Methods + Results + Discussion)

---

## 📌 Objectives

1. Build a **cleaned national & county-level dataset** (2016–2022).  
2. Model national monthly incidence with ARIMA + Prophet.  
3. Engineer spatio-temporal features (lags, rolling means, seasonality).  
4. Train an **XGBoost GeoAI model** for county-level forecasting.  
5. Produce 2023–2026 predictions + spatial hotspot maps.  
6. Deliver manuscript-ready outputs.

---

## 📂 Folder Structure

# Placeholder - content coming soon
