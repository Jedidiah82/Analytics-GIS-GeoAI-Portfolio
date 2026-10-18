# Lassa Fever Forecasting — Liberia

An exploratory project connecting monthly surveillance aggregation, national SARIMA/Prophet models, county-level XGBoost, and GIS mapping. Historical observations end in 2022; dates through 2026 are a projection horizon.

[Read the portfolio case study](https://godwineakpan.com/projects/lassa-geoai-forecasting)

## What was implemented

- National monthly aggregation, rolling-mean inspection and STL decomposition.
- A documented national temporal holdout: train through December 2020, test January 2021–December 2022.
- County–month feature engineering, XGBoost experiments, and boundary joins for maps.
- Original figures and saved outputs; these historical models were not rerun for this review.

## National result with an explicit evaluation window

| Model | Saved RMSE, January 2021–December 2022 |
| --- | ---: |
| SARIMA (1,0,1) × (1,0,1,12) | 5.283 |
| Prophet | 3.652 |

These are rounded saved outputs from notebook cell 135, in monthly case-count units. The recovered national series has 73 months, December 2016–December 2022. Prophet has lower error on this single holdout. No general model superiority, calibrated interval coverage, or county forecast skill follows from this comparison.

![Original national holdout comparison](Figures/national_forecasts/national_ARIMA_vs_Prophet.png)

The figure labels both bands as 95%; the archived Prophet constructor does not explicitly set interval width, so its nominal level needs checking. The later projection in that notebook cell uses the model trained through 2020; it is not a documented refit on all observations through 2022.

## County outputs require methodological revision

The archived workflow contains current-target rolling predictors, zero-filled future outcomes entering lag features, and a training-fit RMSE that does not measure forecast generalization. The recovered 2023–2026 county export has 432 rows across nine counties and includes 305 negative raw predictions. It should not be presented as a validated forecast product.

The author confirms that counties with no recorded outbreaks were assigned historical zero values. This describes historical coding. Some saved maps also fill missing model predictions with zero; those missing predictions should be labelled separately rather than presented as model-derived future zeros. Choropleth colours represent modelled counts, not population-adjusted incidence or statistically significant hotspots. The archived December 2026 map and later county CSV have different numerical ranges and are treated as distinct outputs.

## Evidence available here

- [Historical metrics, labelled by run and validity](Evidence/lassa-saved-metrics.csv).
- [Implementation review and revision plan](Evidence/lassa-evidence-review.txt).
- [Selected original modelling source excerpts](Evidence/archived-model-excerpts.txt).
- Existing [forecasting script](Scripts/lassa_forecasting_pipeline.py) and [original figures](Figures/).

An earlier notebook experiment extends its test panel through 2026 using zero-filled future outcomes. Its lower SARIMA score is preserved in the evidence CSV only for provenance; it is excluded from the observed holdout comparison above.

## Reproducibility status

The existing script is a template-oriented implementation and differs from the historical notebook. The inspected folder does not contain its referenced `data_template/`, shapefile inputs, or `05_Reproducibility_Notebook.ipynb`. A verified one-command reproduction is not yet provided.

Before rerunning or relying on its outputs, correct the overlapping train/test endpoint, SARIMA forecast-date assignment, unshifted rolling predictor, and future-history handling described in the review. Pin dependency versions and publish clearly labelled synthetic aggregate inputs with schema checks.

## Data provenance and scope

The historical notebook reads local case-level data; the repository script describes template inputs. These are different provenance statements. Case-level records, the full notebook with row outputs, and surveillance input CSVs are not included in this update. Data-sharing permissions, reporting completeness, and whether absent months represent verified zeros need documenting before a public data release.

The figures are research outputs, not official forecasts or operational guidance. No clinical or surveillance deployment is established by the recovered evidence.

## Next iteration

1. Compare seasonal-naive, SARIMA and Prophet across rolling forecast origins; measure MAE/RMSE and interval coverage.
2. Shift rolling predictors and fit every transformation within the training window.
3. Keep future outcomes unknown and implement an explicit recursive or direct county forecast strategy.
4. Evaluate nonnegative county forecasts on observed temporal holdouts and report per-county support.
5. Publish a tested synthetic-data demonstration and maps with coverage, uncertainty and consistent scales.
