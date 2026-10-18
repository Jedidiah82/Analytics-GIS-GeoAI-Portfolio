"""Optional source refresh. Keep the packaged boundary for exact reproduction."""
import argparse,json
from datetime import datetime,timezone
from pathlib import Path
import requests

p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args()
if a.output.exists():raise SystemExit('Refusing to overwrite an existing snapshot; choose a new filename.')
url='https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1'
response=requests.get(url+'/query',params={'where':"GEOID='37183'",'outFields':'*','outSR':4326,'f':'geojson'},timeout=90)
response.raise_for_status();data=response.json()
assert len(data['features'])==1 and data['features'][0]['properties']['GEOID']=='37183'
a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(data),encoding='utf8')
meta=requests.get(url,params={'f':'pjson'},timeout=90);meta.raise_for_status()
a.output.with_suffix('.provenance.json').write_text(json.dumps({'retrieved_utc':datetime.now(timezone.utc).isoformat(),'query_url':response.url,'layer_metadata':meta.json()},indent=2),encoding='utf8')
print('Saved a new boundary snapshot:',a.output)
