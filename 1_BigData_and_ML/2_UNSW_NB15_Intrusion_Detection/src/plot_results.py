"""Regenerate dark portfolio figures from exported aggregate results only."""
from pathlib import Path
import argparse
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

BG='#08131f';PANEL='#102330';FG='#edf4fa';MUTED='#a5bac9';GOLD='#f6c573';BLUE='#87bdff';MINT='#5de1b6'
SPLITS=['group_random_70_30','capture_holdout'];NAMES=['Grouped random split','January → February']

def theme():
    plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':PANEL,'text.color':FG,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':'#39586c','font.family':'DejaVu Sans','font.size':11,'savefig.facecolor':BG,'axes.spines.top':False,'axes.spines.right':False})

def header(fig,kicker,title,mobile):
    fig.text(.06,.955,kicker,color=GOLD,fontsize=11,weight='bold')
    fig.text(.06,.895,title,color=FG,fontsize=23 if not mobile else 20,weight='bold')

def benchmark(results,out,mobile):
    frame=pd.read_csv(results/'model_metrics.csv');theme()
    fig,axes=plt.subplots(2,1,figsize=(8,11)) if mobile else plt.subplots(1,2,figsize=(14,6.6))
    fig.subplots_adjust(left=.25 if mobile else .12,right=.91,top=.75 if not mobile else .79,bottom=.25,wspace=.5,hspace=.6)
    header(fig,'UNSW-NB15 / EVALUATION DESIGN','Test beyond the random split',mobile)
    tasks=[('Logistic Regression',['roc_auc','average_precision','balanced_accuracy'],['ROC-AUC','Average precision','Balanced accuracy']),('Random Forest',['accuracy','macro_f1','balanced_accuracy'],['Accuracy','Macro-F1','Balanced accuracy'])]
    for ax,(model,keys,labels) in zip(axes,tasks):
        for i,key in enumerate(keys):
            values=[float(frame[(frame.model==model)&(frame.split==s)].iloc[0][key]) for s in SPLITS]
            ax.plot(values,[i,i],color='#637d90',lw=2,zorder=1)
            for v,color,dy,marker in zip(values,[BLUE,GOLD],[-.14,.14],['o','D']):
                ax.scatter([v],[i],s=75,color=color,marker=marker,zorder=3)
                ax.annotate(f'{v:.3f}',(v,i),xytext=(0,-18 if dy>0 else 12),textcoords='offset points',ha='center',fontsize=10,color=color)
        ax.set_yticks(range(3),labels);ax.set_ylim(-.6,2.6);ax.invert_yaxis();ax.set_xlim(0,1.03);ax.set_xlabel('Score · higher is better');ax.set_title(model,pad=18,loc='left',fontsize=14);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    from matplotlib.lines import Line2D
    handles=[Line2D([],[],marker=m,color=c,lw=0,label=l,markersize=7) for c,m,l in zip([BLUE,GOLD],['o','D'],NAMES)]
    fig.legend(handles=handles,loc='lower left',bbox_to_anchor=(.055,.085),frameon=False,ncol=1 if mobile else 2,labelcolor=FG,fontsize=10)
    fig.text(.06,.025,'Fixed four-feature models · source labels retained\nDifferent capture periods and class proportions; this is a robustness comparison.',fontsize=9,color=MUTED)
    fig.savefig(out,dpi=180);plt.close(fig)

def recall_plot(results,out,mobile):
    frame=pd.read_csv(results/'per_class_metrics.csv');support=pd.read_csv(results/'split_support.csv');theme()
    order=['Normal','Generic','Exploits','Fuzzers','DoS','Reconnaissance','Analysis','Backdoor','Shellcode','Worms']
    fig,ax=plt.subplots(figsize=(8,10) if mobile else (13,7.3));fig.subplots_adjust(left=.29 if mobile else .19,right=.77 if mobile else .84,top=.77,bottom=.18)
    header(fig,'UNSW-NB15 / PER-CLASS DETECTION','See every class, including the rare ones' if not mobile else 'Every class counts',mobile)
    for i,name in enumerate(order):
        values=[frame[(frame.model=='Random Forest')&(frame.split==s)&(frame['class']==name)].iloc[0].recall for s in SPLITS]
        ax.plot(values,[i,i],color='#637d90',lw=2)
        ax.scatter(values,[i,i],color=[BLUE,GOLD],s=65,marker='o')
        ax.scatter([values[1]],[i],color=GOLD,s=62,marker='D')
        n=int(support[(support.split=='capture_holdout')&(support['class']==name)].iloc[0].test)
        ax.text(1.055,i,f'{n:,}',transform=ax.get_yaxis_transform(),ha='left',va='center',fontsize=10,color=MUTED)
    ax.text(1.055,1.035,'February\nsupport',transform=ax.transAxes,fontsize=10,color=MUTED)
    ax.set_yticks(range(len(order)),order);ax.set_ylim(-.7,len(order)-.3);ax.invert_yaxis();ax.set_xlim(-.03,1.03);ax.set_xticks([0,.25,.5,.75,1],['0%','25%','50%','75%','100%']);ax.set_xlabel('Recall · share of each actual class correctly identified');ax.grid(axis='x',alpha=.15)
    from matplotlib.lines import Line2D
    fig.legend(handles=[Line2D([],[],marker=m,color=c,lw=0,label=l) for c,m,l in zip([BLUE,GOLD],['o','D'],NAMES)],loc='lower left',bbox_to_anchor=(.055,.065),ncol=1 if mobile else 2,frameon=False,labelcolor=FG,fontsize=10)
    fig.text(.06,.025,'60-tree Random Forest · 10 named classes\nSupport is shown because small classes produce less stable estimates.',fontsize=9,color=MUTED)
    fig.savefig(out,dpi=180);plt.close(fig)

def curves(results,out,mobile):
    frame=pd.read_csv(results/'model_metrics.csv');theme()
    fig,axes=plt.subplots(2,1,figsize=(8,11)) if mobile else plt.subplots(1,2,figsize=(14,6.8));fig.subplots_adjust(left=.12,right=.95,top=.77,bottom=.20,hspace=.65,wspace=.30)
    header(fig,'UNSW-NB15 / BINARY DISCRIMINATION','Inspect the threshold tradeoff',mobile)
    for split,name,color,style in zip(SPLITS,NAMES,[BLUE,GOLD],['-','--']):
        row=frame[(frame.split==split)&(frame.model=='Logistic Regression')].iloc[0]
        for ax,kind in zip(axes,['roc','pr']):
            curve=pd.read_csv(results/f'{split}_{kind}.csv')
            score=row.roc_auc if kind=='roc' else row.average_precision
            label=f'{name}\n{"AUC" if kind=="roc" else "AP"} {score:.3f}'
            if kind=='pr':
                ax.step(curve.x,curve.y,where='post',color=color,ls=style,lw=2,label=label)
            else:
                ax.plot(curve.x,curve.y,color=color,ls=style,lw=2,label=label)
    axes[0].plot([0,1],[0,1],color='#8296a6',ls=':',lw=1);axes[0].set_xlabel('False-positive rate');axes[0].set_ylabel('True-positive rate');axes[0].set_title('ROC',loc='left',pad=12)
    axes[1].set_xlabel('Recall');axes[1].set_ylabel('Precision');axes[1].set_title('Precision–recall',loc='left',pad=12)
    for ax in axes:ax.set_xlim(0,1);ax.set_ylim(0,1.03);ax.grid(alpha=.13);ax.legend(loc='lower left',frameon=False,labelcolor=FG,fontsize=9)
    prevalences=[frame[(frame.split==s)&(frame.model=='Logistic Regression')].iloc[0].attack_prevalence for s in SPLITS]
    fig.text(.06,.07,f'Attack prevalence: random {prevalences[0]:.1%} · February {prevalences[1]:.1%}\nAverage precision depends on prevalence; curves describe different test cohorts.',fontsize=10,color=MUTED)
    fig.savefig(out,dpi=180);plt.close(fig)

def matrix(results,out):
    data=pd.read_csv(results/'capture_holdout_rf_confusion.csv',index_col=0);values=data.to_numpy();pct=values/values.sum(axis=1,keepdims=True)*100;theme()
    fig,ax=plt.subplots(figsize=(12,10));fig.subplots_adjust(left=.20,right=.88,bottom=.22,top=.78)
    header(fig,'UNSW-NB15 / LATER-CAPTURE CONFUSION','Where February traffic was classified',False)
    cmap=LinearSegmentedColormap.from_list('mint',['#102330','#246e6b','#65e1ba'])
    im=ax.imshow(pct,vmin=0,vmax=100,cmap=cmap)
    labels=[x.replace('Reconnaissance','Recon.').replace('Shellcode','Shellcode') for x in data.index]
    ax.set_xticks(range(10),labels,rotation=45,ha='right');ax.set_yticks(range(10),labels);ax.set_xlabel('Predicted class');ax.set_ylabel('Actual class')
    for i in range(10):
        for j in range(10):ax.text(j,i,'0' if values[i,j]==0 else f'{pct[i,j]:.1f}',ha='center',va='center',fontsize=8,color=BG if pct[i,j]>55 else FG)
    cb=fig.colorbar(im,ax=ax,fraction=.035,pad=.035);cb.set_label('% of actual class')
    fig.text(.06,.045,'Row-normalised percentages · each actual class sums to 100% before rounding\nRecon. = Reconnaissance. Full counts and named class mapping are supplied as CSV.',fontsize=10,color=MUTED)
    fig.savefig(out,dpi=180);plt.close(fig)

def main(project):
    project=Path(project);results=project/'results';out=project/'figures';out.mkdir(exist_ok=True)
    for mobile in [False,True]:
        suffix='-mobile' if mobile else ''
        for stem,fn in [('unsw-evaluation',benchmark),('unsw-class-recall',recall_plot),('unsw-discrimination',curves)]:fn(results,out/f'{stem}{suffix}.png',mobile)
    matrix(results,out/'unsw-capture-confusion.png')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--project',default='.');main(ap.parse_args().project)
