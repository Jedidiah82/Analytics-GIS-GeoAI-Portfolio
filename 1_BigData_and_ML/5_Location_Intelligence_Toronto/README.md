# 🗺️ Location Intelligence — Chinese Restaurant Site Selection (Toronto)

![Geospatial](https://img.shields.io/badge/Geo-Spatial%20Analysis-green)
![Python](https://img.shields.io/badge/Python-3.10-blue)
![KMeans](https://img.shields.io/badge/ML-KMeans-orange)
![Foursquare](https://img.shields.io/badge/API-Foursquare-lightgrey)

## 📌 Overview
A geo-analytics workflow to identify **optimal locations for Chinese restaurant expansion** across Toronto neighborhoods.

Combines:

- Web scraping  
- Geocoding  
- Venue density extraction via Foursquare  
- K-Means clustering  
- Interactive mapping (Folium)  

---

## 🎯 Objectives
- Identify underserved neighborhoods  
- Map clusters of complementary venues  
- Provide a reusable geospatial market analysis framework  

---

## 🛠️ Stack
`Python` · `pandas` · `BeautifulSoup` · `Geopy` · `Foursquare Places API` · `scikit-learn` · `Folium`  

---

## 🔬 Workflow Summary

1. **Scraping**
   - Extract neighborhood names from Wikipedia  
2. **Geocoding**
   - Convert neighborhoods → coordinates  
3. **Foursquare Venue Extraction**
   - Fetch all venues within 500m radius  
4. **Feature Engineering**
   - Category density matrix  
5. **Clustering (k = 5)**
   - Identify neighborhood profiles  
6. **Mapping**
   - Folium cluster overlays  
   - Heatmaps for density patterns  

---

## 🧭 Key Insights
- East York, York, and West Toronto show strong market potential  
- Clusters reveal neighborhood similarities in amenities  
- Framework generalizes to any retail or service location analysis  

---

## 📊 Deliverables
- Interactive HTML maps  
- Cluster membership tables  
- Density plots  

---

## 🚀 Next Steps
- Add census demographics and mobility data  
- Try HDBSCAN or GMM clustering  
- Deploy as a web-based decision tool  

