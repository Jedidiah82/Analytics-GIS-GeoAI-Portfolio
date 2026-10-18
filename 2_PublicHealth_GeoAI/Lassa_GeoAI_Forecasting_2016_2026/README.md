# Lassa Fever Forecasting

A Liberia research project combining monthly surveillance analysis, seasonal forecasting, and exploratory county-level GeoAI. National model comparisons and spatial visualisation connect statistical reasoning with public-health data engineering.

[Read the portfolio case study](https://godwineakpan.com/projects/lassa-geoai-forecasting)

## Engineering contribution

Built the monthly aggregation, SARIMA/Prophet comparisons, county feature workflow, and GIS outputs, connecting temporal modelling with spatial communication.

## Workflow

1. **Aggregate the history:** Parse onset dates, count records by month, and construct a continuous national series and county–month panel. Keep observed coverage separate from future dates.
2. **Compare national models:** Fit seasonal SARIMA and Prophet to training data through 2020; compare predictions with the January 2021–December 2022 holdout using RMSE.
3. **Explore county features:** Build calendar, dry-season, lag, rolling-average, and national-model features for exploratory county-level XGBoost experiments.
4. **Communicate spatially:** Link county outputs to administrative boundaries and communicate temporal and spatial patterns through clear figures.

## Selected results

- **Prophet / national holdout — 3.652 RMSE.** Lower monthly count error on the January 2021–December 2022 holdout.
- **SARIMA / same holdout — 5.283 RMSE.** A seasonal autoregressive baseline evaluated against the same observed months.
- **Analytical contribution — Time + place.** Monthly aggregation, seasonal diagnostics, comparative forecasting, and county feature engineering form one coherent research workflow.

![Original national time-series plot showing training observations through 2020 and observed versus SARIMA and Prophet values in 2021–2022, with shaded bands.](Figures/national_forecasts/national_ARIMA_vs_Prophet.png)

National monthly observations with SARIMA and Prophet predictions across the 2021–2022 temporal holdout. The comparison makes model fit and uncertainty visible alongside RMSE.

## Engineering decisions

- **Evaluate forward in time.** A 24-month national holdout preserves temporal order: train through December 2020, then compare forecasts with observations from 2021–2022.
- **Pair statistical and visual inspection.** SARIMA and Prophet offer complementary seasonal models; decomposition and observed-versus-predicted plots help interpret the aggregate error metric.
- **Connect national and county scales.** National trends and county histories form complementary analytical views. The county workflow explores how temporal features can be linked to spatial outputs.

## Scope and limitations

- **County forecasting remains exploratory.** The county workflow includes current-target rolling predictors and zero-filled future outcomes in feature construction. Its training-fit score is not held-out forecast validation. Shifted predictors, explicit future handling, and temporal county evaluation are required before relying on those projections.
- **Count support and map coverage.** The county export contains negative predictions and covers nine modelled counties. Historical zeros for counties with no recorded outbreaks must be distinguished from missing model predictions and unknown future outcomes.
- **National evaluation and uncertainty.** The national comparison is a single holdout. Rolling-origin tests and seasonal-naive baselines remain needed. The figure’s interval labels require verification against model settings; its subsequent projection continues a model trained through 2020.
- **Reproducibility and data provenance.** The public template and historical notebook differ. Correct split/index handling, supply a tested synthetic aggregate example, and document reporting completeness and permissions. Earlier scores based on a zero-extended test panel are excluded from the reported comparison.

## Code and reproducibility

Explore the [implementation](Scripts/) and original project figures. These are historical research results; the models and streaming jobs were not rerun for the portfolio presentation.

The historical analysis uses local surveillance data; the public script describes a template workflow. Case-level records and the full exploratory notebook are not shared. Data provenance, permissions, and a tested synthetic aggregate demonstration remain part of the next iteration. The original implementation review is available in [technical notes](Evidence/lassa-evidence-review.txt).

## Next iteration

1. **Strengthen national evaluation.** Compare seasonal-naive, SARIMA, and Prophet across rolling forecast origins; measure MAE/RMSE and interval coverage before a full-history refit.
2. **Rebuild the county forecast path.** Shift rolling features, preserve unknown future outcomes, and evaluate a defined recursive or direct strategy on observed temporal holdouts.
3. **Make the research reproducible.** Publish a tested synthetic-data workflow with versioned dependencies, coverage-aware maps, and meaningful uncertainty displays.
