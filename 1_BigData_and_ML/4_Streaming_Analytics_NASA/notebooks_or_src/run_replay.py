"""Execute a bounded file replay, graceful checkpoint restart, and reconciliation."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,hashlib,json,os,platform,shutil,time
import numpy as np,pandas as pd,pyspark
from pyspark.sql import functions as F
from nasa_streaming_counts import get_spark,start_query,parse_lines,journal_progress

def publish_file(source,input_dir):
    source=Path(source);target=Path(input_dir)/source.name
    if target.exists():raise ValueError('Refusing to replace an already published input file')
    temp=Path(input_dir)/('.'+source.name+'.tmp');shutil.copyfile(source,temp);os.replace(temp,target)

def flush_line(epoch):
    stamp=datetime.fromtimestamp(epoch,tz=timezone.utc).strftime('%d/%b/%Y:%H:%M:%S +0000')
    return f'__REPLAY_FLUSH__ - - [{stamp}] "GET /synthetic-flush HTTP/1.0" 599 0\n'

def progress_table(path):
    rows=[]
    for line in Path(path).read_text(encoding='utf-8').splitlines():
        j=json.loads(line);state=j.get('stateOperators',[]);d=j.get('durationMs',{});event=j.get('eventTime',{})
        rows.append({'batch_id':j['batchId'],'run_id':j['runId'],'phase':j['replay_phase'],'timestamp':j['timestamp'],
            'input_rows':j['numInputRows'],'processed_rows_per_second':j.get('processedRowsPerSecond'),
            'input_rows_per_second':j.get('inputRowsPerSecond'),'trigger_ms':d.get('triggerExecution'),
            'add_batch_ms':d.get('addBatch'),'watermark':event.get('watermark'),
            'state_rows':sum(s.get('numRowsTotal',0) for s in state),
            'state_memory_bytes':sum(s.get('memoryUsedBytes',0) for s in state),
            'state_rows_removed':sum(s.get('numRowsRemoved',0) for s in state),
            'rows_dropped_by_watermark':sum(s.get('numRowsDroppedByWatermark',0) for s in state)})
    frame=pd.DataFrame(rows).sort_values('batch_id').reset_index(drop=True)
    if frame.batch_id.duplicated().any():raise AssertionError('Duplicate progress batch IDs')
    return frame

def run(private_dir,project,master='local[4]',execution_name='execution'):
    private=Path(private_dir);project=Path(project);info=json.loads((private/'input_manifest.json').read_text())
    if Path(execution_name).name!=execution_name:raise ValueError('Execution name must be one directory name')
    runtime=private/execution_name
    if runtime.exists():raise ValueError('Use a fresh execution directory; previous replay state is preserved')
    runtime.mkdir();incoming=runtime/'input';incoming.mkdir();checkpoint=runtime/'checkpoint';sink=runtime/'counts';journal=runtime/'progress.jsonl';journal.touch()
    spark=get_spark(master);spark.sparkContext.setLogLevel('ERROR');seen=set();start=time.perf_counter()
    query=start_query(spark,incoming,checkpoint,sink);first_id=str(query.id);first_run=str(query.runId)
    chunks=info['chunks'];restart_at=len(chunks)//2;restart_seconds=None
    for i,chunk in enumerate(chunks):
        if i==restart_at:
            query.stop();t=time.perf_counter();query=start_query(spark,incoming,checkpoint,sink)
            assert str(query.id)==first_id and str(query.runId)!=first_run
            query.processAllAvailable();journal_progress(query,journal,seen,'restart')
            restart_seconds=time.perf_counter()-t
            print('Restarted from same checkpoint after',i,'files',flush=True)
        t=time.perf_counter();publish_file(private/'backlog'/chunk['name'],incoming);query.processAllAvailable()
        journal_progress(query,journal,seen,'data')
        print(f'Completed chunk {i+1}/{len(chunks)}: {chunk["rows"]:,} rows, {time.perf_counter()-t:.2f}s drain',flush=True)
    # Explicit finite-replay control advances event time so final real windows
    # can become immutable. It contributes zero requests to the aggregation.
    control=runtime/'flush.log';control.write_text(flush_line(info['event_max_epoch']+240),encoding='utf-8')
    publish_file(control,incoming);query.processAllAvailable();journal_progress(query,journal,seen,'flush')
    replay_seconds=time.perf_counter()-start;query.stop()
    frame=progress_table(journal)
    data=frame[(frame.phase=='data')&(frame.input_rows>0)].copy()
    assert len(data)==len(chunks) and int(data.input_rows.sum())==info['total_lines']
    assert int(frame.rows_dropped_by_watermark.sum())==0,'Unexpected late traffic in chronological replay'
    observed=spark.read.parquet(str(sink.resolve())).toPandas()
    observed['epoch_minute']=pd.to_datetime(observed.window_start,utc=True).astype('int64')//10**9
    observed=observed[['epoch_minute','status','requests']].sort_values(['epoch_minute','status']).reset_index(drop=True)
    expected=pd.read_csv(private/'reference_windows.csv').sort_values(['epoch_minute','status']).reset_index(drop=True)
    assert not observed.duplicated(['epoch_minute','status']).any(),'Duplicate final window keys'
    pd.testing.assert_frame_equal(observed,expected,check_dtype=False)
    parsed=parse_lines(spark.read.text(str((private/'backlog').resolve())))
    quality={r['reason']:r['count'] for r in parsed.groupBy('reason').count().collect()}
    assert quality==info['parse_counts'],'Independent Python/Spark parsing disagrees'
    unknown=parsed.filter((F.col('reason')=='valid')&F.col('bytes').isNull()).count()
    assert unknown==info['unknown_bytes_rows']
    post=data.iloc[2:];weighted_rate=float(post.input_rows.sum()/(post.trigger_ms.sum()/1000))
    results=project/'results';results.mkdir(parents=True,exist_ok=True)
    frame.to_csv(results/'batch_metrics.csv',index=False)
    pd.DataFrame([{'reason':k,'rows':v} for k,v in sorted(quality.items())]).to_csv(results/'parse_quality.csv',index=False)
    # Public traffic summaries only; fine-grained windows and raw input stay private.
    observed['date_utc']=pd.to_datetime(observed.epoch_minute,unit='s',utc=True).dt.strftime('%Y-%m-%d')
    observed.groupby(['date_utc','status'],as_index=False).requests.sum().to_csv(results/'daily_status_counts.csv',index=False)
    observed.groupby('status',as_index=False).requests.sum().to_csv(results/'status_counts.csv',index=False)
    summary={'source_lines':info['total_lines'],'valid_requests':quality.get('valid',0),'rejected_lines':sum(v for k,v in quality.items() if k!='valid'),
        'unknown_bytes_rows':unknown,'data_batches':len(data),'warmup_batches_excluded':2,'post_warmup_batches':len(post),
        'post_warmup_weighted_rows_per_second':weighted_rate,'post_warmup_trigger_p50_ms':float(post.trigger_ms.median()),
        'post_warmup_trigger_p95_ms':float(post.trigger_ms.quantile(.95)),'post_warmup_min_rows_per_second':float(post.processed_rows_per_second.min()),
        'post_warmup_max_rows_per_second':float(post.processed_rows_per_second.max()),'replay_wall_seconds':replay_seconds,
        'replay_wall_rows_per_second':info['total_lines']/replay_seconds,'peak_state_rows':int(frame.state_rows.max()),
        'final_state_rows':int(frame.iloc[-1].state_rows),'late_rows_in_ordered_replay':int(frame.rows_dropped_by_watermark.sum()),
        'checkpoint_restart_after_files':restart_at,'restart_to_idle_seconds':restart_seconds,'query_id_preserved':True,'run_id_changed':True,
        'unique_final_windows':len(observed),'reconciliation':'Every final minute/status count matches an independent Python parser; no duplicate final keys',
        'throughput_definition':'Post-warm-up raw input rows / sum of their triggerExecution durations; excludes zero-input and synthetic flush batches',
        'finite_flush':'One synthetic control event at maximum real event time + 240 seconds; contributes zero requests; not a performance batch',
        'order':'Event-time-sorted historical replay; not original arrival order or a live source'}
    (results/'summary.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
    manifest={'run_date':time.strftime('%Y-%m-%d'),'inputs':info['inputs'],'chunk_rows':info['chunk_rows'],'chunks':info['chunks'],
        'parser':'Common-log structure + valid timestamp/status; request protocol optional; unknown bytes remain null',
        'query':{'window':'1 minute','watermark':'2 minutes','output_mode':'append','sink':'native Parquet file sink','max_files_per_trigger':1,'shuffle_partitions':4},
        'execution':{'master':master,'single_machine':True,'platform':platform.system(),'processor':platform.processor(),'java_version':spark._jvm.java.lang.System.getProperty('java.version'),'max_jvm_heap_bytes':spark._jvm.java.lang.Runtime.getRuntime().maxMemory()},
        'versions':{'python':platform.python_version(),'pyspark':pyspark.__version__,'pandas':pd.__version__,'numpy':np.__version__},
        'code_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (project/'notebooks_or_src').glob('*.py')},
        'scope':'Full local July and August NASA source files; event-time-sorted finite replay; graceful checkpoint restart; no crash fault injection'}
    (results/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    spark.stop();print(json.dumps(summary,indent=2),flush=True)

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--private-dir',required=True);ap.add_argument('--project',required=True);ap.add_argument('--master',default='local[4]');ap.add_argument('--execution-name',default='execution');a=ap.parse_args();run(a.private_dir,a.project,a.master,a.execution_name)
