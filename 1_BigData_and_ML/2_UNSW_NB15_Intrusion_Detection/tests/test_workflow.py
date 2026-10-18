import csv,sys,tempfile,unittest
from pathlib import Path
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from unsw_model_workflow import CLASSES,COLUMNS,FEATURES,canonical_category,metric_rows,summarize,read_validated,split_data

class MetricTests(unittest.TestCase):
    def test_source_label_contract(self):
        self.assertEqual(canonical_category(0,None),'Normal')
        self.assertEqual(canonical_category(0,' Normal '),'Normal')
        self.assertEqual(canonical_category(1,' Backdoors '),'Backdoor')
        self.assertEqual(canonical_category(1,' DoS '),'DoS')
        for y,c in [(1,None),(1,'Normal'),(0,'Generic'),(2,'Generic'),(1,'unknown')]:
            with self.assertRaises(ValueError):canonical_category(y,c)
    def test_macro_is_not_weighted_accuracy(self):
        actual=np.array([0]*90+[1]*10);pred=np.zeros(100,dtype=int)
        s,detail,cm=summarize(actual,pred,['Normal','Attack'])
        self.assertEqual(s['accuracy'],.9)
        self.assertAlmostEqual(s['macro_f1'],(180/190)/2)
        self.assertEqual(detail.loc[1,'recall'],0)
        self.assertEqual(cm.tolist(),[[90,0],[10,0]])
    def test_named_class_order_keeps_unpredicted_classes(self):
        rows=metric_rows(np.array([0,9]),np.array([0,0]),CLASSES)
        self.assertEqual(len(rows),10)
        self.assertEqual(rows.iloc[9]['class'],'Worms')
        self.assertEqual(rows.iloc[9]['support'],1)
        self.assertEqual(rows.iloc[9]['recall'],0)
    def test_features_exclude_targets_and_identifiers(self):
        self.assertEqual(FEATURES,['log_sbytes','log_dbytes','sttl','dttl'])
        self.assertFalse(set(FEATURES)&{'label','attack_cat','Stime','Ltime','srcip','dstip'})

class SparkContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from pyspark.sql import SparkSession
        cls.spark=SparkSession.builder.master('local[2]').appName('UNSW tests').config('spark.ui.enabled','false').config('spark.driver.bindAddress','127.0.0.1').config('spark.driver.host','127.0.0.1').config('spark.sql.session.timeZone','UTC').getOrCreate()
        cls.spark.sparkContext.setLogLevel('ERROR')
    @classmethod
    def tearDownClass(cls):cls.spark.stop()
    def fixture(self,folder,label=0,category='',ttl=31):
        values={c:'0' for c in COLUMNS};values.update(sbytes='999',dbytes='0',sttl=str(ttl),dttl='29',Stime='1422000000',Ltime='1422000010',label=str(label),attack_cat=category)
        p=Path(folder)/'fixture.csv'
        with p.open('w',newline='') as f:csv.writer(f).writerow([values[c] for c in COLUMNS])
        return p
    def test_actual_spark_label_and_feature_transform(self):
        with tempfile.TemporaryDirectory() as d:
            p=self.fixture(d,1,' Backdoors ')
            row=read_validated(self.spark,p).first()
            self.assertEqual(row.class_name,'Backdoor');self.assertEqual(row.label_multi,2.)
            self.assertAlmostEqual(row.log_sbytes,np.log(1000));self.assertEqual(row.log_dbytes,0.)
    def test_spark_rejects_disagreement_and_invalid_range(self):
        for label,category,ttl in [(0,'Generic',31),(1,'',31),(0,'',256)]:
            with tempfile.TemporaryDirectory() as d:
                with self.assertRaises(ValueError):read_validated(self.spark,self.fixture(d,label,category,ttl))
    def test_temporal_boundary_excludes_crossing_flow(self):
        data=self.spark.createDataFrame([(9.,9.,'a'),(9.,11.,'b'),(10.,12.,'c')],['Stime','Ltime','record_hash'])
        train,test=split_data(data,'capture_holdout',10,42)
        self.assertEqual([r.record_hash for r in train.collect()],['a'])
        self.assertEqual([r.record_hash for r in test.collect()],['c'])
    def test_duplicate_groups_never_cross_random_split(self):
        data=self.spark.createDataFrame([(str(i//2),) for i in range(200)],['record_hash'])
        a,b=split_data(data,'group_random_70_30',10,42)
        self.assertEqual(a.count()+b.count(),200)
        self.assertEqual(a.join(b,'record_hash').count(),0)

if __name__=='__main__':unittest.main()
