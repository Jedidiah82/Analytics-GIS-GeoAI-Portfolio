"""Wake County footprint exposure. No network access required during analysis."""
from __future__ import annotations
import argparse, hashlib, importlib.metadata, json, platform, sys, time
from datetime import datetime, timezone
from pathlib import Path
import geopandas as gpd
import ijson
import numpy as np
import pandas as pd
import shapely
from shapely.geometry import shape, Polygon, MultiPolygon

CRS = 'EPSG:32119'  # NAD83 / North Carolina; metres

def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(8*1024*1024), b''): h.update(b)
    return h.hexdigest()

def polygonal(g):
    if g is None or g.is_empty: return Polygon()
    if isinstance(g,(Polygon,MultiPolygon)): return g
    parts=[]
    for x in getattr(g,'geoms',[]):
        p=polygonal(x)
        if isinstance(p,Polygon) and not p.is_empty: parts.append(p)
        elif isinstance(p,MultiPolygon): parts.extend(p.geoms)
    return shapely.union_all(parts) if parts else Polygon()

def positive_pairs(buildings, hazards):
    """Return positive-area intersections; preserve source building identity."""
    pairs=gpd.sjoin(buildings[['building_id','geometry']],hazards[['geometry']],how='inner',predicate='intersects')
    if pairs.empty:
        return gpd.GeoDataFrame({'building_id':[],'overlap_m2':[]},geometry=[],crs=buildings.crs)
    right=hazards.geometry.loc[pairs.index_right].to_numpy()
    geom=shapely.intersection(pairs.geometry.to_numpy(),right)
    out=gpd.GeoDataFrame({'building_id':pairs.building_id.to_numpy()},geometry=geom,crs=buildings.crs)
    out=out[out.area>0].copy()
    return out

def exposure(buildings,hazards):
    pairs=positive_pairs(buildings,hazards)
    if pairs.empty: return pd.Series(dtype=float),pairs
    # Dissolve intersections per original building: overlapping hazard polygons cannot inflate area.
    dissolved=pairs.dissolve(by='building_id')
    return dissolved.area,pairs

def coords(g):
    c=g['coordinates']
    def walk(a):
        if a and isinstance(a[0],(float,int)): yield a
        else:
            for v in a: yield from walk(v)
    return walk(c)

def extract(raw,boundary,cache):
    """Stream 1.3 GB source without loading the statewide layer into memory."""
    bounds=boundary.to_crs(4326).total_bounds
    x0,y0,x1,y1=bounds
    records=[]; geoms=[]; count=0
    with raw.open('rb') as fp:
        for i,feat in enumerate(ijson.items(fp,'features.item',use_float=True)):
            count=i+1; geom=feat.get('geometry')
            if not geom: continue
            # Input is polygonal; inspect every vertex, including multipart geometries.
            xy=np.asarray(list(coords(geom)),dtype=float)
            if not len(xy): continue
            if xy[:,0].max()<x0 or xy[:,0].min()>x1 or xy[:,1].max()<y0 or xy[:,1].min()>y1: continue
            records.append({'building_id':f'MSNC-{i:07d}',**feat.get('properties',{})})
            geoms.append(shape(geom))
            if count%500000==0: print(f'Scanned {count:,}; candidates {len(records):,}',flush=True)
    frame=gpd.GeoDataFrame(records,geometry=geoms,crs=4326)
    frame.to_file(cache,layer='raw_candidates',driver='GPKG')
    return frame,count

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',type=Path,required=True,help='Original project folder containing data_raw and hazards')
    ap.add_argument('--boundary',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--cache',type=Path,required=True)
    a=ap.parse_args(); start=time.time()
    if a.output.exists() and any(a.output.iterdir()):
        raise SystemExit('Output directory is not empty. Choose a new run directory to prevent stale-result confusion.')
    a.output.mkdir(parents=True,exist_ok=True);a.cache.mkdir(parents=True,exist_ok=True)
    raw=a.source/'data_raw/microsoft_footprints.geojson'; flood_path=a.source/'hazards/flood_fema_nfhl.gpkg'
    inputs={str(p):{'bytes':p.stat().st_size,'sha256':digest(p)} for p in [raw,flood_path,a.boundary]}
    key=hashlib.sha256(json.dumps(inputs,sort_keys=True).encode()).hexdigest()
    cache=a.cache/f'{key[:16]}-candidates.gpkg'; cm=a.cache/f'{key[:16]}-cache.json'
    county=gpd.read_file(a.boundary)
    assert len(county)==1 and str(county.iloc[0].GEOID)=='37183'
    county=county.to_crs(CRS); cb=county.geometry.union_all();assert cb.is_valid
    print('Inputs hashed; county boundary loaded.',flush=True)
    if cache.exists() and cm.exists():
        buildings=gpd.read_file(cache,layer='raw_candidates');state_count=json.loads(cm.read_text())['raw_statewide_features']
    else:
        buildings,state_count=extract(raw,county,cache)
        cm.write_text(json.dumps({'raw_statewide_features':state_count}))
    qa={'raw_statewide_features':state_count,'bbox_candidates':len(buildings)}
    buildings=buildings.to_crs(CRS)
    qa['invalid_candidates_before_repair']=int((~buildings.is_valid).sum())
    buildings.geometry=buildings.geometry.make_valid().map(polygonal)
    good=~buildings.is_empty & buildings.is_valid & (buildings.area>0)
    qa['unusable_candidates']=int((~good).sum());buildings=buildings[good].copy()
    selected=buildings.representative_point().covered_by(cb)
    qa['outside_county_representative_point']=int((~selected).sum());buildings=buildings[selected].copy()
    normalized=shapely.to_wkb(shapely.normalize(buildings.geometry.to_numpy()))
    dupe=pd.Series(normalized).duplicated().to_numpy()
    qa['exact_geometry_duplicates_removed']=int(dupe.sum());buildings=buildings[~dupe].copy().reset_index(drop=True)
    buildings['area_m2']=buildings.area;buildings['perimeter_m']=buildings.length
    buildings['small_under_30m2']=buildings.area_m2<30
    qa['county_buildings']=len(buildings);qa['small_under_30m2_retained']=int(buildings.small_under_30m2.sum())
    qa['boundary_crossing_buildings']=int((~buildings.covered_by(cb)).sum())
    print('County footprint QA:',qa,flush=True)
    flood=gpd.read_file(flood_path).to_crs(CRS)
    assert {'FLD_ZONE','SFHA_TF','ZONE_SUBTY'}<=set(flood.columns)
    qa['flood_source_polygons']=len(flood);qa['invalid_flood_geometries_before_repair']=int((~flood.is_valid).sum())
    flood.geometry=flood.geometry.make_valid().map(polygonal)
    flood=gpd.clip(flood,county,keep_geom_type=True).reset_index(drop=True)
    flood=flood[(~flood.is_empty)&(flood.area>0)].copy().reset_index(drop=True)
    sfha=flood[flood.SFHA_TF.astype(str).str.upper()=='T'].copy()
    assert len(sfha)>0
    assert flood.SFHA_TF.astype(str).str.upper().isin(['T','F']).all(), 'Unexpected SFHA flags require review'
    qa['county_flood_polygons']=len(flood);qa['county_sfha_polygons']=len(sfha)
    zone_counts=flood.groupby(['FLD_ZONE','SFHA_TF','ZONE_SUBTY'],dropna=False).size().rename('polygon_count').reset_index()
    zone_counts.to_csv(a.output/'fema_zone_inventory.csv',index=False)
    print('Computing positive-area exposure...',flush=True)
    overlap,pairs=exposure(buildings,sfha)
    buildings['sfha_overlap_m2']=buildings.building_id.map(overlap).fillna(0)
    buildings['sfha_overlap_pct']=100*buildings.sfha_overlap_m2/buildings.area_m2
    buildings['sfha_exposed']=buildings.sfha_overlap_m2>0
    # Independent topology check: interior-interior intersection on the dissolved hazard.
    union=sfha.geometry.union_all();shapely.prepare(union)
    independent=shapely.intersects(union,buildings.geometry.to_numpy())
    possible=np.flatnonzero(independent)
    independent[possible] &= ~shapely.touches(buildings.geometry.to_numpy()[possible],union)
    assert np.array_equal(independent,buildings.sfha_exposed.to_numpy()), 'Independent exposure reconciliation failed'
    mapped=flood.geometry.union_all();shapely.prepare(mapped)
    buildings['representative_point_in_fema_coverage']=shapely.covers(mapped,buildings.representative_point().to_numpy())
    n=len(buildings);e=int(buildings.sfha_exposed.sum())
    qa['positive_intersection_pieces']=len(pairs)
    qa['invalid_output_geometries']=int((~buildings.is_valid).sum())
    qa['unique_building_ids']=buildings.building_id.nunique()
    qa['representative_points_outside_fema_coverage']=int((~buildings.representative_point_in_fema_coverage).sum())
    qa['exposed_small_under_30m2']=int((buildings.sfha_exposed&buildings.small_under_30m2).sum())
    assert n==qa['unique_building_ids'] and qa['invalid_output_geometries']==0
    assert 0<=e<=n and (buildings.sfha_overlap_m2<=buildings.area_m2+1e-4).all()
    assert buildings.representative_point().covered_by(cb).all()
    summary={'county_geoid':'37183','county_name':'Wake County, North Carolina','analysis_crs':CRS,
        'county_buildings':n,'sfha_exposed_buildings':e,'percent_exposed':100*e/n,
        'exposed_footprint_area_m2':float(buildings.sfha_overlap_m2.sum()),
        'coverage_representative_points_pct':100*float(buildings.representative_point_in_fema_coverage.mean()),
        'definition':'Positive-area footprint intersection with archived FEMA SFHA_TF=T polygons; representative-point county assignment.'}
    sensitivity=[]
    for label,mask in [('Any positive area',buildings.sfha_overlap_m2>0),('At least 1 m²',buildings.sfha_overlap_m2>=1),('At least 10% footprint',buildings.sfha_overlap_pct>=10)]:
        sensitivity.append({'definition':label,'exposed_buildings':int(mask.sum()),'denominator':n,'percent':100*mask.mean()})
    pd.DataFrame(sensitivity).to_csv(a.output/'exposure_sensitivity.csv',index=False)
    byzone=[]
    for zone,group in sfha.groupby('FLD_ZONE'):
        ar,_=exposure(buildings,group)
        byzone.append({'fema_zone':zone,'distinct_buildings':len(ar),'note':'Zone counts may overlap; do not sum to obtain county total.'})
    pd.DataFrame(byzone).to_csv(a.output/'exposure_by_zone.csv',index=False)
    for name,field in [('summary',summary),('qa',qa)]:
        (a.output/f'{name}.json').write_text(json.dumps(field,indent=2),encoding='utf8')
    spatial=a.output/'spatial';spatial.mkdir(exist_ok=True)
    buildings.to_file(spatial/'wake_buildings.gpkg',layer='buildings',driver='GPKG')
    flood.to_file(spatial/'wake_flood.gpkg',layer='flood_zones',driver='GPKG')
    county.to_file(spatial/'wake_boundary.gpkg',layer='county',driver='GPKG')
    versions={p:importlib.metadata.version(p) for p in ['geopandas','shapely','pyproj','pyogrio','pandas','numpy','ijson']}
    audit={'status':'SUCCESS','completed_utc':datetime.now(timezone.utc).isoformat(),'duration_seconds':time.time()-start,
        'inputs':inputs,'boundary_provenance':json.loads(a.boundary.with_suffix('.provenance.json').read_text(encoding='utf8')) if a.boundary.with_suffix('.provenance.json').exists() else {'note':'No boundary metadata sidecar supplied; consult the input snapshot provenance.'},
        'python':sys.version,'platform':platform.platform(),'dependencies':versions,'checks':{
          'unique_ids':True,'county_assignment':True,'valid_geometry':True,'bounded_area':True,'independent_union_reconciliation':True},
        'summary':summary,'qa':qa}
    (a.output/'run_manifest.json').write_text(json.dumps(audit,indent=2),encoding='utf8')
    print(json.dumps(summary,indent=2),flush=True);print('SUCCESS: independent reconciliation passed.',flush=True)

if __name__=='__main__': main()
