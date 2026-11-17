"""Reviewed branch definitions for the 2026-11-17 source snapshot.

Only recipe facts are retained. Notes are original summaries. A minimum-count
branch is explicitly flagged when the source gives ingredients but no estimate.
"""
import re

def build(guides, soups, recipe, items):
    groups={}
    def step(lo,hi,value,minimum=False):
        r=recipe(value)
        if not r or not r['spell']: raise ValueError(('Unresolved alternate recipe',value))
        if minimum: r['minimum']=True
        return {'from':lo,'to':hi,'recipes':[r]}
    def block(lo,hi,*steps): return {'from':lo,'to':hi,'steps':list(steps)}
    def option(key,label,blocks,note='',level=1,faction=None):
        out={'id':key,'label':label,'blocks':blocks,'note':note,'level':level}
        if faction: out['faction']=faction
        return out
    def add(slug,key,label,ranges,default,*options):
        groups.setdefault(slug,[]).append({'id':key,'label':label,'ranges':ranges,
            'options':[option('default','Guide default: '+default,[])]+list(options)})
    s,b,o=step,block,option
    add('alchemy','finish','Oil or mana finishing path',[[250,300]],'Stonescale Oil, then Greater Defense',
        o('mana','Greater Intellect, then Superior Mana Potion',[b(250,300,
            s(250,265,'21x Elixir of Greater Intellect - 21 Blindweed, 21 Khadgar\'s Whisker, 21 Crystal Vial'),
            s(265,300,'55x Superior Mana Potion - 110 Sungrass, 110 Blindweed, 55 Crystal Vial'))],
          'Changes 250-300 together. Skip Stonescale Oil. Superior Mana recipe: Algernon (Undercity) or Ulthir (Darnassus).'))
    add('blacksmithing','silver','Belt or rod',[[75,80]],'Silver Rod',
        o('belt','Runed Copper Belt',[b(75,80,s(75,80,'5x Runed Copper Belt - 50 Copper Bar'))]))
    add('blacksmithing','bronze','Bronze recipe',[[125,140]],'Bronze Shortsword',
        o('bracers','Patterned Bronze Bracers',[b(125,140,s(125,140,'24x Patterned Bronze Bracers - 120 Bronze Bar, 48 Coarse Grinding Stone'))]))
    add('blacksmithing','spurs','Mithril path',[[215,245]],'Heavy Mithril path',
        o('spurs','Mithril Spurs path (215-245)',[b(215,245,
            s(215,225,'10x Mithril Spurs - 40 Mithril Bar, 30 Solid Grinding Stone'),
            s(225,230,'5x Dense Sharpening Stone - 5 Dense Stone'),
            s(230,245,'33x Mithril Spurs - 132 Mithril Bar, 99 Solid Grinding Stone'))],
          'Requires world-drop Plans: Mithril Spurs. Skips Imperial Plate Belt. Replaces any selected 240-270 alternate path.'))
    groups['blacksmithing'][-1]['conflicts']=['imperial']
    bracers=s(255,270,'17x Imperial Plate Bracers - 340 Thorium Bar, 17 Star Ruby')
    add('blacksmithing','imperial','Imperial Plate alternative path',[[240,270]],'Imperial Plate quests',
        o('rapier','Dazzling Mithril Rapier, then Imperial Plate Bracers',[b(240,270,
            s(240,255,'27x Dazzling Mithril Rapier - 378 Mithril Bar, 27 Aquamarine, 54 Lesser Moonstone, 54 Moss Agate, 27 Solid Grinding Stone, 54 Mageweave Cloth'),bracers)],
          'Requires world-drop rapier plans. After 255, resumes Imperial Plate Bracers (scaled estimate); that quest still needs level 50.'),
        o('hammer','Runed Mithril Hammer, then Imperial Plate Bracers',[b(240,270,
            s(240,255,'20x Runed Mithril Hammer - 360 Mithril Bar, 40 Core of Earth, 20 Solid Grinding Stone, 80 Thick Leather'),bracers)],
          'Requires world-drop hammer plans. After 255, resumes Imperial Plate Bracers (scaled estimate); that quest still needs level 50.'),
        o('thorium','Thorium Bracers, then Imperial Plate Bracers',[b(240,270,s(240,255,'17x Thorium Bracers - 204 Thorium Bar, 68 Blue Power Crystal'),bracers)],
          'Requires world-drop Thorium Bracers plans. After 255, resumes Imperial Plate Bracers (scaled estimate); that quest still needs level 50.'))
    groups['blacksmithing'][-1]['options'][0].update(level=50,
        note='Imperial Plate recipe quests: Derotain Mudsipper, Tanaris. The lowered quest skill gates are unverified.')
    groups['blacksmithing'][-1]['conflicts']=['spurs']
    # Use the site's active dust tab as a consistent default, including 20-70.
    dust=[]; essence=[]
    for tab,dest in [('tab2-70-150',dust),('tab1-70-150',essence)]:
        for li in soups['enchanting'].find(id=tab).select('li'):
            label=li.find('b',recursive=False)
            if not label: continue
            match=re.fullmatch(r'(\d+)-(\d+)',label.get_text(strip=True))
            if not match: continue
            direct=' '.join(c.get_text(' ',strip=True) if getattr(c,'name',None) else str(c)
                for c in li.contents if getattr(c,'name',None) not in ['p','ul','ol','details'])
            direct=li.get('data-primary',direct)
            r=recipe(' '.join(direct.split()))
            if not r: raise ValueError(('Enchanting tab',direct))
            dest.append({'from':int(match[1]),'to':int(match[2]),'recipes':[r]})
    base=guides['enchanting']['steps']
    guides['enchanting']['steps']=[x for x in base if x['to']<=70]+dust+[x for x in base if x['from']>=150]
    essence_start=s(20,70,'50x Enchant Bracer - Minor Deflect - 50 Lesser Magic Essence')
    train=[x for x in essence if x['to']<=125]+[s(125,150,'25x Enchant Boots - Minor Stamina - 100 Strange Dust')]
    soul=dust[:-1]+[s(130,150,'20x Enchant Bracer - Lesser Stamina - 20 Soul Dust')]
    dust_start=[x for x in base if x['from']==20][0]
    add('enchanting','early-path','Dust or essence path',[[20,150]],'Strange Dust path',
        o('essence','Lesser Magic Essence path',[b(20,150,essence_start,*essence)],'Lesser Intellect formula: Kithas, Nata Dawnstrider, Leo Sarn or Tilli Thistlefuzz.'),
        o('essence-trainer','Essence start, then trainer recipes',[b(20,150,essence_start,*train)],'Uses trainer alternatives at 110-150 instead of buying Lesser Intellect.'),
        o('soul','Strange Dust, then Soul Dust at 130',[b(20,150,dust_start,*soul)],'Changes the full 20-150 path together.'))
    add('enchanting','agility-strength','Dust choice',[[165,200]],'Lesser Agility to 200',
        o('strength','Lesser Agility to 185, then Strength',[b(165,200,
            s(165,185,'22x Enchant Boots - Lesser Agility - 22 Soul Dust'),
            s(185,200,'15x Enchant Bracer - Strength - 15 Vision Dust'))],
          'The 22 boot crafts are inferred from the source shopping-list alternative.'))
    add('enchanting','lotus','Oil or enchant',[[250,265]],'Lesser Mana Oil',
        o('strength','Enchant Bracer - Greater Strength',[b(250,265,s(250,265,'15x Enchant Bracer - Greater Strength - 15 Dream Dust, 30 Lesser Nether Essence',True))],
          'Annora teaches this. Minimum craft count only: the source provides no estimate; allow extra materials.'))
    add('enchanting','finish','Final skill point',[[299,300]],'Runed Arcanite Rod',
        o('shield','One more Greater Stamina shield enchant',[b(299,300,s(299,300,'1x Enchant Shield - Greater Stamina - 6 Dream Dust',True))],
          'Source suggests one more shield instead if you do not need the rod yet. Minimum estimate; skill-up is not guaranteed.'))
    add('engineering','silver','Contacts or goggles',[[100,105]],'Silver Contact',
        o('goggles','Flying Tiger Goggles',[b(100,105,s(100,105,'5x Flying Tiger Goggles - 30 Light Leather, 10 Tigerseye'))]))
    add('engineering','scope','Scope or powder',[[125,135]],'Standard Scope',
        o('powder','Heavy Blasting Powder',[b(125,135,s(125,135,'10x Heavy Blasting Powder - 10 Heavy Stone',True))],
          'Minimum craft count only: source gives no estimate for this alternate. Save the powder for later steps.'))
    add('leatherworking','shoes','Gauntlets or shoes',[[235,265]],'Wicked Leather Gauntlets',
        o('shoes','Blue Suede Shoes',[b(235,265,s(235,265,'36x Blue Suede Shoes - 288 Rugged Leather, 36 Blue Dye, 36 Rune Thread'))],
          'Requires the Blue Suede Shoes pattern. Source compares vendor resale value; no live auction price is assumed.'))
    add('leatherworking','finish','Finishing leatherwork',[[265,300]],'Runic Leather Headband',
        o('bracers','Headbands to 275, then Blue Suede Bracers',[b(265,300,
            s(265,275,'16x Runic Leather Headband - 224 Rugged Leather, 160 Runecloth, 16 Rune Thread'),
            s(275,300,'27x Blue Suede Bracers - 270 Rugged Leather, 27 Blue Dye, 27 Rune Thread'))],
          'Requires the bracers pattern. Opening headband count is scaled from the source 265-300 estimate.'),
        o('hat','Headbands to 280, then Blue Suede Hat',[b(265,300,
            s(265,280,'23x Runic Leather Headband - 322 Rugged Leather, 230 Runecloth, 23 Rune Thread'),
            s(280,300,'20x Blue Suede Hat - 320 Rugged Leather, 80 Blue Dye, 20 Rune Thread'))],
          'Requires the hat pattern and access to another leatherworker\'s Sewing Machine; your own needs skill 300. Opening headband count is scaled.'))
    add('tailoring','bags','Bags or belts',[[215,225]],'Mageweave Bag',
        o('belts','Runecloth Belt',[b(215,225,s(215,225,'10x Runecloth Belt - 30 Bolt of Runecloth, 10 Rune Thread'))],
          'Requires Artisan Tailoring, even though this step is below 225.',35))
    add('tailoring','finish','Final tailoring recipe',[[280,300]],'Runecloth Shoulders',
        o('turban','Wizardweave Turban',[b(280,300,s(280,300,'58x Wizardweave Turban - 348 Bolt of Runecloth, 232 Dream Dust, 58 Star Ruby'))],
          'Requires a rare pattern; check availability before buying materials. Both 280-300 options depend on world-drop patterns.'))
    add('first-aid','starter','Bandages or potions',[[1,75]],'Linen bandages',
        o('potions','Minor Healing Potion',[b(1,75,s(1,75,'81x Minor Healing Potion - 81 Peacebloom, 81 Mild Spices, 81 Empty Vial'))],
          'Mild Spices: Cooking supply vendors. Empty Vial: Alchemy supply vendors.'))

    # Cooking offers several complete recipe rows at each skill band.
    lo,hi=1,50
    for el in soups['cooking'].find_all(['h2','h3','table']):
        if el.name!='table':
            match=re.search(r'(\d+)-(\d+)',el.get_text(' ',strip=True).replace('\u2060',''))
            if match: lo,hi=map(int,match.groups())
            continue
        rows=[r for r in el.select('tr') if r.find('td')]
        ancestor=el.find_parent('li',class_='route-step')
        if ancestor:
            match=re.fullmatch(r'(\d+)-(\d+)',ancestor.find('b',recursive=False).get_text(strip=True))
            if match: lo,hi=map(int,match.groups())
        opts=[]
        for row in rows:
            cells=row.find_all('td',recursive=False)
            if len(cells)!=3: continue
            food=cells[0].get_text(' ',strip=True)
            if not re.match(r'^\d+(?:-\d+)?x ',food): continue
            food=re.sub(r'^\d+-(\d+)x',r'\1x',food)
            mat=re.sub(r'\(.*?\)','',cells[1].get_text(' ',strip=True)).replace('x ',' ')
            mat=re.sub(r'\d+-(\d+) ',r'\1 ',mat)
            # A table cell can separate ingredients with <br> instead of commas.
            mat=re.sub(r'(?<=[A-Za-z])\s+(?=\d+\s)',', ',mat)
            r=recipe(food+' - '+mat)
            if not r or not r['spell']: raise ValueError(('Cooking alternate',food,mat))
            source=cells[2].get_text(' ',strip=True)
            faction='Horde' if '(Horde only)' in source else 'Alliance' if '(Alliance only)' in source else None
            # Two separate quest routes exist for Strider Stew; keep both factions.
            if '(Horde only)' in source and '(Alliance only)' in source: faction=None
            opts.append(o(str(r['spell']),r['name'],[b(lo,hi,{'from':lo,'to':hi,'recipes':[r]})],
                'Recipe source: '+source,1,faction))
        if len(opts)>1: add('cooking','recipe-'+str(lo),'Cooking recipe',[[lo,hi]],opts[0]['label'],*opts[1:])

    for group in groups.get('cooking',[]):
        if group['id']=='recipe-150':
            group['options'].append(o('catfish','Bristle Whisker Catfish',[b(150,175,
                s(150,175,'90x Bristle Whisker Catfish - 90 Raw Bristle Whisker Catfish'))],
                'Source estimates about 90; this recipe is green from 160.'))

    items.update({'Dense Grinding Stone':12644,'Iron Buckle':7071,'Cured Light Hide':4231,
        'Blue Power Crystal':11184,'Heart of Fire':7077,'Large Opal':12799,
        'Lesser Nether Essence':11174,'Truesilver Bar':6037,'Core of Earth':7075,
        'Cured Heavy Hide':4236,'Lesser Moonstone':1705,'Stonescale Oil':13423})
    return groups
