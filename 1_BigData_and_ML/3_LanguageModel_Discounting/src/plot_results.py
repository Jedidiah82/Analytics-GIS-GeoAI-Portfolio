"""Publication figures from summary.csv; bands denote sample SD, not CI."""
import argparse
import csv
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter

COLORS = {'MLE': '#aebed3', 'Simple Good–Turing': '#62e3ba', 'Absolute discounting': '#c6a0ff'}
MARKERS = {'MLE': 'o', 'Simple Good–Turing': 's', 'Absolute discounting': '^'}
BG, PANEL, FG, MUTED = '#08131f', '#0d1e2c', '#f1f6fc', '#b2c5d5'


def theme():
    plt.rcParams.update({'font.family':'DejaVu Sans', 'font.size':11,
        'figure.facecolor':BG, 'axes.facecolor':PANEL, 'axes.edgecolor':'#375066',
        'axes.labelcolor':MUTED, 'text.color':FG, 'xtick.color':MUTED, 'ytick.color':MUTED,
        'grid.color':'#2a4154', 'grid.alpha':.55, 'axes.spines.top':False,
        'axes.spines.right':False, 'savefig.facecolor':BG})


def plot_metric(rows, metric, title, ylabel, output, mobile=False):
    theme()
    fig, axes = plt.subplots(2, 1, figsize=(7, 10.5), sharey=True) if mobile else plt.subplots(1, 2, figsize=(13.4, 5.8), sharey=True)
    if mobile:
        fig.subplots_adjust(left=.15, right=.96, bottom=.19, top=.82, hspace=.5)
    else:
        fig.subplots_adjust(left=.075, right=.98, bottom=.24, top=.73, wspace=.24)
    fig.text(.075, .94, 'RARE-WORD PROBABILITY ESTIMATION', color=COLORS['Simple Good–Turing'], fontsize=10, weight='bold')
    if mobile:
        title = 'The smoothing trade-off' if metric == 'js_nats' else 'Words not yet observed'
    fig.text(.075, .865, title, fontsize=23 if not mobile else 21, weight='bold')
    supports = [('50k + UNK','50,000-word vocabulary + UNK'),('Full training vocabulary + UNK','Full training vocabulary + UNK')]
    for ax,(support,label) in zip(axes,supports):
        for method,color in COLORS.items():
            group = sorted([r for r in rows if r['support']==support and r['estimator']==method], key=lambda r:int(r['sample_tokens']))
            x=np.array([int(r['sample_tokens']) for r in group]);y=np.array([float(r[metric+'_mean']) for r in group]);sd=np.array([float(r[metric+'_sd']) for r in group])
            ax.plot(x,y,label=method,color=color,marker=MARKERS[method],linewidth=2.3,markersize=6)
            ax.fill_between(x,np.maximum(0,y-sd),y+sd,color=color,alpha=.12,linewidth=0)
        ax.set_title(label,loc='left',fontsize=12,pad=16,color=FG)
        ax.set_xscale('log');ax.set_xticks([1000,10000,100000,1000000],['1k','10k','100k','1M'])
        ax.set_ylim(bottom=0);ax.grid(axis='y');ax.set_xlabel('Verified sample size (tokens)',labelpad=12)
    axes[0].set_ylabel(ylabel,labelpad=12)
    common_top = max(float(r[metric+'_mean']) + float(r[metric+'_sd']) for r in rows) * 1.12
    axes[0].set_ylim(0, common_top)
    if metric=='unseen_mass_absolute_error':
        for ax in axes:ax.yaxis.set_major_formatter(FuncFormatter(lambda x,_:f'{x*100:.0f}%'))
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower left',bbox_to_anchor=(.065,.055 if mobile else .085),ncol=1 if mobile else 3,frameon=False,labelcolor=FG)
    footnote='Mean ± sample SD · 5 draws · lower is better\nReference: final 20% of Text8' if mobile else 'Mean ± sample SD over 5 draws · held-out reference: final 20% of Text8 · lower is better'
    fig.text(.075,.015 if mobile else .035,footnote,color=MUTED,fontsize=10)
    fig.savefig(output,dpi=180);plt.close(fig)


def main(base):
    base=Path(base);figs=base/'figures';figs.mkdir(exist_ok=True)
    with (base/'results/summary.csv').open(encoding='utf-8') as f:rows=list(csv.DictReader(f))
    plot_metric(rows,'js_nats','More data changes the smoothing trade-off','Jensen–Shannon divergence (nats)',figs/'smoothing-js-comparison.png')
    plot_metric(rows,'unseen_mass_absolute_error','Estimate the probability of words not yet observed','Absolute error in unseen probability mass',figs/'smoothing-unseen-mass.png')
    plot_metric(rows,'js_nats','More data changes the smoothing trade-off','Jensen–Shannon divergence (nats)',figs/'smoothing-js-mobile.png',mobile=True)
    plot_metric(rows,'unseen_mass_absolute_error','Estimate the probability of words not yet observed','Absolute error in unseen probability mass',figs/'smoothing-unseen-mobile.png',mobile=True)
    theme();q=np.load(base/'results/example_reference.npy');p=np.load(base/'results/example_sgt.npy');mle_p=np.load(base/'results/example_mle.npy')
    # One common ordering: held-out frequency rank; estimators are not re-sorted.
    ids=np.argsort(-q);ids=ids[q[ids]>0];ranks=np.arange(1,len(ids)+1)
    fig,ax=plt.subplots(figsize=(11,5.8));fig.subplots_adjust(left=.11,right=.96,bottom=.19,top=.8)
    for values,label,color in [(q,'Held-out reference',FG),(mle_p,'MLE',COLORS['MLE']),(p,'Simple Good–Turing',COLORS['Simple Good–Turing'])]:
        positive=values[ids]>0
        ax.loglog(ranks[positive],values[ids][positive],'.',color=color,label=label,alpha=.45,markersize=1.7,rasterized=True)
    ax.set_xlabel('Word rank by held-out frequency');ax.set_ylabel('Unigram probability');ax.grid(alpha=.3)
    ax.set_title('A frequent head and a sparse, difficult tail',loc='left',fontsize=20,pad=22,weight='bold')
    ax.legend(frameon=False,markerscale=4,labelcolor=FG)
    fig.text(.11,.04,'1M-token draw · seed 17 · full training vocabulary + UNK · zero estimates omitted on log scale',color=MUTED,fontsize=9)
    fig.savefig(figs/'smoothing-zipf-profile.png',dpi=180);plt.close(fig)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--base',default='.')
    main(parser.parse_args().base)

