# Correction record

The previous summary used 4,672,975 statewide cleaned footprints and 1,943 overlay rows to report 0.042%. It is superseded; it is not a Wake County exposure percentage.

| Previous issue | Corrected behaviour |
|---|---|
| Statewide denominator and county hazard extent | One county boundary governs numerator and denominator |
| Count of overlay fragments | Distinct stable source building IDs; overlapping pieces dissolved |
| Overlay row index used to flag original buildings | Explicit ID join |
| Web Mercator measurement and automatic <30 m² removal | North Carolina metric CRS; retain and flag small features |
| All FEMA polygons styled as flood hazard | SFHA flag controls primary exposure and map styling; 0.2% zone shown separately |
| Missing execution contract and planned README | Executed summaries, pinned environment, tests, saved-file validation and provenance |
| Broad multi-hazard success language | Completed flood exposure scope; other hazards remain future work |

This is not a like-for-like trend or a measured increase in flood risk: geography, counting rules, CRS, geometry processing and retained population changed. The old script and notebook are preserved in the original source location, outside this prepared upload package. Historical repository artifacts are explicitly superseded in the README. The old root map filename is replaced with the validated atlas so existing image links show the corrected presentation.
