"""Create a clearly synthetic aggregate example; not Liberian surveillance data."""
import argparse
from pathlib import Path
import numpy as np
import pandas as pd


def create(path):
    rng=np.random.default_rng(42)
    dates=pd.date_range('2016-12-31','2022-12-31',freq='ME')
    rows=[]
    for county,rate in [('Example A',2.),('Example B',.5),('Example zero-history county',0.)]:
        for date in dates:
            intensity=rate*(1+.4*np.cos(2*np.pi*date.month/12))
            rows.append({'date':date,'county':county,'cases':int(rng.poisson(intensity))})
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    pd.DataFrame(rows).to_csv(path,index=False)
    print('Created synthetic example, not project observations:',path)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--output',default='data/example_synthetic.csv')
    create(parser.parse_args().output)
