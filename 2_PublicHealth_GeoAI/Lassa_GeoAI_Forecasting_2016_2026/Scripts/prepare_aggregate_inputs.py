"""Prepare the project's aggregate exports; never read a case-level line list.

The supplied county roster is complete. Counties absent from the source panel
are assigned historical zero only under the author's explicit no-outbreak coding.
"""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd

COUNTIES=['Bomi','Bong','Gbarpolu','Grand Bassa','Grand Cape Mount','Grand Gedeh',
          'Grand Kru','Lofa','Margibi','Maryland','Montserrado','Nimba','River Gee','Rivercess','Sinoe']


def prepare(panel_csv,national_csv,output):
    p=pd.read_csv(panel_csv)
    p['date']=pd.to_datetime(p['month_date']).dt.to_period('M').dt.to_timestamp('M')
    blank=p.FIRST_CCNA.isna() | p.FIRST_CCNA.astype(str).str.strip().eq('')
    if not p.loc[blank,'cases'].eq(0).all():
        raise ValueError('Unassigned nonzero cases require geographic reconciliation')
    p=p.loc[~blank & p.date.between('2016-12-31','2022-12-31')].copy()
    p['county']=p.FIRST_CCNA.str.strip()
    if not set(p.county).issubset(COUNTIES):
        raise ValueError('Unknown county label')
    if p.duplicated(['date','county']).any():
        raise ValueError('Duplicate county-months')
    dates=pd.date_range('2016-12-31','2022-12-31',freq='ME')
    for county,frame in p.groupby('county'):
        if not pd.DatetimeIndex(frame.date.sort_values()).equals(dates):
            raise ValueError('Missing observed row for '+county)
    index=pd.MultiIndex.from_product([dates,COUNTIES],names=['date','county'])
    observed=p.set_index(['date','county']).cases
    result=observed.reindex(index,fill_value=0).rename('cases').reset_index()
    n=pd.read_csv(national_csv)
    n['date']=pd.to_datetime(n.onset_date)
    if not pd.DatetimeIndex(n.date).equals(dates):
        raise ValueError('National observed dates do not match the project window')
    actual=result.groupby('date').cases.sum().reindex(dates).to_numpy()
    if not np.array_equal(actual,n.cases.to_numpy()):
        raise ValueError('County totals do not reconcile with national series')
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    result.to_csv(output,index=False)
    print('Prepared',len(result),'observed rows; historical total',int(result.cases.sum()))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--panel-csv',required=True)
    ap.add_argument('--national-csv',required=True);ap.add_argument('--output',required=True)
    args=ap.parse_args();prepare(args.panel_csv,args.national_csv,args.output)
