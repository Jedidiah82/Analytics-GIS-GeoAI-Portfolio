# 🦠 Lassa Fever GeoAI Forecasting — Liberia (2016–2026)

<p align="center">
  <strong>Godwin Etim Akpan</strong><br>
  Public Health Informatics • GeoAI • Spatial Epidemiology
</p>

<p align="center">
  <img src="https://img.shields.io/badge/GeoAI-Spatial%20ML-blueviolet" />
  <img src="https://img.shields.io/badge/Public%20Health-Epidemiology-red" />
  <img src="https://img.shields.io/badge/Python-3.10-blue" />
  <img src="https://img.shields.io/badge/XGBoost-ML-orange" />
  <img src="https://img.shields.io/badge/Time%20Series-ARIMA%20%7C%20Prophet-green" />
  <img src="https://img.shields.io/badge/GIS-GeoPandas%20%7C%20ArcGIS-darkgreen" />
</p>

---

## Project Metadata

| Field | Details |
|------|---------|
| **Title** | Lassa Fever GeoAI Forecasting — Liberia (2016–2026) |
| **Author** | Godwin Etim Akpan |
| **Affiliation** | Public Health Informatics \| GeoAI \| Spatial Epidemiology |
| **Version** | 1.0 |
| **Last Updated** | 2025-12-09 |
| **License** | MIT License (repository only — not for clinical use) |

---

## Description

A reproducible **spatio-temporal forecasting pipeline** combining national time-series models  
(**ARIMA, Prophet, STL decomposition**) with **GeoAI-based county-level prediction using XGBoost**.

### The workflow supports:

- Public health surveillance  
- Outbreak preparedness  
- Spatial epidemiology research  
- GeoAI demonstration  

**Forecast horizon:** 2016–2026

---

## Datasets

### 1️⃣ Lassa Fever Line List (Mocked)

- **Type:** CSV  
- **Source:** MoH/NPHIL (synthetic template only)

### 2️⃣ Liberia Administrative Boundaries

- **Type:** Shapefiles  
- **Source:** HDX / Humanitarian Data Exchange

---

## Models Used

- **ARIMA** – Univariate time-series forecasting  
- **Prophet** – Trend and seasonality decomposition  
- **STL** – Structural time-series decomposition  
- **XGBoost** – GeoAI spatio-temporal regression  

---

## Dependencies

- **Python:** ≥ 3.10  
- **Core:** pandas, numpy, scikit-learn  
- **ML:** xgboost, prophet  
- **Spatial:** geopandas  
- **Visualization:** matplotlib, seaborn  

---

## Reproducibility

### Requirements

- Jupyter Lab or VS Code Notebooks  
- Mock datasets in `data_template/`  
- Shapefiles in `shapefiles/`  

### Run Instructions

```bash
Open 05_Reproducibility_Notebook.ipynb and execute all cells
```

---

## Project Overview

This folder presents a complete **spatio-temporal forecasting workflow** for Lassa fever in Liberia.

It integrates **classical epidemiology** with **GeoAI** for national and subnational prediction  
through **2026**.

### Designed for:

- Public health decision-making  
- Epidemiological research  
- GeoAI demonstration  

### Key Outputs

- National-level case forecasts (ARIMA, Prophet)  
- Trend, seasonality, and anomaly decomposition (STL)  
- County-level GeoAI projections (XGBoost)  
- Heatmaps and hotspot spatial predictions  
- Optional forecast animations  
- Manuscript-ready figures  

---

## Objectives

1. Build a cleaned national and county-level dataset (2016–2022).  
2. Model monthly national incidence using:
   - ARIMA  
   - Prophet  
   - STL decomposition  
3. Engineer spatio-temporal features (lags, rolling means, climate proxies).  
4. Train an XGBoost model for county-level risk prediction.  
5. Generate forecasts for 2023–2026.  
6. Produce maps, figures, and tables for research and surveillance reporting.  

---

## Modeling Workflow

### 1️⃣ Time-Series Forecasting (National)

- ARIMA for autoregressive modeling  
- Prophet for trend + seasonal extraction  
- STL for structural decomposition  
- Confidence intervals and peak annotations  
- Forecast comparisons through 2026  

### 2️⃣ GeoAI (County-Level)

- Lagged features (t-1, t-2, t-3)  
- Rolling means and seasonal indicators  
- Optional covariates (rainfall, temperature, roads, population)  
- XGBoost regression for spatial prediction  

### 3️⃣ Spatial Analysis

- Choropleth hotspot maps  
- Cluster visualization (custom Python, SaTScan-style)  
- Multi-panel yearly incidence maps  
- Optional animated risk evolution  

---

## Example Outputs (Figures)

All generated plots and maps are available in the **Figures** folder:

👉 **[View Figures](https://github.com/Jedidiah82/Analytics-GIS-GeoAI-Portfolio/tree/main/2_PublicHealth_GeoAI/Lassa_GeoAI_Forecasting_2016_2026/Figures)**

This includes:

- ARIMA vs Prophet Forecast (2016–2026)  
- Prophet Trend & Seasonality Components  
- STL Decomposition  
- Rolling Mean Trends  
- GeoAI Hotspot Map (December 2026)  
- County-Level Incidence Maps (2017–2022)  
- Localized Cluster Maps  

*(Images rendered from analysis — no raw case data included.)*

---

## Data Disclaimer

All visualizations and outputs are derived from **aggregated, non-identifiable surveillance data**.

- No individual-level data is stored or shared  
- No confidential MoH/NPHIL datasets are included  
- Synthetic/template datasets are provided for reproducibility  
- Results do not represent official government reports  

---

## Citation

If referencing this work:

**Akpan, G.E. (2025).**  
*Lassa Fever GeoAI Forecasting — Liberia (2016–2026).*  
Big Data • GeoAI • Public Health Analytics Portfolio.  
https://github.com/Jedidiah82/
