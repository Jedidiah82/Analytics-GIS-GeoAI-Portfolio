from pathlib import Path
import sys,unittest,tempfile,json
from types import SimpleNamespace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'notebooks_or_src'))
from prepare_replay import parse_reference
from nasa_streaming_counts import parse_lines,get_spark,journal_progress
from pyspark.sql import functions as F

def line(stamp='01/Jul/1995:00:00:01 -0400',request='GET /sample HTTP/1.0',status='200',size='-'):
    return f'example.invalid - - [{stamp}] "{request}" {status} {size}'

class ParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spark=get_spark('local[2]');cls.spark.sparkContext.setLogLevel('ERROR')
    @classmethod
    def tearDownClass(cls):cls.spark.stop()
    def spark_row(self,text):return parse_lines(self.spark.range(1).select(F.lit(text).alias('value'))).first()
    def test_unknown_bytes_stay_null(self):
        row=self.spark_row(line());self.assertEqual(row.reason,'valid');self.assertIsNone(row.bytes)
        parsed,reason=parse_reference(line());self.assertEqual(reason,'valid');self.assertIsNone(parsed[2])
    def test_timezone_is_preserved(self):
        a=self.spark_row(line());b=self.spark_row(line(stamp='01/Jul/1995:04:00:01 +0000'))
        self.assertEqual(a.ts,b.ts)
        self.assertEqual(parse_reference(line())[0][0],parse_reference(line(stamp='01/Jul/1995:04:00:01 +0000'))[0][0])
    def test_legacy_request_without_protocol(self):
        self.assertEqual(self.spark_row(line(request='GET /sample')).reason,'valid')
    def test_invalid_structure_is_rejected(self):
        self.assertEqual(self.spark_row('not a log line').reason,'structure')
        self.assertEqual(parse_reference('not a log line')[1],'structure')
    def test_invalid_timestamp_is_rejected(self):
        bad=line(stamp='32/Jul/1995:00:00:00 -0400')
        self.assertEqual(self.spark_row(bad).reason,'timestamp');self.assertEqual(parse_reference(bad)[1],'timestamp')
    def test_invalid_status_is_rejected(self):
        self.assertEqual(self.spark_row(line(status='999')).reason,'structure')
    def test_bytes_overflow_is_rejected(self):
        bad=line(size=str(2**63))
        self.assertEqual(self.spark_row(bad).reason,'bytes_overflow');self.assertEqual(parse_reference(bad)[1],'bytes_overflow')
    def test_flush_control_is_explicit(self):
        self.assertFalse(self.spark_row(line()).is_control)
        self.assertTrue(self.spark_row(line().replace('example.invalid','__REPLAY_FLUSH__')).is_control)
    def test_idle_progress_does_not_hide_next_data_batch(self):
        idle={'id':'query','batchId':34,'numInputRows':0,'durationMs':{'triggerExecution':1}}
        real={'id':'query','batchId':34,'numInputRows':100000,'durationMs':{'addBatch':500,'triggerExecution':900}}
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'progress.jsonl';seen=set()
            journal_progress(SimpleNamespace(recentProgress=[idle]),p,seen,'restart')
            journal_progress(SimpleNamespace(recentProgress=[idle,real]),p,seen,'data')
            rows=[json.loads(line) for line in p.read_text().splitlines()]
            self.assertEqual(len(rows),1);self.assertEqual(rows[0]['numInputRows'],100000)
    def test_committed_empty_watermark_batch_is_retained(self):
        committed={'id':'query','batchId':35,'numInputRows':0,'durationMs':{'addBatch':500,'triggerExecution':900}}
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'progress.jsonl';seen=set();query=SimpleNamespace(recentProgress=[committed])
            journal_progress(query,p,seen,'data');journal_progress(query,p,seen,'data')
            self.assertEqual(len(p.read_text().splitlines()),1)

if __name__=='__main__':unittest.main()
