import unittest
import tempfile,sys
from pathlib import Path
from unittest.mock import patch
import geopandas as gpd
import numpy as np
from shapely.geometry import box, Polygon, GeometryCollection, LineString
from pipeline import exposure, polygonal, CRS

class ExposureContracts(unittest.TestCase):
    def test_split_and_overlapping_hazards_count_once(self):
        b=gpd.GeoDataFrame({'building_id':['one','touch','outside']},geometry=[box(0,0,2,2),box(2,0,3,2),box(4,4,5,5)],crs=CRS)
        h=gpd.GeoDataFrame(geometry=[box(-1,-1,1.5,3),box(.5,-1,2,3)],crs=CRS)
        a,p=exposure(b,h)
        self.assertEqual(set(a.index),{'one'})
        self.assertAlmostEqual(a['one'],4)
        self.assertEqual(len(p),2)
    def test_positive_sliver_retained(self):
        b=gpd.GeoDataFrame({'building_id':['small']},geometry=[box(0,0,1,1)],crs=CRS)
        h=gpd.GeoDataFrame(geometry=[box(.999,0,2,1)],crs=CRS)
        a,_=exposure(b,h);self.assertAlmostEqual(a['small'],.001)
    def test_empty_hazard(self):
        b=gpd.GeoDataFrame({'building_id':['one']},geometry=[box(0,0,1,1)],crs=CRS)
        h=gpd.GeoDataFrame(geometry=[box(2,2,3,3)],crs=CRS)
        a,_=exposure(b,h);self.assertTrue(a.empty)
    def test_collection_preserves_polygon_only(self):
        g=polygonal(GeometryCollection([box(0,0,1,1),LineString([(3,3),(4,4)])]))
        self.assertAlmostEqual(g.area,1)
    def test_assignment_and_exact_dedup(self):
        import shapely,pandas as pd
        county=box(0,0,10,10)
        b=gpd.GeoSeries([box(-1,1,1,2),box(3,3,4,4),box(4,4,3,3)],crs=CRS)
        self.assertTrue(b.representative_point().covered_by(county).all())
        dup=pd.Series(shapely.to_wkb(shapely.normalize(b.to_numpy()))).duplicated()
        self.assertEqual(int(dup.sum()),1)
    def test_nonempty_output_refused(self):
        import pipeline
        with tempfile.TemporaryDirectory() as d:
            (Path(d)/'stale.json').write_text('{}')
            with patch.object(sys,'argv',['pipeline.py','--source','unused','--boundary','unused','--cache','unused','--output',d]):
                with self.assertRaisesRegex(SystemExit,'not empty'):pipeline.main()

if __name__=='__main__':unittest.main(verbosity=2)
