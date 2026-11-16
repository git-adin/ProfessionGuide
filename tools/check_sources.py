"""Fetch fresh upstream pages and compare readable guide content to local cache.

Never overwrite the baseline: fresh HTML stays in the ignored cache. The report
contains hashes and counts; changed paragraphs are printed for a manual review.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import argparse, hashlib, re, sys, urllib.request
sys.path.insert(0,str(Path(__file__).resolve().parents[2]/'.tools'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'.tools'))
from bs4 import BeautifulSoup

SLUGS=['alchemy','blacksmithing','enchanting','engineering','leatherworking','tailoring',
       'first-aid','cooking','mining','herbalism','skinning','fishing','lockpicking']
ROOT=Path(__file__).resolve().parents[1]

def readable(html):
    soup=BeautifulSoup(html,'html.parser')
    for el in soup(['script','style','nav','header','footer','noscript']): el.decompose()
    return re.sub(r'\s+',' ',soup.get_text(' ',strip=True)).strip()

def inspect(slug,date):
    url='https://www.wow-professions.com/forever/'+slug+'-leveling-guide'
    req=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Cache-Control':'no-cache'})
    with urllib.request.urlopen(req,timeout=45) as response:
        fresh=response.read()
    if not BeautifulSoup(fresh,'html.parser').find('h1'): raise ValueError('No guide heading: '+slug)
    cache=ROOT/'tools/.source-cache'
    latest=cache/('checked-'+date); latest.mkdir(exist_ok=True)
    (latest/(slug+'.html')).write_bytes(fresh)
    previous=(cache/(slug+'.html')).read_bytes()
    old,new=readable(previous),readable(fresh)
    return slug,old,new,hashlib.sha256(fresh).hexdigest()

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--date',required=True,help='Explicit review date (YYYY-MM-DD)')
    parser.add_argument('--details',action='store_true',help='Print changed source passages for manual review')
    args=parser.parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}',args.date): parser.error('Expected YYYY-MM-DD')
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(lambda slug:inspect(slug,args.date),SLUGS))
    manifest={}
    import difflib,json
    for slug,old,new,digest in results:
        changed=old!=new
        print(slug+(': CHANGED' if changed else ': unchanged readable content'))
        manifest[slug]={'url':'https://www.wow-professions.com/forever/'+slug+'-leveling-guide',
            'checked':args.date,'sha256':digest,'contentChanged':changed}
        if changed and args.details:
            for part in difflib.SequenceMatcher(None,old.split(),new.split(),autojunk=False).get_opcodes():
                tag,a,b,c,d=part
                if tag!='equal':
                    print('  BEFORE:',' '.join(old.split()[max(0,a-8):b+8]))
                    print('  AFTER: ',' '.join(new.split()[max(0,c-8):d+8]))
    (ROOT/'tools/.source-cache'/('checked-'+args.date)/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
