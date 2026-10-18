"""Run labelled synthetic late-data and checkpoint contracts, outside timing."""
from pathlib import Path
import argparse,json,time
from datetime import datetime,timezone
import pandas as pd
from nasa_streaming_counts import get_spark,start_query,journal_progress
from run_replay import progress_table,publish_file,flush_line

def example(stamp,status=200,size='10'):
    return f'example.invalid - - [01/Jul/1995:{stamp} +0000] "GET /fixture HTTP/1.0" {status} {size}\n'

def run(private_dir,project):
    private=Path(private_dir)
    if private.exists():raise ValueError('Synthetic test directory must be fresh')
    private.mkdir(parents=True);incoming=private/'input';incoming.mkdir();journal=private/'progress.jsonl';journal.touch()
    spark=get_spark('local[2]');spark.sparkContext.setLogLevel('ERROR');seen=set()
    query=start_query(spark,incoming,private/'checkpoint',private/'output');query_id=str(query.id);run_id=str(query.runId)
    fixtures=[example('00:00:10',size='-'),example('00:05:10'),
        example('00:04:20',404)+example('00:00:20',500)+'malformed fixture\n'+example('00:06:10').replace('01/Jul','32/Jul'),
        flush_line(int(datetime(1995,7,1,0,10,10,tzinfo=timezone.utc).timestamp()))]
    for i,text in enumerate(fixtures):
        if i==2:
            query.stop();query=start_query(spark,incoming,private/'checkpoint',private/'output')
            assert str(query.id)==query_id and str(query.runId)!=run_id
        p=private/f'fixture_{i}.log';p.write_text(text,encoding='utf-8');publish_file(p,incoming);query.processAllAvailable();journal_progress(query,journal,seen,'contract')
    query.stop();metrics=progress_table(journal);result=spark.read.parquet(str((private/'output').resolve())).toPandas()
    # Expected: first 200 + later 200 + within-watermark 404, and no old 500.
    assert int(result.requests.sum())==3
    assert result.groupby('status').requests.sum().to_dict()=={200:2,404:1}
    assert not result.duplicated(['window_start','status']).any()
    assert int(metrics.rows_dropped_by_watermark.sum())==1
    assert int(metrics.input_rows.sum())==7
    summary={'data_type':'Labelled synthetic fixtures, separate from NASA performance replay','input_lines':7,'accepted_requests':3,'malformed_lines':2,'too_late_dropped':1,'synthetic_flush_controls':1,'within_watermark_event_accepted':True,'old_closed_window_not_reopened':True,'graceful_checkpoint_restart_passed':True,'duplicate_final_window_keys':0,'state_eviction_observed':bool(metrics.state_rows_removed.sum()>0)}
    assert summary['state_eviction_observed']
    out=Path(project)/'results';out.mkdir(parents=True,exist_ok=True);(out/'stream_contract_tests.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');metrics.to_csv(out/'synthetic_contract_metrics.csv',index=False)
    spark.stop();print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--private-dir',required=True);ap.add_argument('--project',required=True);a=ap.parse_args();run(a.private_dir,a.project)
