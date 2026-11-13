"""Compile recipe facts only, never guide prose or images. Review before shipping.

Populate tools/.source-cache with inspect_source.py first. beautifulsoup4 is a
development dependency only. Cached source pages are excluded from releases.
"""
from pathlib import Path
import sys, re, json
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.tools'))
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ['alchemy','blacksmithing','enchanting','engineering','leatherworking','tailoring','first-aid','cooking']
items, spells, recipe_icons = {}, {}, {}
soups = {}
for slug in SLUGS:
    soup = BeautifulSoup((ROOT / 'tools/.source-cache' / (slug+'.html')).read_bytes(), 'html.parser')
    soups[slug] = soup
    for a in soup.select('a[href]'):
        m = re.search(r'item=(\d+)', a['href'])
        if m: items[a.get_text(' ',strip=True)] = int(m[1])
        m = re.search(r'spell=(\d+)', a['href'])
        if m:
            spells[a.get_text(' ',strip=True)] = int(m[1])
            image=a.find('img',src=True)
            icon=re.search(r'/([^/]+)\.(?:jpg|png)$',image['src']) if image else None
            if icon: recipe_icons[int(m[1])]='Interface\\Icons\\'+icon[1]
items.update({'Coarse Thread':2320,'Fine Thread':2321,'Silken Thread':4291,
    'Heavy Silken Thread':8343,'Rune Thread':14341,'Red Dye':2604,'Blue Dye':6260,
    'Green Dye':2605,'Black Dye':2325,'Salt':4289,'Refreshing Spring Water':159,
    'Hot Spices':2692,'Soothing Spices':3713,'Mild Spices':2678,
    'Bolt of Linen Cloth':2996,'Bronze Framework':4382,'Bronze Tube':4371,
    'Coarse Blasting Powder':4364,'Coarse Grinding Stone':3478,'Cured Medium Hide':4233,
    'Fine Leather Belt':4246,'Fire Oil':6371,'Gray Dye':4340,'Handful of Copper Bolts':4359,
    'Heavy Blasting Powder':4377,'Heavy Grinding Stone':3486,'Mithril Casing':10561,
    'Rough Blasting Powder':4357,'Rough Grinding Stone':3470,'Solid Blasting Powder':10505,
    'Solid Grinding Stone':7966,'Unstable Trigger':10560,'Whirring Bronze Gizmo':4375})

def recipe(text):
    # Recipe names contain hyphens; use the separator before a numeric reagent.
    m = re.search(r'(\d+)x\s+(.+?)\s+-\s+(\d+\s+.+)', text)
    if not m: return None
    count, name, rest = m.groups()
    mats = []
    for part in rest.split(','):
        x = re.match(r'\s*(\d+)x?\s+(.+?)[.]*$', part.strip())
        if not x: raise ValueError((name, part))
        amount, material = x.groups()
        material = re.sub(r'\s*\(.*', '', material).rstrip('.')
        mats.append({'name':material,'quantity':int(amount)/int(count)})
    return {'name':name,'spell':spells.get(name,0),'crafts':int(count),'materials':mats,'yield':2 if name=='Fire Oil' else 1}

guides = {}
for slug,soup in soups.items():
    steps=[]; seen=set()
    for li in soup.select('li'):
        label=li.find(['b','strong'],recursive=False)
        if not label: continue
        m=re.fullmatch(r'(\d+)\s*[-–]\s*(\d+)',label.get_text(strip=True))
        if not m: continue
        lo,hi=map(int,m.groups())
        if slug=='tailoring' and lo>=265: continue  # source has no route yet
        if (lo,hi) in seen: continue  # first branch is the selected default route
        # First Aid defaults to bandages, not the alternative potion tab.
        if slug=='first-aid' and lo==1 and hi==75: continue
        direct=' '.join(c.get_text(' ',strip=True) if getattr(c,'name',None) else str(c)
                        for c in li.contents if getattr(c,'name',None) not in ['p','ul','ol','details'])
        r=recipe(' '.join(direct.split()))
        if r is None:
            # Nested choices: choose one, except Engineering 135-150 needs both.
            nested=li.find(['ul','ol'])
            choices=[recipe(' '.join(c.get_text(' ',strip=True).split())) for c in nested.find_all('li',recursive=False)] if nested else []
            choices=[c for c in choices if c]
            if not choices: raise ValueError((slug,lo,'No recipe'))
            chosen=choices if slug=='engineering' and lo==135 else choices[:1]
        else: chosen=[r]
        steps.append({'from':lo,'to':hi,'recipes':chosen})
        seen.add((lo,hi))
    # Blacksmithing uses headings for its final ranges.
    if slug=='blacksmithing':
        for h in soup.select('h3'):
            m=re.fullmatch(r'(\d+)-(\d+)',h.get_text(strip=True))
            if not m: continue
            lo,hi=map(int,m.groups())
            if (lo,hi) in seen: continue
            for sibling in h.next_siblings:
                if getattr(sibling,'name',None) in ['h2','h3']: break
                if getattr(sibling,'get_text',None):
                    r=recipe(sibling.get_text(' ',strip=True))
                    if r:
                        steps.append({'from':lo,'to':hi,'recipes':[r]}); seen.add((lo,hi)); break
    if slug=='cooking':
        # Cooking presents alternatives in tables; use the first option per band.
        lo,hi=1,50
        for el in soup.find_all(['h2','h3','table']):
            if el.name!='table':
                text=el.get_text(' ',strip=True).replace('\u2060','')
                m=re.search(r'(\d+)-(\d+)',text)
                if m: lo,hi=map(int,m.groups())
            else:
                rows=el.select('tr')
                rows=[row for row in rows if row.find('td')]
                if not rows: continue
                cells=rows[0].find_all('td',recursive=False)
                if len(cells)!=3: continue
                food=cells[0].get_text(' ',strip=True)
                if not re.match(r'^\d+x ',food): continue
                mat=cells[1].get_text(' ',strip=True)
                mat=re.sub(r'\(.*?\)','',mat).replace('x ', ' ')
                r=recipe(food+' - '+mat)
                if r and (lo,hi) not in seen:
                    steps.append({'from':lo,'to':hi,'recipes':[r]}); seen.add((lo,hi))
    # Exclude overlapping alternative tabs by following the first continuous route.
    selected=[]; end=1
    for step in steps:
        if step['from']==end:
            selected.append(step); end=step['to']
    steps=selected
    if slug=='leatherworking':
        steps[0]['recipes'][0]['materials'][0]['quantity']=3
    expected=1
    for step in steps:
        if step['from']!=expected: raise ValueError((slug,'gap/overlap',expected,step['from']))
        expected=step['to']
    if expected != (265 if slug=='tailoring' else 300): raise ValueError((slug,'Unexpected coverage',expected))
    guides[slug]={'steps':steps,'cap':expected,'source':'https://www.wow-professions.com/forever/'+slug+'-leveling-guide'}

from alternate_routes import build as build_alternates
alternates=build_alternates(guides,soups,recipe,items)
all_recipes=[r for g in guides.values() for s in g['steps'] for r in s['recipes']]
for slug,groups in alternates.items():
    for group in groups:
        for option in group['options']:
            for block in option['blocks']:
                expected=block['from']
                for step in block['steps']:
                    if step['from']!=expected: raise ValueError(('Alternate gap',slug,group['id']))
                    expected=step['to']
                    all_recipes.extend(step['recipes'])
                if expected!=block['to']: raise ValueError(('Alternate coverage',slug,group['id']))
missing_ids=sorted({m['name'] for r in all_recipes for m in r['materials'] if m['name'] not in items})
if missing_ids: raise ValueError(('Unresolved alternate item IDs',missing_ids))

def lua(value):
    if isinstance(value,dict): return '{'+','.join('['+json.dumps(k)+']='+lua(v) for k,v in value.items())+'}'
    if isinstance(value,list): return '{'+','.join(map(lua,value))+'}'
    if isinstance(value,bool): return 'true' if value else 'false'
    return json.dumps(value,ensure_ascii=True)

output='-- Recipe facts compiled from WoW-Professions.com, 2026-11-12. See SOURCES.md.\nlocal _, ns = ...\n'
output+='ns.ItemIDs = {\n'+''.join('    ['+json.dumps(k)+']='+str(v)+',\n' for k,v in sorted(items.items()))+'}\n'
output+='ns.Guides = {\n'
for slug,g in guides.items():
    output+='    ['+json.dumps(slug)+']={cap='+str(g['cap'])+',source='+json.dumps(g['source'])+',steps={\n'
    output+=''.join('        '+lua(step)+',\n' for step in g['steps'])
    output+='    }},\n'
output+='}\n'
output+='ns.Alternates = {\n'
for slug,groups in alternates.items():
    output+='    ['+json.dumps(slug)+']={\n'+''.join('        '+lua(group)+',\n' for group in groups)+'    },\n'
output+='}\n'
used_spells={r['spell'] for r in all_recipes}
output+='ns.RecipeIcons = {\n'+''.join('    ['+str(k)+']='+json.dumps(v)+',\n' for k,v in sorted(recipe_icons.items()) if k in used_spells)+'}\n'
(ROOT/'Data.lua').write_text(output,encoding='utf-8')
for slug,g in guides.items(): print(slug,len(g['steps']),g['cap'])
unknown=sorted({m['name'] for g in guides.values() for s in g['steps'] for r in s['recipes'] for m in r['materials'] if m['name'] not in items})
print('Unresolved item IDs:',unknown)
