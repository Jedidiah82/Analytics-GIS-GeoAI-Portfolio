"""One checkpointed NASA event-time aggregation with an append Parquet sink.

Use run_replay.py for a bounded, measured historical replay. No host or request
path is retained in aggregate outputs. The special replay flush control is only
for finite-input finalisation, not a production watermark policy.
"""
from pathlib import Path
import argparse,json
from pyspark.sql import SparkSession,functions as F

PATTERN=r'^\S+\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"(.+)"\s+([1-5]\d{2})\s+(\d+|-)\s*$'

def get_spark(master='local[4]'):
    return (SparkSession.builder.master(master).appName('NASA corrected streaming')
        .config('spark.ui.enabled','false').config('spark.driver.bindAddress','127.0.0.1')
        .config('spark.driver.host','127.0.0.1').config('spark.sql.session.timeZone','UTC')
        .config('spark.sql.shuffle.partitions','4').config('spark.sql.legacy.timeParserPolicy','CORRECTED')
        .config('spark.sql.streaming.numRecentProgressUpdates','100').getOrCreate())

def parse_lines(lines):
    parsed=lines.select(F.col('value'),F.regexp_extract('value',PATTERN,1).alias('time_text'),
        F.regexp_extract('value',PATTERN,2).alias('request'),
        F.regexp_extract('value',PATTERN,3).cast('int').alias('status'),
        F.regexp_extract('value',PATTERN,4).alias('bytes_text'))
    parsed=parsed.withColumn('ts',F.try_to_timestamp('time_text',F.lit('dd/MMM/yyyy:HH:mm:ss Z')))
    parsed=parsed.withColumn('bytes',F.col('bytes_text').cast('long'))
    parsed=parsed.withColumn('reason',F.when(F.col('time_text')=='','structure')
        .when(F.col('ts').isNull(),'timestamp')
        .when((F.col('bytes_text')!='-')&F.col('bytes').isNull(),'bytes_overflow')
        .otherwise(F.lit('valid')))
    return parsed.withColumn('is_control',F.col('value').startswith('__REPLAY_FLUSH__ '))

def aggregate(parsed):
    return (parsed.filter(F.col('reason')=='valid').withWatermark('ts','2 minutes')
        .groupBy(F.window('ts','1 minute'),F.col('status'))
        .agg(F.sum(F.when(~F.col('is_control'),1).otherwise(0)).cast('long').alias('requests'))
        .filter(F.col('requests')>0)
        .select(F.col('window.start').alias('window_start'),F.col('window.end').alias('window_end'),'status','requests'))

def start_query(spark,input_dir,checkpoint,output_dir):
    lines=spark.readStream.format('text').option('maxFilesPerTrigger',1).option('pathGlobFilter','*.log').load(str(Path(input_dir).resolve()))
    return (aggregate(parse_lines(lines)).writeStream.outputMode('append').format('parquet')
        .option('checkpointLocation',str(Path(checkpoint).resolve()))
        .option('path',str(Path(output_dir).resolve())).start())

def journal_progress(query,path,seen,phase):
    """Persist after each drained file; de-duplicate batch IDs across restarts.

    Raw progress contains local paths and stays private. Public exports select
    only rates, durations, watermark, and state counters.
    """
    with Path(path).open('a',encoding='utf-8') as f:
        for progress in query.recentProgress:
            # An idle status can advertise the NEXT batch ID without executing
            # it. Do not reserve that ID before the real data batch commits.
            # Empty watermark-advance batches do have addBatch and are retained.
            if 'addBatch' not in progress.get('durationMs',{}):continue
            key=(progress['id'],progress['batchId'])
            if key in seen:continue
            seen.add(key);record=dict(progress);record['replay_phase']=phase
            f.write(json.dumps(record)+'\n')

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--input-dir',required=True);ap.add_argument('--checkpoint',required=True);ap.add_argument('--output-dir',required=True);ap.add_argument('--master',default='local[4]');args=ap.parse_args()
    spark=get_spark(args.master);query=start_query(spark,args.input_dir,args.checkpoint,args.output_dir)
    query.awaitTermination()
