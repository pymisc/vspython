#!/usr/bin/env python3
"""Download official NCES IPEDS tuition data and chart a 20-school panel.

Usage: python build_cs_tuition_trends.py
Requires: matplotlib (pip install matplotlib), internet access.
Covers IPEDS collection years 2000..2024, where available.
Public schools: default uses in-state tuition; CSV also includes out-of-state.
4-year price = sum of four consecutive years' published annual rates.
No interpolation: missing years lead to blank values.
"""
import csv
import io
import math
import pathlib
import urllib.error
import urllib.request
import zipfile

SCHOOLS = {
    'MIT': (166683, 'private'), 'Stanford': (243744, 'private'),
    'Carnegie Mellon': (211440, 'private'), 'Princeton': (186131, 'private'),
    'Cornell': (190415, 'private'), 'Caltech': (110404, 'private'),
    'Harvard': (166027, 'private'), 'Columbia': (190150, 'private'),
    'Penn': (215062, 'private'), 'Johns Hopkins': (162928, 'private'),
    'UC Berkeley': (110635, 'public'), 'Georgia Tech': (139755, 'public'),
    'UIUC': (145637, 'public'), 'UT Austin': (228778, 'public'),
    'U Washington': (236948, 'public'), 'UC San Diego': (110680, 'public'),
    'U Michigan': (170976, 'public'), 'UCLA': (110662, 'public'),
    'Purdue': (243780, 'public'), 'UW Madison': (240444, 'public'),
}
YEARS = range(2000, 2025)
OUT = pathlib.Path.cwd()
DATA_URL = 'https://nces.ed.gov/ipeds/datacenter/data/IC{year}_AY.zip'


def number(row, field):
    raw = row.get(field, '').strip().replace(',', '')
    try:
        value = float(raw)
        return value if value >= 0 else None
    except ValueError:
        return None


def fetch_year(year):
    url = DATA_URL.format(year=year)
    with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent':'Mozilla/5.0'}), timeout=60) as r:
        zdata = r.read()
    with zipfile.ZipFile(io.BytesIO(zdata)) as z:
        csvname = next(name for name in z.namelist() if name.lower().endswith('.csv') and 'dict' not in name.lower())
        content = z.read(csvname).decode('utf-8-sig', errors='replace')
    reader = csv.DictReader(io.StringIO(content))
    mapping = {}
    for raw in reader:
        row = {k.upper():v for k,v in raw.items() if k is not None}
        try:
            unitid = int(row.get('UNITID',''))
        except ValueError:
            continue
        if unitid in {u for u,_ in SCHOOLS.values()}:
            mapping[unitid] = (number(row, 'TUITION2'), number(row, 'TUITION3'))
    return mapping


def main():
    import matplotlib.pyplot as plt
    panel = {}
    for y in YEARS:
        try:
            rows = fetch_year(y)
            print(f'{y}: {len(rows)} selected institutions')
            for name,(unitid,kind) in SCHOOLS.items():
                if unitid in rows:
                    ins, outs = rows[unitid]
                    panel[(name,y)] = (ins, outs)
        except (urllib.error.URLError, zipfile.BadZipFile, StopIteration, TimeoutError) as ex:
            print(f'{y}: unavailable ({ex})')

    with open(OUT/'cs_tuition_annual_2000_2024.csv','w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['university','IPEDS_collection_year','residency','annual_tuition_fees_USD','source_URL'])
        for name,(unitid,kind) in SCHOOLS.items():
            for y in YEARS:
                for residence, val in zip(['in_state','out_of_state'],panel.get((name,y),(None,None))):
                    w.writerow([name,y,residence,'' if val is None else int(val),DATA_URL.format(year=y)])

    with open(OUT/'cs_four_year_cost_by_entry_year.csv','w',newline='',encoding='utf-8') as f:
        w=csv.writer(f)
        w.writerow(['university','entry_year','residency','four_year_tuition_USD','years_covered'])
        for name,(unitid,kind) in SCHOOLS.items():
            for start in range(2000,2022):
                for residence, ix in [('in_state',0),('out_of_state',1)]:
                    vals=[panel.get((name,y),(None,None))[ix] for y in range(start,start+4)]
                    total=sum(vals) if all(v is not None for v in vals) else None
                    w.writerow([name,start,residence,'' if total is None else int(total),sum(v is not None for v in vals)])

    fig,ax=plt.subplots(figsize=(14,9))
    for name,(unitid,kind) in SCHOOLS.items():
        ix=0  # private universities use TUITION2; public universities show in-state by default
        xs=[];ys=[]
        for start in range(2000,2022):
            vals=[panel.get((name,y),(None,None))[ix] for y in range(start,start+4)]
            if all(v is not None for v in vals):
                xs.append(start);ys.append(sum(vals)/1000)
        if xs:
            ax.plot(xs,ys,label=name,linewidth=1.7,alpha=.88,linestyle='--' if kind=='public' else '-')
    ax.set(title='Published tuition for a four-year entry cohort (20 leading CS universities)',xlabel='Fall entry year',ylabel='Tuition and required fees over four years (USD thousands)')
    ax.grid(alpha=.2)
    ax.legend(ncol=4,fontsize=8,loc='upper left')
    fig.text(.01,.01,'Source: NCES/IPEDS IC_AY survey files, 2000–2024. Nominal USD; public = in-state. No room/board or aid. Missing data omitted.',fontsize=8)
    fig.tight_layout(rect=[0,.03,1,1])
    fig.savefig(OUT/'top20_cs_four_year_tuition_trends.png',dpi=220)
    print('Saved annual CSV, four-year CSV and PNG. Check missing coverage before citing individual school trends.')

if __name__=='__main__':
    main()
