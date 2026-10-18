import sys
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'Scripts'))
import numpy as np
import pandas as pd
from lassa_forecasting_pipeline import load_panel, next_features, make_training_features, county_forecast, score
from lassa_forecasting_pipeline import evaluate


class ForecastTests(unittest.TestCase):
    def panel(self):
        dates=pd.date_range('2018-01-31',periods=48,freq='ME')
        return pd.DataFrame({'A':np.tile(np.arange(12),4),'Zero':np.zeros(48)},index=dates)

    def test_features_exclude_current_target(self):
        p=self.panel();x,y=make_training_features(p)
        changed=p.copy();changed.iloc[-1,0]=9999
        xx,yy=make_training_features(changed)
        # The final target changes, but its corresponding feature vector does not.
        np.testing.assert_array_equal(x.iloc[35],xx.iloc[35])
        self.assertNotEqual(y[35],yy[35])
        self.assertEqual(x.iloc[0].roll_3,p.A.iloc[9:12].mean())

    def test_future_truth_cannot_enter_forecast(self):
        p=self.panel();dates=pd.date_range('2022-01-31',periods=24,freq='ME')
        for method in ['Seasonal naive','Recent mean','Zero baseline']:
            a=county_forecast(p,dates,method)
            b=county_forecast(p.copy(),dates,method)
            pd.testing.assert_frame_equal(a,b)
            self.assertTrue((a.prediction>=0).all())

    def test_recursive_history_updates(self):
        p=self.panel();dates=pd.date_range('2022-01-31',periods=24,freq='ME')
        r=county_forecast(p,dates,'Seasonal naive')
        np.testing.assert_array_equal(r[r.county=='A'].prediction,np.tile(np.arange(12),2))
        z=r[r.county=='Zero'];self.assertTrue(z.prediction.eq(0).all())
        # A three-month-mean forecast must update its history after each step.
        r=county_forecast(p,dates[:2],'Recent mean');a=r[r.county=='A'].prediction.to_numpy()
        self.assertAlmostEqual(a[0],10)
        self.assertAlmostEqual(a[1],(10+11+10)/3)

    def test_zero_history_and_complete_input(self):
        p=self.panel();frame=p.rename_axis('date').stack().rename('cases').reset_index()
        frame.columns=['date','county','cases']
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'aggregate.csv';frame.to_csv(path,index=False)
            loaded=load_panel(path)
            self.assertTrue(loaded.Zero.eq(0).all())
            with self.assertRaises(ValueError):load_panel(path,'2022-12-31')
            frame.iloc[:-1].to_csv(path,index=False)
            with self.assertRaises(ValueError):load_panel(path)

    def test_duplicate_and_negative_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'input.csv'
            pd.DataFrame({'date':['2022-01-31']*2,'county':['A']*2,'cases':[1,1]}).to_csv(path,index=False)
            with self.assertRaises(ValueError):load_panel(path)
            pd.DataFrame({'date':['2022-01-31'],'county':['A'],'cases':[-1]}).to_csv(path,index=False)
            with self.assertRaises(ValueError):load_panel(path)

    def test_scoring(self):
        values=score([0,2],[1,1])
        self.assertEqual(values['mae'],1)
        self.assertEqual(values['rmse'],1)
        self.assertEqual(values['bias'],0)

    def test_backtest_forecasts_ignore_poisoned_test_targets(self):
        p=self.panel();poisoned=p.copy();poisoned.loc['2021-01-31':,'A']=9999
        with patch('lassa_forecasting_pipeline.NATIONAL_MODELS',['Seasonal naive']):
            a=evaluate(p,['2020-12-31'],12,'test')
            b=evaluate(poisoned,['2020-12-31'],12,'test')
        for index in [2,3]:
            columns=[c for c in a[index].columns if c!='actual']
            pd.testing.assert_frame_equal(a[index][columns],b[index][columns])

    def test_poisson_outputs_and_history_preservation(self):
        p=self.panel();original=p.copy(deep=True)
        r=county_forecast(p,pd.date_range('2022-01-31',periods=24,freq='ME'),'Poisson XGBoost')
        self.assertTrue(np.isfinite(r.prediction).all())
        self.assertTrue((r.prediction>=0).all())
        pd.testing.assert_frame_equal(p,original)


if __name__=='__main__':unittest.main()
