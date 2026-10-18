"""Publication figures from executed Wake County outputs; offline and deterministic."""
import argparse,json
from pathlib import Path
import numpy as np,pandas as pd,geopandas as gpd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Patch,Rectangle
from matplotlib.lines import Line2D
from shapely.geometry import box

INK='#152e42';BLUE='#3b87af';PALE='#e0edf3';AMBER='#b54d19';GRAY='#a5afb6'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':11,'text.color':INK,'axes.labelcolor':INK,'axes.edgecolor':'#b5c3cc','xtick.color':INK,'ytick.color':INK,'savefig.facecolor':'white'})

def scale(ax,length,label):
    x0,x1=ax.get_xlim();y0,y1=ax.get_ylim();x=x0+(x1-x0)*.06;y=y0+(y1-y0)*.05
    ax.plot([x,x+length],[y,y],color=INK,lw=2.5,zorder=9)
    ax.text(x+length/2,y+(y1-y0)*.016,label,ha='center',va='bottom',fontsize=9,bbox={'facecolor':'white','edgecolor':'none','alpha':.85,'pad':1},zorder=10)

def save(fig,path):
    fig.savefig(path.with_suffix('.png'),dpi=190,bbox_inches='tight')
    fig.savefig(path.with_suffix('.pdf'),bbox_inches='tight')
    plt.close(fig)

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
    s=json.loads((a.run/'summary.json').read_text());qa=json.loads((a.run/'qa.json').read_text())
    b=gpd.read_file(a.run/'spatial/wake_buildings.gpkg');f=gpd.read_file(a.run/'spatial/wake_flood.gpkg');c=gpd.read_file(a.run/'spatial/wake_boundary.gpkg')
    sf=f[f.SFHA_TF=='T'];moderate=f[(f.SFHA_TF=='F')&f.ZONE_SUBTY.fillna('').str.contains('0.2 PCT',case=False)]
    pts=b.representative_point();ex=b[b.sfha_exposed];ep=ex.representative_point()
    grid=pd.DataFrame({'gx':(ep.x//2000).astype(int),'gy':(ep.y//2000).astype(int)})
    hot=grid.value_counts().reset_index(name='n').sort_values(['n','gx','gy'],ascending=[False,True,True])
    centers=[]
    for row in hot.itertuples():
        xy=np.array([(row.gx+.5)*2000,(row.gy+.5)*2000])
        if all(np.linalg.norm(xy-z)>6000 for z in centers):centers.append(xy)
        if len(centers)==2:break
    assert len(centers)==2
    fig=plt.figure(figsize=(14,9));gs=fig.add_gridspec(2,2,left=.04,right=.98,bottom=.13,top=.78,width_ratios=[1.15,1],wspace=.08,hspace=.24)
    ax=fig.add_subplot(gs[:,0]);c.plot(ax=ax,facecolor='#f5f7f8',edgecolor='#697f8e',lw=.8)
    ax.scatter(pts.x,pts.y,s=.06,c=GRAY,alpha=.65,rasterized=True)
    if len(moderate):moderate.plot(ax=ax,color=PALE,edgecolor='none',zorder=2)
    sf.plot(ax=ax,color=BLUE,edgecolor='none',zorder=3)
    ax.scatter(ep.x,ep.y,s=1.8,c=AMBER,zorder=4,rasterized=True)
    ax.set_axis_off();ax.set_title('County overview',loc='left',fontsize=12,pad=10);scale(ax,10000,'10 km')
    ax.annotate('Grid N',xy=(.08,.94),xytext=(.08,.84),xycoords='axes fraction',ha='center',arrowprops={'arrowstyle':'->','color':INK},fontsize=9)
    extents=[]
    for i,xy in enumerate(centers):
        extent=box(xy[0]-1000,xy[1]-1000,xy[0]+1000,xy[1]+1000);extents.append(list(extent.bounds))
        d=fig.add_subplot(gs[i,1]);c.plot(ax=d,color='#f5f7f8',edgecolor='none')
        for layer,color in [(moderate,PALE),(sf,BLUE)]:
            sub=layer[layer.intersects(extent)]
            if len(sub):sub.plot(ax=d,color=color,edgecolor='none',alpha=.8)
        sub=b[b.intersects(extent)]
        sub[~sub.sfha_exposed].plot(ax=d,color='#697d8b',edgecolor='white',linewidth=.15,zorder=3)
        sub[sub.sfha_exposed].plot(ax=d,color=AMBER,edgecolor='white',linewidth=.2,zorder=4)
        x0,y0,x1,y1=extent.bounds;d.set_xlim(x0,x1);d.set_ylim(y0,y1);d.set_axis_off();scale(d,500,'500 m')
        d.set_title(f'Detail {chr(65+i)} · Footprints and mapped zones',loc='left',fontsize=11,pad=6)
        ax.add_patch(Rectangle((x0,y0),2000,2000,fill=False,edgecolor=INK,lw=1.3,zorder=6))
        ax.text(x1+600,y1,chr(65+i),weight='bold',fontsize=12,zorder=7)
    fig.text(.045,.95,'WAKE COUNTY / SPATIAL DATA ENGINEERING',fontsize=10,weight='bold',color=BLUE)
    fig.text(.045,.905,'Building footprints meet the floodplain.',fontsize=25,weight='bold')
    fig.text(.045,.855,f"{s['county_buildings']:,} footprints   /   {s['sfha_exposed_buildings']:,} intersect mapped SFHAs   /   {s['percent_exposed']:.2f}%",fontsize=15)
    handles=[Patch(facecolor=BLUE,label='Special Flood Hazard Area'),Patch(facecolor=PALE,label='0.2% annual-chance zone'),Patch(facecolor=AMBER,label='Footprint intersecting SFHA'),Patch(facecolor='#697d8b',label='Other footprint')]
    fig.legend(handles=handles,loc='lower center',bbox_to_anchor=(.5,.075),ncol=2,frameon=False,fontsize=10)
    fig.text(.045,.025,'Sources: Microsoft US Building Footprints (ODbL); archived FEMA NFHL; US Census TIGERweb boundary.\nNAD83 / North Carolina (metres). Historical screening demonstration; not observed flooding or a parcel-level determination.',fontsize=8,color='#526775')
    save(fig,a.output/'wake-exposure-atlas')
    # A vertically arranged companion is readable on narrow screens.
    from PIL import Image
    # Figures remain native plots; mobile detail uses the same input geometries.
    fig,axs=plt.subplots(2,1,figsize=(6,13));fig.subplots_adjust(left=.04,right=.96,top=.9,bottom=.15,hspace=.18)
    for i,ax in enumerate(axs):
        extent=box(*extents[i]);sub=b[b.intersects(extent)]
        for layer,color in [(moderate,PALE),(sf,BLUE)]:
            v=layer[layer.intersects(extent)]
            if len(v):v.plot(ax=ax,color=color,edgecolor='none')
        sub[~sub.sfha_exposed].plot(ax=ax,color='#697d8b',edgecolor='white',lw=.1)
        sub[sub.sfha_exposed].plot(ax=ax,color=AMBER,edgecolor='white',lw=.2)
        ax.set_xlim(extents[i][0],extents[i][2]);ax.set_ylim(extents[i][1],extents[i][3]);ax.set_axis_off();scale(ax,500,'500 m');ax.set_title(f'Detail {chr(65+i)} · 2 × 2 km',loc='left',fontsize=12)
    fig.suptitle('Wake County · Building exposure',fontsize=18,weight='bold',y=.97)
    fig.legend(handles=handles,loc='lower center',ncol=1,frameon=False,fontsize=12,bbox_to_anchor=(.5,.015))
    save(fig,a.output/'wake-exposure-details-mobile')
    sens=pd.read_csv(a.run/'exposure_sensitivity.csv')
    fig,axs=plt.subplots(1,2,figsize=(13,6),gridspec_kw={'width_ratios':[1,1.15]});fig.subplots_adjust(left=.06,right=.96,top=.73,bottom=.23,wspace=.36)
    ax=axs[0];vals=sens.exposed_buildings.to_numpy();labels=['Any positive area','At least 1 m²','At least 10% of footprint']
    ax.barh(labels[::-1],vals[::-1],color=BLUE,height=.5);ax.set_xlim(0,vals.max()*1.22)
    for y,v in enumerate(vals[::-1]):ax.text(v+vals.max()*.025,y,f'{v:,}',va='center',fontsize=11)
    ax.set_xlabel('Distinct buildings');ax.set_title('Exposure depends on the overlap rule',loc='left',fontsize=12,pad=14);ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
    ax=axs[1];x=ex.sfha_overlap_pct.to_numpy();bins=[0,1,10,25,50,75,100.000001];counts=np.histogram(x,bins=bins)[0]
    labels=['<1%','1–<10%','10–<25%','25–<50%','50–<75%','75–100%']
    ax.bar(labels,counts,color=AMBER,width=.68)
    ax.set_ylim(0,max(counts)*1.23)
    for i,v in enumerate(counts):ax.text(i,v+max(counts)*.025,f'{v:,}',ha='center',fontsize=10)
    ax.set_ylabel('Exposed buildings');ax.set_xlabel('Share of each footprint inside mapped SFHA');ax.set_title('How much of each footprint overlaps?',loc='left',fontsize=12,pad=14);ax.spines[['top','right']].set_visible(False)
    fig.text(.06,.93,'METHOD SENSITIVITY / SAME COUNTY DENOMINATOR',fontsize=10,color=BLUE,weight='bold')
    fig.text(.06,.86,'A count with a definition you can inspect.',fontsize=23,weight='bold')
    fig.text(.06,.11,f"All rules use {s['county_buildings']:,} distinct Wake County footprints. Positive-area intersection excludes boundary-only contact.\nOverlap percentages describe footprint geometry, not damage, flood depth, or probability of a particular building flooding.",fontsize=10,color='#526775')
    save(fig,a.output/'wake-exposure-sensitivity')
    fig,axs=plt.subplots(2,1,figsize=(7,9));fig.subplots_adjust(left=.32,right=.95,top=.86,bottom=.16,hspace=.55)
    ax=axs[0];ax.barh(['At least 10%\nof footprint','At least 1 m²','Any positive area'],vals[::-1],color=BLUE,height=.5)
    ax.set_xlim(0,vals.max()*1.23)
    for y,v in enumerate(vals[::-1]):ax.text(v+vals.max()*.025,y,f'{v:,}',va='center',fontsize=10)
    ax.set_xlabel('Distinct buildings');ax.set_title('Three overlap rules',loc='left',fontsize=12,pad=12);ax.spines[['top','right','left']].set_visible(False);ax.tick_params(axis='y',length=0)
    ax=axs[1];ax.bar(range(6),counts,color=AMBER);ax.set_xticks(range(6),['<1','1–<10','10–<25','25–<50','50–<75','75–100']);ax.tick_params(axis='x',labelsize=8);ax.set_ylim(0,max(counts)*1.23)
    for i,v in enumerate(counts):ax.text(i,v+max(counts)*.025,f'{v:,}',ha='center',fontsize=9)
    ax.set_ylabel('Exposed buildings');ax.set_xlabel('Footprint inside SFHA (%)');ax.set_title('Overlap share',loc='left',fontsize=12,pad=12);ax.spines[['top','right']].set_visible(False)
    fig.text(.07,.95,'WAKE COUNTY / EXPOSURE SENSITIVITY',fontsize=10,color=BLUE,weight='bold')
    fig.text(.07,.9,'The definition changes the count.',fontsize=16,weight='bold')
    fig.text(.07,.035,f"Same denominator: {s['county_buildings']:,} county footprints.\nHistorical geometric exposure; not observed flooding.\nPositive-area overlap excludes boundary-only contact.",fontsize=9,color='#526775')
    save(fig,a.output/'wake-exposure-sensitivity-mobile')
    (a.output/'figure_metadata.json').write_text(json.dumps({'detail_extents_epsg32119':extents,'selection':'Two highest-count 2 km exposure-point grid cells, separated by at least 6 km; illustrative, not a risk ranking.','histogram_bins_pct':bins,'histogram_counts':counts.tolist()},indent=2))
    print('Figures saved:',a.output)

if __name__=='__main__': main()
