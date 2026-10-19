"""ThamesWatch: discover EA water-quality sampling points within 20 km of Southend.
Run: python search_stations.py
Requires: pip install requests
No RAG classifications or pollutant claims are made by this script.
"""
import csv
import json
import math
import os
import sys
from datetime import datetime, timezone
from urllib.parse import urljoin
import requests

BASE = 'https://environment.data.gov.uk/water-quality/data/sampling-point'
LAT, LON, RADIUS_KM = 51.54, 0.71, 20.0
OUT = 'output'
os.makedirs(OUT, exist_ok=True)

def distance_km(a,b,c,d):
    p1,p2=math.radians(a),math.radians(c)
    dp=math.radians(c-a); dl=math.radians(d-b)
    h=math.sin(dp/2)**2+math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 6371.0088*2*math.asin(min(1,math.sqrt(h)))

def pick(obj,*names):
    for n in names:
        if n in obj and obj[n] is not None:
            val=obj[n]
            if isinstance(val,dict):
                return val.get('value') or val.get('label') or val.get('notation') or ''
            return val
    return ''

def fetch_all():
    url=BASE; params={'latitude':LAT,'longitude':LON,'radius':RADIUS_KM,'limit':250}
    seen=set(); results=[]
    for page in range(1,101):
        response=requests.get(url,params=params,timeout=45,headers={'Accept':'application/json','User-Agent':'ThamesWatchAI/1.0'})
        print("HTTP status:", response.status_code)
print("Request URL:", response.url)
print("Allowed methods:", response.headers.get("Allow", "Not supplied"))
print("Response preview:", response.text[:500])
        response.raise_for_status()
        data=response.json()
        if isinstance(data,list):
            items=data; nxt=None
        elif isinstance(data,dict):
            items=data.get('items',data.get('results',[]))
            nxt=data.get('next') or data.get('nextPage')
            if isinstance(nxt,dict): nxt=nxt.get('href') or nxt.get('url')
        else: raise ValueError('Unexpected API response shape')
        if not isinstance(items,list): raise ValueError('API items is not a list')
        results.extend(items)
        print(f'Page {page}: {len(items)} stations')
        if not nxt: break
        next_url=urljoin(response.url,nxt)
        if next_url in seen: raise RuntimeError('Pagination loop detected')
        seen.add(next_url); url=next_url; params=None
    else: raise RuntimeError('Page safety limit reached; results incomplete')
    return results

def main():
    print('Requesting official sampling points around Southend (20 km)...')
    raw=fetch_all()
    now=datetime.now(timezone.utc).isoformat()
    with open(f'{OUT}/raw_sampling_points.json','w',encoding='utf-8') as f:
        json.dump({'retrieved_utc':now,'request':{'latitude':LAT,'longitude':LON,'radius_km':RADIUS_KM},'items':raw},f,indent=2,ensure_ascii=False)
    rows=[]; missing=0
    for obj in raw:
        if not isinstance(obj,dict): continue
        coords=obj.get('lat') or obj.get('latitude')
        lng=obj.get('long') or obj.get('longitude')
        if coords is None or lng is None:
            missing+=1; continue
        try: lat=float(coords); lon=float(lng)
        except (ValueError,TypeError): missing+=1; continue
        dist=distance_km(LAT,LON,lat,lon)
        if dist>RADIUS_KM+0.05: continue
        rows.append({'station_id':pick(obj,'notation','pointNotation','samplingPointNotation','id'),
            'station_name':pick(obj,'label','name','samplingPointName'),
            'latitude':lat,'longitude':lon,'distance_km':round(dist,2),
            'sample_type':pick(obj,'samplingPointType','type'),
            'source_url':pick(obj,'@id','uri','id') or BASE,
            'retrieved_utc':now})
    rows.sort(key=lambda r:r['distance_km'])
    with open(f'{OUT}/southend_stations_20km.csv','w',newline='',encoding='utf-8') as f:
        w=csv.DictWriter(f,fieldnames=['station_id','station_name','latitude','longitude','distance_km','sample_type','source_url','retrieved_utc'])
        w.writeheader();w.writerows(rows)
    print(f'Found {len(rows)} points with valid coordinates inside 20 km; {missing} lacked parseable coordinates.')
    print(f'Files saved in {OUT}/')
    if not raw: print('WARNING: API returned no stations; check the endpoint and query parameter conventions.')
    if missing: print('WARNING: Some records lacked coordinates; inspect raw_sampling_points.json.')

if __name__=='__main__':
    try: main()
    except Exception as e:
        print(f'FAILED: {e}',file=sys.stderr)
        sys.exit(1)
