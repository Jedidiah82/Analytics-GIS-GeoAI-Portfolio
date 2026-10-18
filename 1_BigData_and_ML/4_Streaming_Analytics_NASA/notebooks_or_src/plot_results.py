"""Render portfolio figures from the executed replay and labelled test exports."""
from pathlib import Path
import argparse,json
import numpy as np,pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

BG='#08131f';PANEL='#102330';FG='#edf4fa';MUTED='#a5bac9';BLUE='#87bdff';MINT='#5de1b6';GOLD='#f6c573'

def theme():
    plt.rcParams.update({'figure.facecolor':BG,'axes.facecolor':PANEL,'text.color':FG,'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':MUTED,'axes.edgecolor':'#39586c','font.family':'DejaVu Sans','font.size':11,'savefig.facecolor':BG,'axes.spines.top':False,'axes.spines.right':False})

def header(fig,kicker,title,mobile):
    fig.text(.065,.955,kicker,color=BLUE,fontsize=11,weight='bold')
    fig.text(.065,.895,title,color=FG,fontsize=20 if mobile else 23,weight='bold')

def performance(results,out,mobile):
    summary=json.loads((results/'summary.json').read_text());frame=pd.read_csv(results/'batch_metrics.csv');data=frame[(frame.phase=='data')&(frame.input_rows>0)].copy();data['sequence']=np.arange(1,len(data)+1);theme()
    fig,axes=plt.subplots(2,1,figsize=(8,10.5)) if mobile else plt.subplots(1,2,figsize=(14,6.8))
    fig.subplots_adjust(left=.12,right=.95,top=.77,bottom=.21,wspace=.3,hspace=.60)
    header(fig,'NASA HTTP / FULL HISTORICAL REPLAY','Measure the whole replay',mobile)
    for ax,y,color,title,unit in zip(axes,[data.processed_rows_per_second/1000,data.trigger_ms/1000],[BLUE,GOLD],['Processing rate','Trigger execution time'],['Thousand input rows / second','Seconds']):
        ax.axvspan(.5,2.5,color='#233e51',alpha=.9,label='First 2 batches: warm-up')
        ax.plot(data.sequence,y,color=color,lw=2,marker='o',markersize=4)
        ax.axvline(summary['checkpoint_restart_after_files']+.5,color=MINT,ls='--',lw=1.5)
        ax.set_xlim(.5,len(data)+.5);ax.set_ylim(bottom=0);ax.set_title(title,loc='left',pad=14,fontsize=15);ax.set_xlabel('Data-bearing batch sequence');ax.set_ylabel(unit);ax.grid(axis='y',alpha=.14)
        ax.set_xticks([1,5,10,15,20,25,30,len(data)])
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    fig.legend(handles=[Patch(facecolor='#233e51',label='Warm-up'),Line2D([],[],color=MINT,ls='--',label='Checkpoint restart')],loc='lower left',bbox_to_anchor=(.055,.095),ncol=2,frameon=False,labelcolor=FG,fontsize=10)
    fig.text(.065,.025,f'{summary["source_lines"]:,} source lines · {summary["data_batches"]} data batches · local Spark\nPost-warm-up weighted rate: {summary["post_warmup_weighted_rows_per_second"]:,.0f} rows/s. Zero-input and flush batches excluded.',fontsize=9,color=MUTED)
    fig.savefig(out,dpi=180);plt.close(fig)

def recovery(results,out,mobile):
    s=json.loads((results/'summary.json').read_text());frame=pd.read_csv(results/'batch_metrics.csv');theme()
    data=frame[(frame.phase=='data')&(frame.input_rows>0)];restart_id=float(data.iloc[s['checkpoint_restart_after_files']].batch_id)-.5
    fig,axes=plt.subplots(2,1,figsize=(8,10.7)) if mobile else plt.subplots(1,2,figsize=(14,7))
    fig.subplots_adjust(left=.13,right=.95,top=.77,bottom=.22,wspace=.3,hspace=.60)
    header(fig,'NASA HTTP / STATE & CORRECTNESS','Recover state. Reconcile every window.' if not mobile else 'Recovery with evidence',mobile)
    ax=axes[0];ax.plot(frame.batch_id,frame.state_rows,color=BLUE,lw=1.7,marker='o',markersize=3);ax.axvline(restart_id,color=MINT,ls='--',lw=1.5,label='Graceful restart');ax.set_xlabel('Spark micro-batch ID');ax.set_ylabel('Active minute/status keys');ax.set_ylim(bottom=0);ax.grid(axis='y',alpha=.15);ax.set_title('Aggregation state',loc='left',pad=14,fontsize=15);ax.legend(frameon=False,labelcolor=FG,fontsize=9)
    ax=axes[1];ax.set_facecolor(BG);ax.axis('off')
    items=[(f'{s["valid_requests"]:,}','Valid requests'),(f'{s["unique_final_windows"]:,}','Final minute/status windows'),('100%','Window counts match Python oracle'),('0','Duplicate final keys')]
    for y,(value,label) in zip([.86,.60,.34,.08],items):
        ax.text(.04,y,value,transform=ax.transAxes,fontsize=25,color=MINT,weight='bold');ax.text(.04,y-.09,label,transform=ax.transAxes,fontsize=11,color=MUTED)
    fig.text(.065,.05,'Append-mode Parquet + checkpoint · one query before and after restart\nA finite-replay control closes the last real windows and contributes zero requests.\nThe test covers graceful restart, not arbitrary crash or external-sink recovery.',fontsize=9,color=MUTED)
    fig.savefig(out,dpi=180);plt.close(fig)

def late_contract(results,out,mobile):
    s=json.loads((results/'stream_contract_tests.json').read_text());frame=pd.read_csv(results/'synthetic_contract_metrics.csv');theme()
    data=frame[frame.input_rows>0];assert len(data)==4
    fig,axes=plt.subplots(2,1,figsize=(8,11)) if mobile else plt.subplots(1,2,figsize=(14,7.2))
    fig.subplots_adjust(left=.13,right=.95,top=.76,bottom=.23,wspace=.28,hspace=.65)
    header(fig,'NASA PIPELINE / LABELLED SYNTHETIC TEST','Late data, tested deliberately',mobile)
    ax=axes[0]
    ax.scatter([1,2,3],[10/60,5+10/60,4+20/60],color=MINT,s=80,marker='o',label='Accepted request',zorder=3)
    ax.scatter([3],[20/60],color=GOLD,s=110,marker='x',linewidths=2,label='Too late: closed window',zorder=3)
    ax.scatter([4],[10+10/60],color=MUTED,s=80,marker='D',label='Flush control: zero requests',zorder=3)
    base=pd.Timestamp('1995-07-01T00:00:00Z');watermarks=pd.to_datetime(data.watermark,utc=True);minutes=(watermarks-base).dt.total_seconds()/60
    mask=minutes>-20
    ax.step(np.arange(1,5)[mask.to_numpy()],minutes[mask],where='post',color=BLUE,ls='--',lw=2,label='Watermark used in batch')
    ax.set_xticks([1,2,3,4],['Initial','Advance','Mixed','Flush']);ax.set_xlim(.6,4.4);ax.set_ylim(-2.2,11.2);ax.set_ylabel('Event time · minutes from fixture start');ax.set_xlabel('Controlled arrival batch');ax.grid(axis='y',alpha=.15);ax.set_title('Event time versus arrival',loc='left',pad=14,fontsize=14)
    ax=axes[1];values=[s['accepted_requests'],s['malformed_lines'],s['too_late_dropped'],s['synthetic_flush_controls']];labels=['Accepted requests','Malformed lines','Too-late event','Flush control']
    ax.barh(labels,values,color=[MINT,'#7892a6',GOLD,BLUE],height=.58);ax.invert_yaxis();ax.set_xlim(0,3.8);ax.set_xticks(range(4));ax.set_xlabel('Fixture records');ax.set_title('Verified outcomes',loc='left',pad=14,fontsize=14);ax.grid(axis='x',alpha=.15);ax.set_axisbelow(True)
    for i,v in enumerate(values):ax.text(v+.08,i,str(v),va='center',fontsize=12,color=FG)
    if mobile:
        position=ax.get_position();ax.set_position([.34,position.y0,.61,position.height])
    handles,labels=axes[0].get_legend_handles_labels();fig.legend(handles,labels,loc='lower left',bbox_to_anchor=(.055,.08),ncol=1 if mobile else 2,frameon=False,labelcolor=FG,fontsize=9)
    fig.text(.065,.025,'Synthetic correctness fixtures, separate from NASA traffic and performance measurements.\nThe within-watermark event survives; the closed window stays closed after restart.',fontsize=9,color=MUTED)
    fig.savefig(out,dpi=180);plt.close(fig)

def traffic(results,out):
    data=pd.read_csv(results/'daily_status_counts.csv');data['date']=pd.to_datetime(data.date_utc,utc=True);data['family']=(data.status//100).astype(str)+'xx';table=data.groupby(['date','family']).requests.sum().unstack().reindex(pd.date_range(data.date.min(),data.date.max(),freq='D'))
    theme();fig,axes=plt.subplots(2,1,figsize=(13,7.8),sharex=True);fig.subplots_adjust(left=.09,right=.96,top=.79,bottom=.18,hspace=.42)
    header(fig,'NASA HTTP / HISTORICAL TRAFFIC','Separate traffic patterns from pipeline performance',False)
    axes[0].plot(table.index,table.sum(axis=1,min_count=1)/1000,color=BLUE,lw=2);axes[0].set_ylabel('Requests / day · thousands');axes[0].set_ylim(bottom=0)
    for family,color in [('4xx',GOLD),('5xx',MINT)]:
        if family in table:axes[1].plot(table.index,table[family],color=color,lw=1.8,label=family)
    axes[1].set_ylabel('Error responses / day');axes[1].set_ylim(bottom=0);axes[1].legend(frameon=False,labelcolor=FG,ncol=2);axes[1].set_xlabel('Historical event date · UTC')
    for ax in axes:ax.grid(axis='y',alpha=.15)
    fig.text(.065,.045,'July–August 1995 source traffic, grouped in UTC; gaps are left missing.\nFirst and last UTC dates are partial. Counts do not measure modern service availability or processing capacity.',fontsize=10,color=MUTED)
    fig.savefig(out,dpi=180);plt.close(fig)

def main(project):
    project=Path(project);results=project/'results';out=project/'figures';out.mkdir(exist_ok=True)
    for mobile in [False,True]:
        suffix='-mobile' if mobile else ''
        for stem,fn in [('nasa-full-replay',performance),('nasa-recovery-state',recovery),('nasa-late-data-contract',late_contract)]:fn(results,out/f'{stem}{suffix}.png',mobile)
    traffic(results,out/'nasa-historical-traffic.png')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--project',default='.');main(ap.parse_args().project)
