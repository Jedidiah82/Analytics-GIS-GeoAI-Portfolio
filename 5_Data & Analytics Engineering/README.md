# Data and Geospatial Engineering

This index connects the portfolio's implemented data workflows to their source code, execution records and validation evidence. The projects cover historical log replay, network-flow preparation, spatial quality assurance and research data integration.

The implementations live in their project folders below. This directory provides navigation across them rather than a separate deployed data platform.

## Engineering evidence

| Project | Implemented engineering work | Recorded execution and scope |
| --- | --- | --- |
| [NASA HTTP log analytics](../1_BigData_and_ML/4_Streaming_Analytics_NASA/README.md) | Parse and validate HTTP logs; prepare event-time replay; aggregate minute/status windows; checkpoint, restart and reconcile outputs. | 3,461,612 valid requests across 35 data batches; 183,308 final windows independently reconciled. This is an event-time-sorted historical replay on local Spark, not a live production feed. |
| [UNSW-NB15 security analytics](../1_BigData_and_ML/2_UNSW_NB15_Intrusion_Detection/README.md) | Validate the 49-column flow schema and label semantics; group identical records during splitting; construct features; export named class metrics and provenance. | 2,539,739 records in the supplied extract. Corrected models ran in local PySpark on one machine; earlier HDFS/Hive work is documented separately. No multi-node speedup is claimed. |
| [Wake County building exposure](../3_GIS_Spatial_DataScience/BuildingFootprint_Demo_NCEM/README.md) | Reconcile a county inventory; validate and repair geometry; retain traceable identifiers; intersect archived hazards; reconcile distinct-building counts and threshold sensitivity. | 325,436 distinct footprints; 1,837 have positive-area overlap with archived Special Flood Hazard Areas. The result describes geometric exposure, not observed damage. Independent portfolio demonstration. |
| [GeoAI health surveillance](https://godwineakpan.com/projects/geoai-health-surveillance) | Integrate surveillance, population, environmental and boundary data; validate district-month records; build lagged features; expose research outputs through authenticated APIs and spatial reporting. | Evaluated research prototype spanning 136 districts and 4,760 modelling-ready observations. The evaluated data layer used CSV/GeoJSON; PostgreSQL/PostGIS functionality was separately validated. |

### Inspect the code and checks

**NASA:** [replay preparation](../1_BigData_and_ML/4_Streaming_Analytics_NASA/notebooks_or_src/prepare_replay.py), [streaming replay runner](../1_BigData_and_ML/4_Streaming_Analytics_NASA/notebooks_or_src/run_replay.py), [streaming contract results](../1_BigData_and_ML/4_Streaming_Analytics_NASA/results/stream_contract_tests.json), and [reconciliation summary](../1_BigData_and_ML/4_Streaming_Analytics_NASA/results/summary.json).

**UNSW-NB15:** [preparation and modelling workflow](../1_BigData_and_ML/2_UNSW_NB15_Intrusion_Detection/src/unsw_model_workflow.py), [input and split manifest](../1_BigData_and_ML/2_UNSW_NB15_Intrusion_Detection/results/manifest.json), [validation results](../1_BigData_and_ML/2_UNSW_NB15_Intrusion_Detection/results/validation.json), and [per-class metrics](../1_BigData_and_ML/2_UNSW_NB15_Intrusion_Detection/results/per_class_metrics.csv).

**Wake County:** [pipeline](../3_GIS_Spatial_DataScience/BuildingFootprint_Demo_NCEM/scripts/pipeline.py), [geometry QA](../3_GIS_Spatial_DataScience/BuildingFootprint_Demo_NCEM/results/qa.json), [independent output validation](../3_GIS_Spatial_DataScience/BuildingFootprint_Demo_NCEM/results/validation.json), and [exposure sensitivity](../3_GIS_Spatial_DataScience/BuildingFootprint_Demo_NCEM/results/exposure_sensitivity.csv).

**GeoAI:** [project repository](https://github.com/Jedidiah82/GeoAI-Health-Surveillance-System), [data schema](https://github.com/Jedidiah82/GeoAI-Health-Surveillance-System/blob/main/reproducibility/DATA_SCHEMA.md), [API implementation](https://github.com/Jedidiah82/GeoAI-Health-Surveillance-System/blob/main/app/api.py), and [analytical environment record](https://github.com/Jedidiah82/GeoAI-Health-Surveillance-System/blob/main/reproducibility/ANALYTICAL_ENVIRONMENT.txt). The case study distinguishes original evaluation, additional geographic/temporal validation, demonstrated deployment and proposed production work.

## Additional implemented workflows

- **[NLP and document clustering](../1_BigData_and_ML/1_Large_scale_NLP_and_document_clustering/README.md):** normalized-text deduplication, training-only feature learning, held-out evaluation, resumable experiments and aggregate result validation. The corrected experiments used single-machine scikit-learn/gensim; see the [runner](../1_BigData_and_ML/1_Large_scale_NLP_and_document_clustering/src/run_experiments.py) and [validation record](../1_BigData_and_ML/1_Large_scale_NLP_and_document_clustering/results/validation.json).
- **[Validated catalog uploads](../6_Automation_Reliability/Secure_File_Upload/README.md):** bounded metadata/JPEG preparation, bearer authentication, verified HTTPS, timeouts and explicit acknowledgement handling. [29 passing local tests](../6_Automation_Reliability/Secure_File_Upload/evidence/validation.json) include disposable HTTPS receivers and certificate rejection. External service deployment and durable storage require separate validation.

## Reproduce a workflow

1. Open the selected project's README and use its declared Python, Java and dependency versions.
2. Obtain the permitted source data and compare input hashes with its manifest. Public aggregate outputs do not replace missing raw inputs.
3. Run the project's tests and execution commands. Inspect fresh exit states, timestamps, counts and validation results before interpreting figures.
4. Retain the run configuration, source/input hashes and aggregate results. Keep restricted records, individual predictions, secrets and local environments outside public commits.

The environment requirements differ between projects; there is no single shared runner for this index. Linked records describe their published executions, not a new rerun triggered by reading this page.

## Future development

Potential extensions include workflow orchestration with Airflow, event ingestion with Kafka, and a Microsoft Fabric/Power BI implementation with versioned transformations and a semantic model. These are proposed directions here; this directory contains no corresponding deployed platform, notebooks, pipelines or BI model.

A future addition should publish runnable source, a permitted sample input, expected outputs, validation checks and a clear execution scope before it is listed as implemented evidence. Production operation would also require deployment-specific monitoring, access control, recovery procedures and measured service behavior.

## Professional development

Relevant background includes MSc Big Data Technologies coursework and research, the IBM Data Science Professional Certificate and Google IT Automation with Python. The MSc's 180 credits are completed and passed; final award remains pending university confirmation. [Current qualifications and credential evidence](https://godwineakpan.com/#education) are maintained on the portfolio.

[View the portfolio](https://godwineakpan.com/) · [Return to the repository](../README.md)

