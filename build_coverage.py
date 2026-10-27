"""Build coverage only; never change rainfall values or ranking results."""
import argparse, json, hashlib
from pathlib import Path
import pandas as pd
import numpy as np

def build(rain, metadata, out):
    files=sorted(Path(rain).glob('1985-2014/Rainfall_*.csv'))
    assert len(files)==30, 'Need 30 yearly CSVs'
    frames=[]; provenance=[]
    for f in files:
        d=pd.read_csv(f,dtype=str,keep_default_na=False)
        assert set(d.date.str[:4])=={f.stem[-4:]}
        frames.append(d);provenance.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest()))
    d=pd.concat(frames,ignore_index=True)
    existing=set(d.station_id)
    later_names={}
    for f in sorted(Path(rain).glob('2015-current/Rainfall_*.csv')):
        later=pd.read_csv(f,dtype=str,keep_default_na=False,usecols=['station_id','station_name'])
        later_names.update(dict(later[['station_id','station_name']].drop_duplicates('station_id').values))
        provenance.append(dict(file=f.name,sha256=hashlib.sha256(f.read_bytes()).hexdigest(),purpose='station inventory only; no post-2014 observations scored'))
    extra=[dict(station_id=sid,station_name=name,date='1985-01-01',flag='absent',rainfall_mm='') for sid,name in later_names.items() if sid not in existing]
    d=pd.concat([d,pd.DataFrame(extra)],ignore_index=True)
    assert not d.duplicated(['station_id','date']).any(),'Ambiguous duplicate station dates'
    days=pd.date_range('1985-01-01','2014-12-31'); expected=len(days)
    d['valid']=d.flag.isin(['observed','trace_as_zero']) & pd.to_numeric(d.rainfall_mm,errors='coerce').ge(0)
    m=pd.read_excel(metadata,dtype=str).fillna('')
    code=m['รหัสสถานี / WMO'].str.strip()
    fix=code.eq('4003201/48401') & m['ชื่อสถานี'].str.contains('ตากฟ้า')
    code.loc[fix]='400301/48401' # Existing documented metadata correction; no coordinate guessing.
    m['id']=code.str.extract(r'^(\d{6})(?:\s*/|$)')[0]
    stations=[]; allgaps=[]; annual=[]
    for sid,g in d.groupby('station_id',sort=True):
        valid=set(g.loc[g.valid,'date']); mask=np.array([x.strftime('%Y-%m-%d') not in valid for x in days])
        missing=int(mask.sum());passed=missing*5<=expected
        hit=m[m.id.eq(sid)];lat=lon=None;issue=''
        if len(hit)!=1:issue='ไม่พบพิกัด' if len(hit)==0 else 'รหัสซ้ำใน metadata ต้องยืนยันพิกัด'
        else:
            lat=pd.to_numeric(hit.iloc[0].Latitude,errors='coerce');lon=pd.to_numeric(hit.iloc[0].Longitude,errors='coerce')
            if not (np.isfinite(lat) and np.isfinite(lon) and 5<=lat<=21 and 97<=lon<=106):
                lat=lon=None;issue='พิกัดไม่ถูกต้องหรืออยู่นอกกรอบตรวจสอบประเทศไทย'
        ranges=[]; start=None
        for i,bad in enumerate(np.r_[mask,False]):
            if bad and start is None:start=i
            if not bad and start is not None:
                row=dict(station_id=sid,start=str(days[start].date()),end=str(days[i-1].date()),days=i-start)
                ranges.append(row);allgaps.append(row);start=None
        yearly=[]
        for y in range(1985,2015):
            ym=days.year==y;n=int(mask[ym].sum());row=dict(station_id=sid,year=y,expected=int(ym.sum()),missing=n,available=int(ym.sum())-n)
            yearly.append(row);annual.append(row)
        stations.append(dict(id=sid,name=g.station_name.iloc[0],lat=lat,lon=lon,expected=expected,available=expected-missing,missing=missing,missing_pct=100*missing/expected,passed=passed,mapped=passed and not issue,coordinate_issue=issue,gaps=ranges,yearly=yearly))
    result=dict(start='1985-01-01',end='2014-12-31',expected=expected,stations=stations,provenance=provenance,metadata_sha256=hashlib.sha256(Path(metadata).read_bytes()).hexdigest(),metadata_correction='4003201/48401 (ตากฟ้า) → 400301/48401; same documented correction as ranking code')
    out=Path(out);out.mkdir(exist_ok=True)
    (out/'coverage.json').write_text(json.dumps(result,ensure_ascii=False,allow_nan=False,separators=(',',':')),encoding='utf8')
    pd.DataFrame([{k:v for k,v in s.items() if k not in ['gaps','yearly']} for s in stations]).to_csv(out/'coverage_summary.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(allgaps).to_csv(out/'missing_periods.csv',index=False,encoding='utf-8-sig')
    pd.DataFrame(annual).to_csv(out/'coverage_yearly.csv',index=False,encoding='utf-8-sig')
    for s in stations:
        assert sum(g['days'] for g in s['gaps'])==s['missing']==sum(y['missing'] for y in s['yearly'])
        assert s['available']+s['missing']==expected
        assert s['passed']==(s['missing_pct']<=20)
    print(json.dumps(dict(stations=len(stations),mapped=sum(s['mapped'] for s in stations),excluded_missing=sum(not s['passed'] for s in stations),passed_without_coordinates=sum(s['passed'] and not s['mapped'] for s in stations),expected_days=expected)))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rain',required=True);p.add_argument('--metadata',required=True);p.add_argument('--out',default='.')
    a=p.parse_args();build(a.rain,a.metadata,a.out)

