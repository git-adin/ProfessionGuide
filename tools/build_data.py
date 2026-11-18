"""Compile recipe facts only, never guide prose or images. Review before shipping.

Populate tools/.source-cache with inspect_source.py first. beautifulsoup4 is a
development dependency only. Cached source pages are excluded from releases.
"""
from pathlib import Path
import sys, re, json, argparse
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / '.tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / '.tools'))
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--cache-dir',type=Path,default=ROOT/'tools/.source-cache')
parser.add_argument('--source-date',default='2026-11-18')
args=parser.parse_args()
SLUGS = ['alchemy','blacksmithing','enchanting','engineering','leatherworking','tailoring','first-aid','cooking']
items, spells, recipe_icons = {}, {}, {}
soups = {}
for slug in SLUGS:
    soup = BeautifulSoup((args.cache_dir / (slug+'.html')).read_bytes(), 'html.parser')
    # November's refreshed layout uses route-step/range divs instead of list
    # items. Normalize just the structure; recipe extraction remains factual.
    for node in soup.select('.route-step'):
        label=node.select_one('.route-range')
        if not label: raise ValueError(('Missing route range',slug))
        label.name='b'
        for p in node.find_all('p',recursive=False):
            if re.match(r'^\d+x\s',p.get_text(' ',strip=True)):
                node['data-primary']=p.get_text(' ',strip=True); break
        node.name='li'
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
    return {'name':name,'spell':spells.get(name,0),'crafts':int(count),'materials':mats,'yield':2 if name in ['Fire Oil','Stonescale Oil'] else 1}

guides = {}
for slug,soup in soups.items():
    steps=[]; seen=set()
    for li in soup.select('li'):
        if slug=='cooking': break  # Cooking steps are recipe tables, parsed below.
        label=li.find(['b','strong'],recursive=False)
        if not label: continue
        m=re.fullmatch(r'(\d+)\s*[-–]\s*(\d+)',label.get_text(strip=True))
        if not m: continue
        lo,hi=map(int,m.groups())
        if (lo,hi) in seen: continue  # first branch is the selected default route
        # First Aid defaults to bandages, not the alternative potion tab.
        if slug=='first-aid' and lo==1 and hi==75: continue
        direct=' '.join(c.get_text(' ',strip=True) if getattr(c,'name',None) else str(c)
                        for c in li.contents if getattr(c,'name',None) not in ['p','ul','ol','details'])
        direct=li.get('data-primary',direct)
        r=recipe(' '.join(direct.split()))
        if r is None:
            # Nested choices: choose one, except Engineering 135-150 needs both.
            nested=li.find(['ul','ol'])
            choices=[recipe(' '.join(c.get_text(' ',strip=True).split())) for c in nested.find_all('li',recursive=False)] if nested else []
            choices=[c for c in choices if c]
            if not choices and slug=='tailoring' and lo==280:
                cells=li.select('table tr')[1].find_all('td',recursive=False)
                materials=cells[2].get_text(' ',strip=True).replace('x ', ' ')
                r=recipe(cells[1].get_text(' ',strip=True)+' - '+materials)
                choices=[r] if r else []
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
                ancestor=el.find_parent('li',class_='route-step')
                if ancestor:
                    match=re.fullmatch(r'(\d+)-(\d+)',ancestor.find('b',recursive=False).get_text(strip=True))
                    if match: lo,hi=map(int,match.groups())
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
    expected=1
    for step in steps:
        if step['from']!=expected: raise ValueError((slug,'gap/overlap',expected,step['from']))
        expected=step['to']
    if expected != 300: raise ValueError((slug,'Unexpected coverage',expected))
    guides[slug]={'steps':steps,'cap':expected,'source':'https://www.wow-professions.com/forever/'+slug+'-leveling-guide'}

from alternate_routes import build as build_alternates
alternates=build_alternates(guides,soups,recipe,items)
reviewed_notes={
    ('engineering',260):'Buy Schematic: Thorium Widget from Sovik (Orgrimmar) or Gearcutter Cogspinner (Ironforge).',
    ('engineering',285):'Buy the bind-on-pickup Thorium Tube schematic from Xizzer Fizzbolt in Everlook, Winterspring, on this character.',
    ('tailoring',200):'These shoulders require an Artisan trainer; the Expert trainers do not teach them.',
    ('tailoring',240):'Runecloth Gloves pattern: Qia, Winterspring.',
    ('tailoring',250):'Runecloth Cuffs pattern: Pexmit, Mount Hyjal (bind on pickup). Optional Horde quest source: Threading a Solution from Kal\'tinzan, Elderwild, Mount Hyjal; level 54 and 6 Bolt of Runecloth. Quest skill requirement is unverified.',
    ('tailoring',280):'Requires the world-drop Runecloth Shoulders pattern. Check availability before buying. Wizardweave Turban is an alternate; Loom recipes require another tailor\'s Loom and Cenarion Circle reputation (see source).',
    ('first-aid',275):'Major Healing Potion manual: Pexmit in Mount Hyjal for 8 gold, or check the Auction House. Horde quest: A Rest Without Pain from Ortak Lomgok in Elderwild; first complete Herbs for the Bruised and Weary.',
}
for slug,guide in guides.items():
    for step in guide['steps']:
        if (slug,step['from']) in reviewed_notes: step['note']=reviewed_notes[slug,step['from']]
        if slug=='tailoring' and step['from']>=200: step['level']=35
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

output='-- Recipe facts compiled from WoW-Professions.com, '+args.source_date+'. See SOURCES.md.\nlocal _, ns = ...\n'
output+='ns.SourceDate = '+json.dumps(args.source_date)+'\n'
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
