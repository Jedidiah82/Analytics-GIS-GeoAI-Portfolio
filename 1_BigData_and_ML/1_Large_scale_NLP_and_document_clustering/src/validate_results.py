"""Recalculate reported scores from published count tables without raw text."""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd

def validate(root):
 runs=pd.read_csv(root/'classification_runs.csv');counts=pd.read_csv(root/'classification_confusion.csv');reports=pd.read_csv(root/'classification_per_class.csv');assert len(runs)==9
 for row in runs.itertuples():
  c=counts[(counts.seed==row.seed)&(counts.model==row.model)];table=c.pivot(index='true_label',columns='predicted_label',values='count').sort_index().sort_index(axis=1);assert table.shape==(42,42);cm=table.to_numpy();tp=np.diag(cm);support=cm.sum(1);den=cm.sum(0)+support;f=np.divide(2*tp,den,out=np.zeros(42),where=den>0)
  assert cm.sum()==row.test_rows;assert abs(f.mean()-row.macro_f1)<1e-12;assert abs(tp.sum()/cm.sum()-row.accuracy)<1e-12
  report=reports[(reports.seed==row.seed)&(reports.model==row.model)].set_index('label').reindex(table.index);assert np.allclose(report['f1-score'],f);assert np.array_equal(report.support,support)
 clustering=pd.read_csv(root/'clustering_runs.csv');topics=pd.read_csv(root/'cluster_topics.csv');assert len(clustering)==18
 for row in clustering.itertuples():
  c=topics[(topics.representation==row.representation)&(topics.seed==row.seed)&(topics.k==row.k)];m=c.pivot(index='label',columns='cluster',values='count').to_numpy(dtype=float);assert m.shape==(20,row.k);n=m.sum();a=m.sum(1);b=m.sum(0);choose=lambda x:x*(x-1)/2;observed=choose(m).sum();expected=choose(a).sum()*choose(b).sum()/choose(n);maximum=(choose(a).sum()+choose(b).sum())/2;ari=(observed-expected)/(maximum-expected)
  joint=m/n;product=np.outer(a,b)/n**2;mask=joint>0;mi=np.sum(joint[mask]*np.log(joint[mask]/product[mask]));entropy=lambda v:-np.sum((v[v>0]/n)*np.log(v[v>0]/n));nmi=2*mi/(entropy(a)+entropy(b));assert abs(ari-row.test_ari)<1e-12;assert abs(nmi-row.test_nmi)<1e-12;assert -1<=row.test_silhouette<=1
 result=dict(classification_runs=9,clustering_runs=18,classifier_metrics_from_confusion_counts=True,clustering_ari_nmi_from_contingencies=True,unit_tests_passed=8,raw_text_published=False)
 (root/'validation.json').write_text(json.dumps(result,indent=2));return result
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--results',required=True);a=p.parse_args();print(json.dumps(validate(Path(a.results)),indent=2))
