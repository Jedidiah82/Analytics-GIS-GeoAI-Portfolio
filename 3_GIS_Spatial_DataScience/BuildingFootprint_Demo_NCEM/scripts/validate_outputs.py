"""Independent saved-file validation; does not rerun or modify analysis."""
import argparse,json
from pathlib import Path
import geopandas as gpd
import numpy as np
import pandas as pd
import shapely

def main():
    p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);a=p.parse_args()
    s=json.loads((a.run/'summary.json').read_text());m=json.loads((a.run/'run_manifest.json').read_text())
    b=gpd.read_file(a.run/'spatial/wake_buildings.gpkg');f=gpd.read_file(a.run/'spatial/wake_flood.gpkg');c=gpd.read_file(a.run/'spatial/wake_boundary.gpkg')
    assert b.crs.to_epsg()==32119 and b.crs.axis_info[0].unit_name=='metre'
    assert f.is_valid.all() and (f.area>0).all() and c.is_valid.all()
    assert b.building_id.is_unique and b.is_valid.all() and (b.area>0).all()
    assert b.representative_point().covered_by(c.geometry.union_all()).all()
    assert np.allclose(b.area,b.area_m2,rtol=0,atol=1e-6)
    assert int(b.sfha_exposed.sum())==s['sfha_exposed_buildings'] and len(b)==s['county_buildings']
    assert abs(100*b.sfha_exposed.mean()-s['percent_exposed'])<1e-10
    assert np.array_equal(b.sfha_exposed.to_numpy(),b.sfha_overlap_m2.to_numpy()>0)
    h=f[f.SFHA_TF=='T'].geometry.union_all()
    shapely.prepare(h)
    alternate=shapely.intersects(h,b.geometry.to_numpy())
    possible=np.flatnonzero(alternate)
    alternate[possible] &= ~shapely.touches(b.geometry.to_numpy()[possible],h)
    assert np.array_equal(alternate,b.sfha_exposed.to_numpy())
    # Recalculate an even sample of exposed footprints against a dissolved hazard.
    ids=np.linspace(0,int(b.sfha_exposed.sum())-1,100,dtype=int)
    sample=b[b.sfha_exposed].iloc[np.unique(ids)]
    area=shapely.area(shapely.intersection(sample.geometry.to_numpy(),h))
    assert np.allclose(area,sample.sfha_overlap_m2,rtol=1e-7,atol=.001)
    sen=pd.read_csv(a.run/'exposure_sensitivity.csv')
    assert sen.exposed_buildings.is_monotonic_decreasing and (sen.denominator==len(b)).all()
    assert m['status']=='SUCCESS' and all(m['checks'].values())
    result={'status':'PASS','saved_buildings_checked':len(b),'independent_topology_checked':len(b),'independent_area_sample':len(sample),'checks':['CRS and units','unique IDs','valid positive geometries','county membership','saved area reconciliation','summary arithmetic','dissolved-hazard exposure identity','100-building area reconciliation','sensitivity monotonicity','manifest completion']}
    (a.run/'validation.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))

if __name__=='__main__':main()
