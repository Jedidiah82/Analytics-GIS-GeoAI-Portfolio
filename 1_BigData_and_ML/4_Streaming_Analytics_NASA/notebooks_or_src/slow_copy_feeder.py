"""Optional manual feeder: deterministic order, atomic publish, no overwrites.

Feed the event-time-ordered chunks created by prepare_replay.py. The measured
experiment uses run_replay.py, which drains each file rather than sleeping.
"""
from pathlib import Path
import argparse,time
from run_replay import publish_file

def feed(source,destination,interval=2.,pattern='*.log'):
    if interval<0:raise ValueError('Interval must be nonnegative')
    files=sorted(Path(source).glob(pattern))
    if not files:raise ValueError('No input files matched')
    destination=Path(destination);destination.mkdir(parents=True,exist_ok=True)
    for i,file in enumerate(files):
        publish_file(file,destination);print('Published',file.name,flush=True)
        if i+1<len(files):time.sleep(interval)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--src',required=True);p.add_argument('--dst',required=True);p.add_argument('--interval',type=float,default=2.);p.add_argument('--pattern',default='*.log');a=p.parse_args();feed(a.src,a.dst,a.interval,a.pattern)
