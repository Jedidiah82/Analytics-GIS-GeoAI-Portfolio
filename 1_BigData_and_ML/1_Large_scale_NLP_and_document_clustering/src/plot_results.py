"""Publication figures from verified CSV outputs; no raw headlines are displayed."""
from pathlib import Path
import json,argparse
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
BG='#08131f';PANEL='#102330';FG='#edf4fa';MUTED='#a5bac9';BLUE='#87bdff';MINT='#5de1b6';GOLD='#f6c573'
def theme():plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':PANEL,'text.color':FG,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':'#39586c','font.family':'DejaVu Sans','font.size':11,'savefig.facecolor':BG,'axes.spines.top':False,'axes.spines.right':False})
def heading(fig,title,sub):
 fig.text(.07,.95,'NLP / REPRODUCIBLE REPRESENTATION STUDY',fontsize=10,color=BLUE,weight='bold');fig.text(.07,.89,title,fontsize=22,weight='bold');fig.text(.07,.83,sub,fontsize=10,color=MUTED)
def comparison(r,d,mobile):
 x=pd.read_csv(r/'classification_runs.csv');f,axes=plt.subplots(2,1,figsize=(8,10)) if mobile else plt.subplots(1,2,figsize=(14,7));f.subplots_adjust(left=.26 if mobile else .13,right=.94,top=.72,bottom=.20,wspace=.3,hspace=.6)
 heading(f,'Words, vectors, and the baseline','Three repeated stratified 80/20 splits · same retained headlines per seed')
 order=['Majority','Word2Vec + LR','TF-IDF + LR']
 for ax,col,title in zip(axes,['macro_f1','accuracy'],['Macro-F1 / equal weight per category','Accuracy / all held-out headlines']):
  for i,(name,c) in enumerate(zip(order,[MUTED,GOLD,MINT])):
   v=x[x.model==name][col].to_numpy();ax.barh(i,v.mean(),color=c,height=.48,alpha=.65);ax.scatter(v,np.arange(len(v))*.07+i-.07,color=FG,s=18,zorder=3);ax.text(v.mean()+.025,i,f'{v.mean():.3f}',va='center',color=c,weight='bold')
  ax.set_yticks(range(3),['Majority','Averaged\nWord2Vec' if mobile else 'Averaged Word2Vec','TF-IDF']);ax.set_xlim(0,1);ax.set_title(title,loc='left',fontsize=12,pad=15);ax.set_xlabel('Score (0–1)');ax.grid(axis='x',alpha=.13)
 f.text(.07,.07,'Bars: mean over seeds 42, 137, 2026. White points: individual split results.\nThese overlapping random splits measure split sensitivity, not independent confidence intervals.\nTF-IDF, embeddings, and embedding scaling are fitted on training data only.',fontsize=9,color=MUTED)
 f.savefig(d,dpi=180);plt.close(f)
def classes(r,d,mobile):
 x=pd.read_csv(r/'classification_per_class.csv');p=x[x.model.isin(['TF-IDF + LR','Word2Vec + LR'])].groupby(['label','model'])['f1-score'].mean().unstack();p=p.sort_values('TF-IDF + LR');parts=[p] if mobile else [p.iloc[:21],p.iloc[21:]]
 f,ax=plt.subplots(1,len(parts),figsize=(8,16) if mobile else (15,10),squeeze=False);f.subplots_adjust(left=.30 if mobile else .18,right=.94,top=.77,bottom=.12,wspace=.95)
 heading(f,'Every category counts','Per-category F1 · mean across three splits · all 42 categories')
 for axis,part in zip(ax[0],parts):
  for i,(name,row) in enumerate(part.iterrows()):
   axis.plot([row['Word2Vec + LR'],row['TF-IDF + LR']],[i,i],color='#496071',lw=1.2)
  for name,color,marker in [('Word2Vec + LR',GOLD,'s'),('TF-IDF + LR',MINT,'o')]:axis.scatter(part[name],range(len(part)),c=color,s=24,label=name,marker=marker)
  axis.set_yticks(range(len(part)),[n.replace('_',' ').title() for n in part.index],fontsize=16 if mobile else 13);axis.set_xlim(0,1);axis.set_xlabel('F1 score (0–1)');axis.grid(axis='x',alpha=.13)
 ax[0,0].legend(loc='upper left',bbox_to_anchor=(0,1.10),ncol=1,frameon=False,fontsize=12,labelcolor=FG)
 f.text(.07,.04,'Each category has equal weight in macro-F1.\nThe complete precision, recall, support, and confusion counts are supplied as CSV.',fontsize=10,color=MUTED)
 f.savefig(d,dpi=180);plt.close(f)
def clusters(r,d,mobile):
 x=pd.read_csv(r/'clustering_runs.csv');s=json.loads((r/'summary.json').read_text());f,ax=plt.subplots(2,1,figsize=(8,10)) if mobile else plt.subplots(1,2,figsize=(14,7));f.subplots_adjust(left=.13,right=.94,top=.72,bottom=.23,wspace=.3,hspace=.6)
 heading(f,'How well do clusters recover topics?','Official later partition · no topic labels used to fit the representations or clusters')
 for axis,col,title in zip(ax,['test_ari','test_nmi'],['Adjusted Rand index','Normalized mutual information']):
  for name,color,marker in [('TF-IDF',BLUE,'o'),('LSA-100',MINT,'s')]:
   group=x[x.representation==name].groupby('k')[col];means=group.mean();low=group.min();high=group.max();axis.errorbar(means.index,means,yerr=[means-low,high-means],c=color,marker=marker,capsize=4,label=name,lw=2)
  axis.set_ylim(0,.30 if col=='test_ari' else .50);axis.set_xticks([10,15,20]);axis.set_xlabel('Number of clusters (k)');axis.set_title(title,loc='left',pad=15);axis.grid(axis='y',alpha=.13)
 ax[0].legend(frameon=False,labelcolor=FG)
 f.text(.07,.07,'Points: mean across seeds. Whiskers: observed minimum–maximum, not confidence intervals.\nARI is chance-adjusted; NMI measures topic–cluster association. Perfect agreement = 1.\nCandidate k is selected within each representation using training silhouette only.',fontsize=9,color=MUTED)
 f.savefig(d,dpi=180);plt.close(f)
def topics(r,d):
 x=pd.read_csv(r/'cluster_topics.csv');s=json.loads((r/'summary.json').read_text());k=s['selected_k_by_training_silhouette']['LSA-100'];x=x[(x.representation=='LSA-100')&(x.seed==42)&(x.k==k)];p=x.pivot(index='label',columns='cluster',values='count');p=p.div(p.sum(axis=1),axis=0)
 f,ax=plt.subplots(figsize=(13,10));f.subplots_adjust(left=.29,right=.91,top=.76,bottom=.14);heading(f,'Topic recovery, without a projection',f'LSA-100 · training-selected k={k} · seed 42 · held-out documents')
 im=ax.imshow(p,cmap='Blues',vmin=0,vmax=1,aspect='auto');ax.set_yticks(range(len(p)),p.index,fontsize=10);ax.set_xticks(range(k),range(k));ax.set_xlabel('Arbitrary cluster ID');f.colorbar(im,ax=ax,label='Share of each topic',fraction=.035,pad=.025)
 f.text(.07,.04,'Rows sum to 100%. A topic spread across columns is split between clusters.\nCluster IDs have no semantic order; this view does not imply one-to-one topic recovery.',fontsize=10,color=MUTED);f.savefig(d,dpi=180);plt.close(f)
if __name__=='__main__':
 a=argparse.ArgumentParser();a.add_argument('--results',required=True);a.add_argument('--figures',required=True);args=a.parse_args();r=Path(args.results);out=Path(args.figures);out.mkdir(parents=True,exist_ok=True);theme()
 for name,fn in [('nlp-representation-comparison',comparison),('nlp-category-performance',classes),('nlp-topic-recovery',clusters)]:
  for mobile in [False,True]:fn(r,out/(name+('-mobile' if mobile else '')+'.png'),mobile)
 topics(r,out/'nlp-topic-association.png')

