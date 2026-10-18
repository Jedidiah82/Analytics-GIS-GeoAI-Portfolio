"""Export complete aggregate curves from private predictions after model fitting.

This preserves every PR threshold point for publication; the model runner's
bounded preview exports can omit narrow changes in curve shape.
"""
from pathlib import Path
import argparse
import numpy as np,pandas as pd
from sklearn.metrics import roc_curve,precision_recall_curve

def export(project,private_predictions):
    results=Path(project)/'results'
    for split in ['group_random_70_30','capture_holdout']:
        p=np.load(Path(private_predictions)/f'{split}_lr.npz')
        fpr,tpr,_=roc_curve(p['actual'],p['score'],drop_intermediate=False)
        precision,recall,_=precision_recall_curve(p['actual'],p['score'])
        pd.DataFrame({'x':fpr,'y':tpr}).to_csv(results/f'{split}_roc.csv',index=False)
        pd.DataFrame({'x':recall,'y':precision}).to_csv(results/f'{split}_pr.csv',index=False)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--project',default='.');ap.add_argument('--private-predictions',required=True)
    a=ap.parse_args();export(a.project,a.private_predictions)
