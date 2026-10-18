# Distributed Security Analytics — UNSW-NB15

A 2025 academic workflow using HDFS, Hive, PySpark, and Spark MLlib for traffic profiling and baseline intrusion classification in a Cloudera Hadoop VM environment.

[Read the portfolio case study](https://godwineakpan.com/projects/distributed-security-analytics)

## Engineering contribution

- Load CSV records into HDFS and query an external Hive table.
- Normalize attack categories with trimming and case normalization; check the normal-traffic meaning of blank categories.
- Profile traffic counts, protocols, byte distributions, and selected feature relationships.
- Train binary Logistic Regression and multiclass Random Forest baselines using byte/TTL features and a reported 70/30 split.
- Examine ROC and confusion outputs rather than relying on aggregate accuracy alone.

## Dataset evidence

The report's Hive count is **2,539,739** records: **2,218,456 normal** and **321,283 attack**. This is about 87.4% normal traffic, so a majority-class accuracy baseline is already high. The local raw CSV is headerless; an explicit schema and row-alignment checks are essential.

## Results confirmed in saved notebook output

| Result | Evidence status |
| --- | --- |
| Logistic Regression binary AUC = 0.987 | Saved notebook cell 9 and report section 3.3.1; rounded, not independently rerun |
| Random Forest accuracy = 0.967 | Saved notebook cell 16 confirms report section 3.3.2; 20 trees, rounded |
| Multiclass confusion matrix | Requires full class-index mapping and reconciliation before interpretation |

The former README assigned 96.7% to Logistic Regression and gave Random Forest 92–94% and AUC 0.95+. The recovered notebook confirms the report’s model assignments; the earlier assignments are corrected here.

![Reported binary ROC](figures/roc_curve.png)

The existing figures remain historical outputs, not new validated measurements. The reported confusion matrix should not be presented as evidence of strong minority-class detection until the label mapping and prediction columns are audited.

## Reproducibility status

Recovered material now includes:

- [Selected original PySpark modelling cells](src/unsw_model_workflow.py).
- [Saved printed metrics](results/unsw-saved-metrics.csv), rounded to three decimal places.
- [Run details and qualifications](results/unsw-run-summary.txt).

The source uses explicit names for 49 CSV columns; four features (`sbytes`, `dbytes`, `sttl`, `dttl`); 70/30 random splits with seed 42; and a 20-tree Random Forest. No dataset is bundled. Run the script from a directory containing `UNSW-NB15.csv` after configuring compatible Spark, Java and Python dependencies. Exact historical dependency versions have not been recovered, and this update did not rerun the workflow.

This is a selected-cell archive rather than the entire exploratory notebook. It preserves the original modelling choices so they can be audited. The binary rule assigns 0 to `Unknown` and 1 to every other cleaned category: explicit `Normal` strings would therefore be mislabelled. Verify agreement with the original binary label. The multiclass StringIndexer was fitted before the split; its fitted label order was not saved with this model. Later notebook mappings belong to different scratch work and cannot establish this run’s mapping.

## Corrections and limitations

- The report's capture-year narrative says 2025 while its query screenshot shows 2015. Do not repeat the 2025 capture claim.
- Some feature ranges suggest a need to audit schema-to-column alignment; weak correlation does not prove statistical independence.
- Report per-class precision/recall/support, macro-F1, PR-AUC, and a held-out/temporal evaluation before promoting detector quality.
- No measured multi-node speedup, real-time detection deployment, calibrated probabilities, or SIEM integration is established.

## Next steps

Recover fitted class mappings and dependency versions; validate schema, label agreement, and leakage; rerun both models with auditable split information; publish exact metrics and environment; then evaluate scaling or live ingestion as separate extensions.

Academic provenance: Big Data Analytics coursework report, May 29, 2025. Dataset: UNSW-NB15. A laboratory research project, not an operational security product.
