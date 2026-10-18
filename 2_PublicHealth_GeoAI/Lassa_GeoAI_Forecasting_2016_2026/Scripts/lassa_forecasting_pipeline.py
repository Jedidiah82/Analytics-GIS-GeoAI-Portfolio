"""Leakage-safe national and county forecasting from aggregate monthly counts.

Input: date, county, cases. Every county-month in the observed window must exist;
historical zero rows are explicit data. Future observations must never be supplied
as zero placeholders. Case-level records are neither required nor exported.
"""
import argparse
import hashlib
import json
import logging
import platform
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from statsmodels.tsa.statespace.sarimax import SARIMAX
from prophet import Prophet
from xgboost import XGBRegressor

NATIONAL_MODELS = ['Seasonal naive', 'SARIMA', 'Prophet']
COUNTY_MODELS = ['Zero baseline', 'Seasonal naive', 'Recent mean', 'Poisson XGBoost']
LAGS = [1, 2, 3, 12]
SEED = 42


def load_panel(path, observed_end=None):
    frame = pd.read_csv(path, keep_default_na=False)
    if not {'date', 'county', 'cases'}.issubset(frame.columns):
        raise ValueError('Expected date, county, cases')
    frame = frame[['date', 'county', 'cases']].copy()
    frame['date'] = pd.to_datetime(frame['date']).dt.to_period('M').dt.to_timestamp('M')
    if frame.county.str.strip().eq('').any():
        raise ValueError('Blank county labels are not allowed')
    frame['county'] = frame.county.str.strip()
    frame['cases'] = pd.to_numeric(frame.cases, errors='raise')
    if not np.isfinite(frame.cases).all() or (frame.cases < 0).any() or (frame.cases % 1 != 0).any():
        raise ValueError('Historical counts must be nonnegative finite integers')
    if frame.duplicated(['date', 'county']).any():
        raise ValueError('Duplicate county-month rows')
    if observed_end is not None and frame.date.max() != pd.Timestamp(observed_end):
        raise ValueError('Input must end at the declared observation cutoff; do not append future placeholders')
    pivot = frame.pivot(index='date', columns='county', values='cases').sort_index()
    expected = pd.date_range(pivot.index.min(), pivot.index.max(), freq='ME')
    if not pivot.index.equals(expected) or pivot.isna().any().any():
        raise ValueError('Supply a complete observed panel with explicit historical zeros')
    return pivot.astype(float).asfreq('ME')


def score(actual, prediction):
    actual, prediction = np.asarray(actual), np.asarray(prediction)
    error = prediction - actual
    return {'mae': float(np.abs(error).mean()), 'rmse': float(np.sqrt(np.mean(error**2))),
            'bias': float(error.mean()), 'observations': int(actual.size)}


def next_features(history, date, county, counties):
    """All outcome-based predictors use only values strictly before date."""
    if len(history) < max(LAGS):
        raise ValueError('Need twelve prior months')
    row = {f'lag_{lag}': float(history[-lag]) for lag in LAGS}
    row.update(roll_3=float(np.mean(history[-3:])), roll_6=float(np.mean(history[-6:])),
               month_sin=float(np.sin(2*np.pi*date.month/12)),
               month_cos=float(np.cos(2*np.pi*date.month/12)))
    row.update({f'county_{i}': float(county == name) for i, name in enumerate(counties)})
    return row


def make_training_features(panel):
    records, targets = [], []
    counties = list(panel.columns)
    for county in counties:
        values = panel[county].to_numpy()
        for i in range(12, len(panel)):
            records.append(next_features(values[:i], panel.index[i], county, counties))
            targets.append(values[i])
    return pd.DataFrame(records), np.asarray(targets)


def county_forecast(panel, future_dates, method):
    counties = list(panel.columns)
    histories = {c: panel[c].tolist() for c in counties}
    model = None
    if method == 'Poisson XGBoost':
        x, y = make_training_features(panel)
        if y.sum() > 0:
            model = XGBRegressor(objective='count:poisson', n_estimators=200,
                max_depth=2, learning_rate=.03, min_child_weight=3, reg_lambda=5,
                subsample=1, colsample_bytree=1, random_state=SEED, n_jobs=1)
            model.fit(x, y)
    output = []
    for date in future_dates:
        if model is not None:
            x_future = pd.DataFrame([next_features(histories[c], date, c, counties) for c in counties])
            predicted = np.maximum(0., model.predict(x_future))
        elif method == 'Poisson XGBoost':
            predicted = np.zeros(len(counties))
        elif method == 'Zero baseline':
            predicted = np.zeros(len(counties))
        elif method == 'Seasonal naive':
            predicted = np.array([histories[c][-12] for c in counties])
        elif method == 'Recent mean':
            predicted = np.array([np.mean(histories[c][-3:]) for c in counties])
        else:
            raise ValueError(method)
        for county, prediction in zip(counties, predicted):
            prediction = max(0., float(prediction))
            histories[county].append(prediction)
            output.append({'date': date, 'county': county, 'prediction': prediction})
    return pd.DataFrame(output)


def national_forecast(history, future_dates, method):
    """National models fit only history; model intervals are not calibrated guarantees."""
    diagnostic = {'method': method, 'converged': True, 'warnings': []}
    horizon = len(future_dates)
    if method == 'Seasonal naive':
        values = history.tolist()
        point = []
        for _ in future_dates:
            point.append(values[-12]); values.append(values[-12])
        residual = history.to_numpy()[12:] - history.to_numpy()[:-12]
        low, high = np.quantile(residual, [.025, .975])
        lower, upper = np.array(point) + low, np.array(point) + high
        diagnostic['interval_method'] = '95% training seasonal-residual empirical band; constant across leads'
    elif method == 'SARIMA':
        with warnings.catch_warnings(record=True) as messages:
            warnings.simplefilter('always')
            specification = SARIMAX(history, order=(1,0,1), seasonal_order=(1,0,1,12),
                enforce_stationarity=True, enforce_invertibility=True)
            fit = specification.fit(disp=False, maxiter=500)
            diagnostic['optimizer'] = 'L-BFGS'
            if not fit.mle_retvals.get('converged', False):
                # Optimizer fallback depends only on training convergence, never test error.
                fallback = specification.fit(method='powell',disp=False,maxiter=2000)
                if fallback.mle_retvals.get('converged', False) and np.isfinite(fallback.llf) and np.isfinite(fallback.params).all():
                    fit = fallback
                    diagnostic['optimizer'] = 'Powell fallback after L-BFGS nonconvergence'
            forecast = fit.get_forecast(horizon)
            point = forecast.predicted_mean.to_numpy()
            interval = forecast.conf_int(alpha=.05).to_numpy()
        lower, upper = interval[:,0], interval[:,1]
        diagnostic.update(converged=bool(fit.mle_retvals.get('converged', False)),
            warnings=sorted(set(str(m.message) for m in messages)), interval_method='SARIMA nominal 95% model interval')
    elif method == 'Prophet':
        np.random.seed(SEED)
        logging.getLogger('cmdstanpy').setLevel(logging.WARNING)
        frame = pd.DataFrame({'ds': history.index, 'y': history.to_numpy()})
        model = Prophet(yearly_seasonality=True, weekly_seasonality=False,
            daily_seasonality=False, interval_width=.95, uncertainty_samples=1000)
        model.fit(frame, seed=SEED)
        forecast = model.predict(pd.DataFrame({'ds': future_dates}))
        point, lower, upper = (forecast[k].to_numpy() for k in ['yhat','yhat_lower','yhat_upper'])
        diagnostic['interval_method'] = 'Prophet nominal 95% model interval'
    else:
        raise ValueError(method)
    point = np.asarray(point, dtype=float)
    diagnostic['negative_raw_point_predictions'] = int((point < 0).sum())
    bounded_point, bounded_low, bounded_high = np.maximum(0, point), np.maximum(0, lower), np.maximum(0, upper)
    if not np.isfinite(np.r_[bounded_point, bounded_low, bounded_high]).all():
        raise ValueError('Nonfinite forecast')
    if np.any(bounded_low > bounded_high):
        raise ValueError('Inverted interval')
    return pd.DataFrame({'date': future_dates, 'prediction': bounded_point,
                         'lower': bounded_low, 'upper': bounded_high}), diagnostic


def evaluate(panel, origins, horizon, label):
    national_rows, county_rows, private_national, private_county, diagnostics = [], [], [], [], []
    for origin in origins:
        training = panel.loc[:origin]
        testing = panel.loc[panel.index > pd.Timestamp(origin)].iloc[:horizon]
        if len(training) < 25 or len(testing) != horizon:
            raise ValueError('Not enough history or observed test months')
        history = training.sum(axis=1)
        for method in NATIONAL_MODELS:
            try:
                prediction, diagnostic = national_forecast(history, testing.index, method)
            except RuntimeError as error:
                if method != 'Prophet':
                    raise
                diagnostics.append({'evaluation':label,'origin':origin,'method':method,'converged':False,
                    'available':False,'failure':'Prophet/Stan fit failed in this runtime; no score reported',
                    'error_type':type(error).__name__})
                print('Prophet unavailable for this origin; continuing verified models',flush=True)
                continue
            values = testing.sum(axis=1).to_numpy()
            result = score(values, prediction.prediction)
            result['coverage_95'] = float(((values >= prediction.lower) & (values <= prediction.upper)).mean())
            result['mean_band_width'] = float((prediction.upper-prediction.lower).mean())
            national_rows.append({'evaluation':label, 'origin':origin, 'horizon_months':horizon, 'model':method, **result})
            diagnostics.append({'evaluation':label, 'origin':origin, **diagnostic})
            prediction['actual'] = values; prediction['model'] = method
            prediction['evaluation'] = label; prediction['origin'] = origin
            private_national.append(prediction)
        known_positive = training.columns[training.sum() > 0]
        for method in COUNTY_MODELS:
            prediction = county_forecast(training, testing.index, method)
            truth = testing.rename_axis('date').stack().rename('actual').reset_index()
            truth.columns = ['date','county','actual']
            merged = prediction.merge(truth, on=['date','county'], validate='one_to_one')
            for group, subset in [('All counties',merged), ('Prior-case counties',merged[merged.county.isin(known_positive)])]:
                if len(subset):
                    county_rows.append({'evaluation':label,'origin':origin,'horizon_months':horizon,
                        'model':method,'group':group,**score(subset.actual,subset.prediction)})
            merged['model'] = method; merged['evaluation'] = label; merged['origin'] = origin
            private_county.append(merged)
        print(f'Completed {label} / origin {origin}', flush=True)
    return pd.DataFrame(national_rows), pd.DataFrame(county_rows), pd.concat(private_national), pd.concat(private_county), diagnostics


def run(input_path, output, private_output, origins, projection_end):
    output, private_output = Path(output), Path(private_output)
    results = output/'results'; results.mkdir(parents=True,exist_ok=True)
    private_output.mkdir(parents=True,exist_ok=True)
    panel = load_panel(input_path, '2022-12-31')
    frames = evaluate(panel, origins, 12, 'Annual rolling origin')
    national, county, national_predictions, county_predictions, diagnostics = frames
    fixed = evaluate(panel, ['2020-12-31'], 24, '2021–2022 holdout')
    pd.concat([national,fixed[0]]).to_csv(results/'national_metrics.csv',index=False)
    pd.concat([county,fixed[1]]).to_csv(results/'county_metrics.csv',index=False)
    pd.concat([national_predictions,fixed[2]]).to_csv(private_output/'national_backtests.csv',index=False)
    pd.concat([county_predictions,fixed[3]]).to_csv(private_output/'county_backtests.csv',index=False)
    summary = []
    for level, frame in [('National',national_predictions),('County',county_predictions)]:
        for method, group in frame.groupby('model'):
            summary.append({'level':level,'model':method,**score(group.actual,group.prediction)})
    summary = pd.DataFrame(summary)
    summary.to_csv(results/'backtest_summary.csv',index=False)
    eligible_national = [m for m in NATIONAL_MODELS if all(d['converged'] for d in diagnostics if d['method']==m)]
    selected_national = summary[(summary.level=='National') & summary.model.isin(eligible_national)].sort_values(['mae','model']).iloc[0].model
    selected_county = summary[summary.level=='County'].sort_values(['mae','model']).iloc[0].model
    dates = pd.date_range(panel.index.max()+pd.offsets.MonthEnd(1),projection_end,freq='ME')
    projections = []
    for method in NATIONAL_MODELS:
        try:
            frame, diagnostic = national_forecast(panel.sum(axis=1),dates,method)
        except RuntimeError as error:
            if method != 'Prophet':
                raise
            diagnostics.append({'evaluation':'Full-history projection','origin':str(panel.index.max().date()),
                'method':method,'converged':False,'available':False,
                'failure':'Prophet/Stan fit failed in this runtime; no projection reported',
                'error_type':type(error).__name__})
            continue
        frame['model'] = method; frame['selected'] = method==selected_national
        projections.append(frame); diagnostics.append({'evaluation':'Full-history projection','origin':str(panel.index.max().date()),**diagnostic})
    pd.concat(projections).to_csv(results/'national_projections.csv',index=False)
    county_scenarios=[]
    for method in COUNTY_MODELS:
        frame=county_forecast(panel,dates,method)
        frame['model']=method
        frame['lowest_backtest_mae']=method==selected_county
        county_scenarios.append(frame)
    pd.concat(county_scenarios).to_csv(results/'county_projections.csv',index=False)
    per_county=[]
    for (method,name), group in county_predictions.groupby(['model','county']):
        per_county.append({'model':method,'county':name,'historical_zero':bool(panel[name].sum()==0),**score(group.actual,group.prediction)})
    pd.DataFrame(per_county).to_csv(results/'county_backtest_summary.csv',index=False)
    (results/'diagnostics.json').write_text(json.dumps(diagnostics+fixed[4],indent=2),encoding='utf-8')
    import statsmodels, prophet, xgboost
    manifest = {'run_date':'2026-10-18','source_sha256':hashlib.sha256(Path(input_path).read_bytes()).hexdigest(),
        'observed_start':str(panel.index.min().date()),'observed_end':str(panel.index.max().date()),
        'observed_months':len(panel),'counties':list(panel.columns),'historical_total':int(panel.to_numpy().sum()),
        'historical_zero_counties':list(panel.columns[panel.sum()==0]),
        'zero_policy':'Explicit historical zeros preserved; future targets never zero-filled',
        'origins':origins,'horizon_months':12,'selected_national':selected_national,'selected_county':selected_county,
        'selection':'lowest pooled annual rolling-origin MAE; SARIMA requires convergence in all annual folds',
        'projection_origin':str(panel.index.max().date()),'projection_end':projection_end,
        'prediction_policy':'Point forecasts and interval endpoints bounded below at zero',
        'hierarchy':'National and county models evaluated separately; not reconciled to identical totals',
        'county_uncertainty':'No calibrated county forecast intervals established',
        'unavailable_model_runs':[{'model':d['method'],'evaluation':d['evaluation'],'origin':d['origin']}
            for d in diagnostics+fixed[4] if d.get('available') is False],
        'versions':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,
                    'statsmodels':statsmodels.__version__,'prophet':prophet.__version__,'xgboost':xgboost.__version__},
        'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in Path(__file__).parent.glob('*.py')}}
    (results/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print(summary.to_string(index=False),flush=True)
    print('Selected:',selected_national,'/',selected_county,flush=True)
    return manifest


if __name__=='__main__':
    ap=argparse.ArgumentParser()
    ap.add_argument('--input',required=True);ap.add_argument('--output',default='.')
    ap.add_argument('--private-output',required=True)
    ap.add_argument('--origins',default='2019-12-31,2020-12-31,2021-12-31')
    ap.add_argument('--projection-end',default='2026-12-31')
    args=ap.parse_args();run(args.input,args.output,args.private_output,args.origins.split(','),args.projection_end)
