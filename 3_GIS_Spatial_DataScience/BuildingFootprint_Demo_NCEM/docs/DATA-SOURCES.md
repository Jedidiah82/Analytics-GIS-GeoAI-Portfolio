# Data sources and exact inputs

The corrected run reads original inputs without modifying them. Source files remain external to this code/figure package.

| Input relative to original project | Bytes | SHA-256 |
|---|---:|---|
| `microsoft_footprints.geojson` | 1,313,670,108 | `86cf2fae79b1286590dd10fe6618997cb938d7d77654de95a160d31a5c59adce` |
| `flood_fema_nfhl.gpkg` | 70,205,440 | `df30d7e29e5824f927dd39e1197bc2adf93b78fc66f2d2072e163fdea2f0c9ca` |
| `wake-county-tigerweb.geojson` | 114,742 | `cf59b20e2f7030a822c0f00e9b2afc368e04fb36647e3a5e5216c984403cc37f` |

Original project layout: `data_raw/microsoft_footprints.geojson` and `hazards/flood_fema_nfhl.gpkg`. The authoritative original download endpoint was not preserved. Locate the original files using this layout and compare hashes; replacing them with newly downloaded data creates a new analytical version and is not an exact reproduction.

The boundary packaged here is `data_reference/wake-county-tigerweb.geojson`. Its metadata sidecar preserves the US Census service description (January 1, 2026 vintage) and retrieval timestamp. To retrieve a new snapshot, use `python scripts/fetch_boundary.py --output new-boundary.geojson`; do not overwrite the baseline. The source is `https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query`, with `where=GEOID='37183'`, `outFields=*`, `outSR=4326`, `f=geojson`.

The hazard GPKG's DBF_DATE_LAST_UPDATE is 2025-07-18, DFIRM_ID 37183C. This describes an archived file, not confirmed current regulatory status. The old companion metadata XML contains placeholders and is not accepted as authoritative source documentation.

Dependency versions are pinned in requirements.txt and recorded in results/run_manifest.json. EPSG:32119 is NAD83 / North Carolina in metres. The footprint input is EPSG:4326; hazard input is EPSG:4269. No online basemap is needed or used for the maps.
