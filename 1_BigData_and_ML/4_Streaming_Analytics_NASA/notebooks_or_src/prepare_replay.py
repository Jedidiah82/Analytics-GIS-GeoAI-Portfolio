"""Build event-time-ordered replay chunks and an independent Python oracle.

All raw lines/chunks remain private. Python parsing supplies the comparison
counts; the executed Spark query separately parses the raw replay lines.
"""
from pathlib import Path
from collections import Counter
from datetime import datetime,timezone,timedelta
import argparse,hashlib,json,re,itertools,time

LINE=re.compile(r'^\S+\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"(.+)"\s+([1-5]\d{2})\s+(\d+|-)\s*$')
STAMP=re.compile(r'^(\d{2})/([A-Z][a-z]{2})/(\d{4}):(\d{2}):(\d{2}):(\d{2}) ([+-])(\d{2})(\d{2})$')
MONTHS={name:i+1 for i,name in enumerate(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])}

def parse_reference(line):
    match=LINE.fullmatch(line.rstrip('\r\n'))
    if not match:return None,'structure'
    stamp,request,status,size=match.groups();t=STAMP.fullmatch(stamp)
    if not t:return None,'timestamp'
    day,month,year,hour,minute,second,sign,zh,zm=t.groups()
    try:
        offset=(int(zh)*60+int(zm))*(1 if sign=='+' else -1)
        if int(zh)>23 or int(zm)>59:raise ValueError('Invalid offset')
        date=datetime(int(year),MONTHS[month],int(day),int(hour),int(minute),int(second),tzinfo=timezone(timedelta(minutes=offset)))
        epoch=int(date.timestamp())
    except (ValueError,KeyError,OverflowError):return None,'timestamp'
    size=None if size=='-' else int(size)
    if size is not None and size>2**63-1:return None,'bytes_overflow'
    return (epoch,int(status),size),'valid'

def prepare(sources,private_dir,chunk_rows=100000):
    private=Path(private_dir);private.mkdir(parents=True,exist_ok=True)
    backlog=private/'backlog'
    if backlog.exists() and any(backlog.iterdir()):raise ValueError('Use a fresh private directory; no overwrite of prior replay')
    backlog.mkdir(exist_ok=True);records=[];invalid=[];truth=Counter();reasons=Counter();inputs=[];dash=0;start=time.perf_counter()
    for source in sources:
        p=Path(source);count=0;digest=hashlib.sha256()
        with p.open('rb') as f:
            for raw in f:
                digest.update(raw);line=raw.decode('utf-8',errors='replace').rstrip('\r\n');count+=1
                parsed,reason=parse_reference(line);reasons[reason]+=1
                if parsed is None:invalid.append(line)
                else:
                    epoch,status,size=parsed;records.append((epoch,line));truth[(epoch//60*60,status)]+=1;dash+=size is None
        inputs.append({'name':p.name,'sha256':digest.hexdigest(),'lines':count})
        print('Prepared source',p.name,count,'lines',flush=True)
    records.sort(key=lambda x:x[0])
    # Invalid rows are deliberately included, not silently dropped from replay.
    stream=itertools.chain(invalid,(line for _,line in records));chunks=[]
    for i in itertools.count():
        rows=list(itertools.islice(stream,chunk_rows))
        if not rows:break
        p=backlog/f'chunk_{i:04d}.log';p.write_text('\n'.join(rows)+'\n',encoding='utf-8');chunks.append({'name':p.name,'rows':len(rows),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    import csv
    with (private/'reference_windows.csv').open('w',newline='') as f:
        writer=csv.writer(f);writer.writerow(['epoch_minute','status','requests'])
        writer.writerows((minute,status,n) for (minute,status),n in sorted(truth.items()))
    info={'inputs':inputs,'total_lines':sum(reasons.values()),'parse_counts':dict(reasons),'unknown_bytes_rows':dash,'event_min_epoch':records[0][0],'event_max_epoch':records[-1][0],'chunk_rows':chunk_rows,'chunks':chunks,'preparation_seconds':time.perf_counter()-start,'order':'Globally sorted by event time; invalid lines included at the start; no traffic rows invented'}
    (private/'input_manifest.json').write_text(json.dumps(info,indent=2),encoding='utf-8');print(json.dumps({k:v for k,v in info.items() if k not in ['chunks','inputs']},indent=2),flush=True)
    return info

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--sources',nargs='+',required=True);ap.add_argument('--private-dir',required=True);ap.add_argument('--chunk-rows',type=int,default=100000);a=ap.parse_args();prepare(a.sources,a.private_dir,a.chunk_rows)
