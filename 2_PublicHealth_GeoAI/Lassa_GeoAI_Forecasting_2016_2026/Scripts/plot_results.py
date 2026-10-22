"""Render source-backed charts. Observed backtests remain in a private folder."""
import argparse
import json
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.colors import Normalize, LinearSegmentedColormap
from matplotlib.patches import Patch

BG,PANEL,FG,MUTED='#08131f','#10212f','#f3f8fc','#b5c8d6'
COLORS={'Actual':'#f3f8fc','Seasonal naive':'#f4c47e','SARIMA':'#64e5b9',
        'Prophet':'#c4a4ff','Poisson XGBoost':'#64e5b9','Zero baseline':'#9bb0c5','Recent mean':'#85bfff'}


def theme():
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'figure.facecolor':BG,
        'axes.facecolor':PANEL,'axes.edgecolor':'#355063','axes.labelcolor':MUTED,
        'text.color':FG,'xtick.color':MUTED,'ytick.color':MUTED,'grid.color':'#2b4052',
        'axes.spines.top':False,'axes.spines.right':False,'savefig.facecolor':BG})


def backtest_plot(frame,output,mobile=False):
    theme();origins=sorted(frame.origin.unique())
    fig,axes=plt.subplots(3,1,figsize=(7,11),sharey=True) if mobile else plt.subplots(1,3,figsize=(14,5.7),sharey=True)
    fig.subplots_adjust(left=.09,right=.97,top=.77,bottom=.23,hspace=.65,wspace=.15)
    fig.text(.09,.94,'LASSA FEVER / NATIONAL BACKTEST',color=COLORS['SARIMA'],fontsize=10,weight='bold')
    fig.text(.09,.865,'Test forecasts against unseen months' if not mobile else 'Test before projecting',fontsize=22,weight='bold')
    for ax,origin in zip(axes,origins):
        fold=frame[frame.origin==origin];actual=fold.drop_duplicates('date').sort_values('date')
        ax.plot(actual.date,actual.actual,label='Observed',color=FG,lw=2,marker='o',ms=3)
        for model,group in fold.groupby('model'):
            ax.plot(group.date,group.prediction,label=model,color=COLORS[model],lw=1.8,
                linestyle='--' if model=='Seasonal naive' else '-')
        year=int(origin[:4])+1;ax.set_title(f'{year} holdout',loc='left',fontsize=12,pad=14)
        ticks=actual.date.iloc[[0,3,6,9]];ax.set_xticks(ticks,['Jan','Apr','Jul','Oct'])
        ax.grid(axis='y',alpha=.5);ax.set_ylim(bottom=0)
        ax.set_xlabel('Month')
    axes[0].set_ylim(0, max(frame.actual.max(),frame.prediction.max())*1.12)
    axes[0].set_ylabel('Monthly recorded cases')
    handles,labels=axes[0].get_legend_handles_labels()
    fig.legend(handles,labels,loc='lower left',bbox_to_anchor=(.08,.065),ncol=2 if mobile else len(labels),frameon=False,labelcolor=FG)
    fig.text(.09,.025,'12-month forecasts from Dec 2019, 2020 and 2021\nEach model sees only observations available at its origin.',color=MUTED,fontsize=9)
    fig.savefig(output,dpi=180);plt.close(fig)


def county_benchmark(summary,output,mobile=False):
    theme();rows=summary[summary.level=='County'].copy()
    order=['Zero baseline','Seasonal naive','Recent mean','Poisson XGBoost']
    rows=rows.set_index('model').loc[order]
    fig,axes=plt.subplots(2,1,figsize=(7,9)) if mobile else plt.subplots(1,2,figsize=(13,5.8))
    fig.subplots_adjust(left=.28 if mobile else .19,right=.92,top=.76,bottom=.22,wspace=.4,hspace=.55)
    fig.text(.08,.94,'LASSA FEVER / COUNTY BENCHMARK',color=COLORS['SARIMA'],fontsize=10,weight='bold')
    fig.text(.08,.86,'Different errors reward different forecasts' if not mobile else 'Benchmark the county model',fontsize=21 if not mobile else 18,weight='bold')
    for ax,key,title in zip(axes,['mae','rmse'],['Mean absolute error','Root mean squared error']):
        ax.barh(order,rows[key],color=[COLORS[m] for m in order],height=.6)
        ax.invert_yaxis();ax.grid(axis='x',alpha=.4);ax.set_axisbelow(True)
        ax.set_xlim(0,float(rows[['mae','rmse']].to_numpy().max())*1.25);ax.set_title(title,loc='left',pad=15)
        ax.set_xlabel('Cases per county-month · lower is better')
        for i,value in enumerate(rows[key]):ax.text(value+rows[key].max()*.025,i,f'{value:.3f}',va='center',fontsize=11)
    fig.text(.08,.08,'540 county-month forecasts · 15 counties × 36 held-out months\nHistorical zeros retained. MAE and RMSE emphasize different errors.',color=MUTED,fontsize=9)
    fig.savefig(output,dpi=180);plt.close(fig)


def coverage_map(panel,boundary_path,output,mobile=False):
    import geopandas as gpd
    theme();g=gpd.read_file(boundary_path).to_crs(32629)
    g['county']=g.FIRST_CCNA.str.strip()
    totals=panel.sum().rename('recorded_cases')
    g=g.merge(totals,left_on='county',right_index=True,how='left',validate='one_to_one')
    if g.recorded_cases.isna().any():raise ValueError('Unmatched county; never convert missing map joins to zero')
    fig,axes=plt.subplots(2,1,figsize=(7.5,13),gridspec_kw={'height_ratios':[1.2,1]}) if mobile else plt.subplots(1,2,figsize=(13,7.3),gridspec_kw={'width_ratios':[1.25,1]})
    fig.subplots_adjust(left=.06,right=.96,top=.82,bottom=.14,wspace=.30,hspace=.3)
    if mobile:
        position=axes[1].get_position()
        axes[1].set_position([.31,position.y0,.65,position.height])
    fig.text(.06,.945,'LASSA FEVER / HISTORICAL GEOGRAPHY',color=COLORS['SARIMA'],fontsize=10,weight='bold')
    fig.text(.06,.88,'Every county belongs in the historical record' if not mobile else 'All 15 counties retained',fontsize=21 if not mobile else 20,weight='bold')
    positive=g.recorded_cases>0;g.loc[~positive].plot(ax=axes[0],color='#253d50',edgecolor='#7794a5',linewidth=.6,hatch='///')
    g.loc[positive].plot(ax=axes[0],color='#50cfa5',edgecolor='#92b0b7',linewidth=.6)
    for name in ['Bong','Grand Bassa','Nimba']:
        record=g[g.county==name].iloc[0];point=record.geometry.representative_point()
        axes[0].text(point.x,point.y,name.replace(' ','\n'),ha='center',va='center',fontsize=8,color=FG,weight='bold')
    axes[0].axis('off');axes[0].legend(handles=[Patch(facecolor='#50cfa5',label='Recorded cases in the historical period'),Patch(facecolor='#253d50',edgecolor='#7794a5',hatch='///',label='No recorded outbreaks: historical zero')],loc='lower left',bbox_to_anchor=(0,-.04),frameon=False,labelcolor=FG,fontsize=8)
    ordered=totals.sort_values(ascending=False)
    axes[1].barh(ordered.index,ordered.values,color=[COLORS['SARIMA'] if v else '#536f84' for v in ordered],height=.65)
    axes[1].invert_yaxis();axes[1].set_xlim(0,totals.max()*1.17);axes[1].set_xlabel('Recorded cases, Dec 2016–Dec 2022')
    axes[1].tick_params(axis='y',labelsize=9);axes[1].grid(axis='x',alpha=.4);axes[1].set_axisbelow(True)
    for i,value in enumerate(ordered):axes[1].text(value+1.5,i,str(int(value)),va='center',fontsize=9)
    fig.text(.06,.04,'251 recorded cases · 73 months · 7 counties with zero recorded outbreaks\nHistorical counts, not population-adjusted rates or future outbreak probabilities.',color=MUTED,fontsize=9)
    fig.savefig(output,dpi=180);plt.close(fig)


def projection_plot(panel,projections,selected,output):
    theme();future=projections[projections.model==selected].copy()
    fig,ax=plt.subplots(figsize=(14,7));fig.subplots_adjust(left=.08,right=.97,top=.78,bottom=.2)
    history=panel.sum(axis=1);ax.plot(history.index,history,color=FG,label='Observed monthly records',lw=1.8)
    required={'SARIMA','Prophet'}
    if not required.issubset(set(projections.model)):
        raise ValueError('Both verified SARIMA and Prophet projections are required')
    start=pd.Timestamp(history.index.min()).replace(day=1)
    end=pd.Timestamp(projections.date.max())+pd.offsets.MonthBegin(1)
    for year in range(start.year-1,end.year+1):
        left=max(start,pd.Timestamp(year,12,1))
        right=min(end,pd.Timestamp(year+1,4,1))
        if left<right: ax.axvspan(left,right,color='#f4c47e',alpha=.075,zorder=0)
    for model in ['SARIMA','Prophet']:
        group=projections[projections.model==model].sort_values('date')
        if len(group)!=48 or group.date.duplicated().any():
            raise ValueError('Expected 48 unique monthly projections per model')
        ax.plot(group.date,group.prediction,color=COLORS[model],
                label=f'{model} projection'+(' (selected)' if model==selected else ''),
                lw=2,ls='-' if model==selected else '--')
        ax.fill_between(group.date,group.lower,group.upper,color=COLORS[model],alpha=.10,
                label=f'{model} nominal 95% interval')
    ax.plot([],[],color='#f4c47e',lw=7,alpha=.35,label='Dry season (Dec-Mar)')
    ax.axvline(history.index.max(),color=MUTED,ls='--',lw=1)
    ax.set_ylim(bottom=0);ax.set_ylabel('Monthly case counts');ax.grid(axis='y',alpha=.4)
    ax.legend(frameon=False,labelcolor=FG,fontsize=9,loc='upper left')
    fig.text(.08,.94,'LASSA FEVER / HISTORICAL-ORIGIN PROJECTION',color=COLORS['SARIMA'],fontsize=10,weight='bold')
    fig.text(.08,.86,'SARIMA and Prophet through 2026',fontsize=22,weight='bold')
    fig.text(.08,.045,'Origin: December 2022 · horizon: January 2023–December 2026\nNo observed 2023–2026 outcomes supplied; bands are model-based, not calibrated guarantees.',fontsize=9,color=MUTED)
    fig.savefig(output,dpi=180);plt.close(fig)


def main(project,private_output,input_path,boundaries=None):
    from lassa_forecasting_pipeline import load_panel
    project,private_output=Path(project),Path(private_output)
    output=project/'Figures';output.mkdir(exist_ok=True)
    n=pd.read_csv(private_output/'national_backtests.csv',parse_dates=['date'])
    n=n[n.evaluation=='Annual rolling origin']
    summary=pd.read_csv(project/'results/backtest_summary.csv')
    manifest=json.loads((project/'results/manifest.json').read_text())
    panel=load_panel(input_path,'2022-12-31')
    for mobile,suffix in [(False,''),(True,'-mobile')]:
        backtest_plot(n,output/f'lassa-national-backtest{suffix}.png',mobile)
        county_benchmark(summary,output/f'lassa-county-benchmark{suffix}.png',mobile)
        if boundaries:coverage_map(panel,boundaries,output/f'lassa-historical-coverage{suffix}.png',mobile)
    f=pd.read_csv(project/'results/national_projections.csv',parse_dates=['date'])
    projection_plot(panel,f,manifest['selected_national'],output/'lassa-origin-projection.png')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--project',default='.')
    ap.add_argument('--private-output',required=True);ap.add_argument('--input',required=True)
    ap.add_argument('--boundaries');args=ap.parse_args()
    main(args.project,args.private_output,args.input,args.boundaries)
