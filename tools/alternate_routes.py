"""Reviewed branch definitions for the 2026-11-12 source snapshot.

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
    add('alchemy','starter','Starter elixir',[[1,10]],'Minor Arcane Elixir',
        o('force','Elixir of Minor Force',[b(1,10,s(1,10,'9x Elixir of Minor Force - 9 Silverleaf, 9 Empty Vial'))]))
    add('alchemy','oil-mana','Oil or mana path',[[130,165]],'Fire Oil, then Fire Power',
        o('mana','Lesser Mana Potions (linked path)',[b(130,165,
            s(130,150,'20x Lesser Mana Potion - 20 Mageroyal, 20 Stranglekelp, 20 Empty Vial'),
            s(150,165,'22x Lesser Mana Potion - 22 Mageroyal, 22 Stranglekelp, 22 Empty Vial'))],
          'Changes both 130-150 and 150-165. This path does not need saved Fire Oil.'))
    add('alchemy','finish','Finishing potion',[[265,300]],'Elixir of Greater Defense',
        o('mana','Superior Mana Potion',[b(265,300,s(265,300,'55x Superior Mana Potion - 110 Sungrass, 110 Blindweed, 55 Crystal Vial'))],
          'Buy Recipe: Superior Mana Potion from Algernon (Undercity) or Ulthir (Darnassus).'))
    add('blacksmithing','silver','Belt or rod',[[75,80]],'Runed Copper Belt',
        o('rod','Silver Rod',[b(75,80,s(75,80,'5x Silver Rod - 5 Silver Bar, 10 Rough Grinding Stone'))]))
    add('blacksmithing','bronze','Bronze recipe',[[125,140]],'Bronze Shortsword',
        o('bracers','Patterned Bronze Bracers',[b(125,140,s(125,140,'24x Patterned Bronze Bracers - 120 Bronze Bar, 48 Coarse Grinding Stone'))]))
    add('blacksmithing','spurs','Mithril recipe',[[215,225]],'Heavy Mithril Breastplate',
        o('spurs','Mithril Spurs',[b(215,225,s(215,225,'10x Mithril Spurs - 40 Mithril Bar, 30 Solid Grinding Stone'))],
          'Requires Plans: Mithril Spurs, a world-drop recipe.'))
    ebon=s(240,255,'15x Ebon Shiv - 180 Mithril Bar, 90 Truesilver Bar, 30 Star Ruby, 15 Solid Grinding Stone, 30 Thick Leather')
    axe=s(255,270,'15x Ornate Thorium Handaxe - 300 Thorium Bar, 30 Large Opal, 30 Dense Grinding Stone, 60 Rugged Leather')
    add('blacksmithing','imperial','Imperial Plate alternative path',[[240,270]],'Imperial Plate quests',
        o('ebon','Ebon Shiv, then Ornate Thorium Handaxe',[b(240,270,ebon,axe)],'Both plans: Magnus Frostwake, Western Plaguelands.'),
        o('radiant','Radiant Belt, then Ornate Thorium Handaxe',[b(240,270,s(240,255,'15x Radiant Belt - 150 Thorium Bar, 30 Heart of Fire'),axe)],'Radiant Belt is a world-drop plan; handaxe plan: Magnus Frostwake.'),
        o('thorium','Thorium Bracers, then Ornate Thorium Handaxe',[b(240,270,s(240,255,'17x Thorium Bracers - 204 Thorium Bar, 68 Blue Power Crystal'),axe)],'Thorium Bracers is a world-drop plan; handaxe plan: Magnus Frostwake.'))
    groups['blacksmithing'][-1]['options'][0].update(level=50,
        note='Imperial Plate recipe quests: Derotain Mudsipper, Tanaris. The lowered quest skill gates are unverified.')
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
            r=recipe(' '.join(direct.split()))
            if not r: raise ValueError(('Enchanting tab',direct))
            dest.append({'from':int(match[1]),'to':int(match[2]),'recipes':[r]})
    base=guides['enchanting']['steps']
    guides['enchanting']['steps']=[x for x in base if x['to']<=70]+dust+[x for x in base if x['from']>=150]
    essence_start=s(20,70,'50x Enchant Bracer - Minor Deflect - 50 Lesser Magic Essence')
    train=essence[:3]+dust[3:]
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
    add('enchanting','finish','Finishing enchant',[[295,300]],'Superior Defense',
        o('shield','Enchant Shield - Greater Stamina',[b(295,300,s(295,300,'5x Enchant Shield - Greater Stamina - 30 Dream Dust',True))],
          'Requires the vendor formula. Minimum craft count only; green skill-ups can require substantially more.'))
    add('engineering','silver','Contacts or goggles',[[100,105]],'Silver Contact',
        o('goggles','Flying Tiger Goggles',[b(100,105,s(100,105,'5x Flying Tiger Goggles - 30 Light Leather, 10 Tigerseye'))]))
    add('engineering','scope','Scope or powder',[[125,135]],'Standard Scope',
        o('powder','Heavy Blasting Powder',[b(125,135,s(125,135,'10x Heavy Blasting Powder - 10 Heavy Stone',True))],
          'Minimum craft count only: source gives no estimate for this alternate. Save the powder for later steps.'))
    add('leatherworking','starter','Starter materials',[[1,30]],'Ruined Leather Scraps',
        o('kits','Light Armor Kits',[b(1,30,s(1,30,'29x Light Armor Kit - 29 Light Leather',True))],
          'Uses bought Light Leather. Minimum craft count only; source gives no estimate.'))
    add('leatherworking','light-hides','Light Hide path',[[30,55],[100,115]],'Kits, gloves and cloak',
        o('hides','Cured Light Hides, then Light Leather Pants',[b(30,55,s(30,55,'27x Cured Light Hide - 27 Light Hide, 27 Salt')),
            b(100,115,s(100,115,'24x Light Leather Pants - 240 Light Leather, 24 Cured Light Hide, 24 Fine Thread'))],
          'Links 30-55 to 100-115. Keep 24 cured hides; skip the 45-55 gloves.'))
    add('leatherworking','medium-hides','Medium Hide path',[[80,90],[115,125]],'Cured Medium Hides and Dark Leather Belts',
        o('leather','Medium Leather instead of hides',[b(80,90,s(80,90,'11x Fine Leather Belt - 66 Light Leather, 22 Coarse Thread')),
            b(115,125,s(115,120,'6x Dark Leather Pants - 72 Medium Leather, 6 Gray Dye, 6 Fine Thread'),
                s(120,125,"5x Hillman's Leather Gloves - 70 Medium Leather, 20 Fine Thread"))],
          'Changes 80-90 and 115-125 together; no saved Cured Medium Hides are needed.'))
    add('leatherworking','heavy-hides','Heavy Hide path',[[130,175]],'Cured Heavy Hide path',
        o('leather','Medium/Heavy Leather and Moss Agate',[b(130,175,
            s(130,155,"30x Hillman's Leather Gloves - 420 Medium Leather, 120 Fine Thread"),
            s(155,170,'17x Barbaric Leggings - 170 Heavy Leather, 34 Fine Thread, 17 Moss Agate'),
            s(170,175,'5x Barbaric Harness - 70 Heavy Leather, 10 Fine Thread, 5 Iron Buckle'))],
          'Barbaric Leggings pattern: Jandia, Keena, Hammon Karwn or Lardan. Guardian Gloves after 175 still need cured hides.'))
    add('leatherworking','finish','Finishing headgear',[[285,300]],'Runic Leather Headband',
        o('hat','Blue Suede Hat',[b(285,300,s(285,300,'15x Blue Suede Hat - 240 Rugged Leather, 60 Blue Dye, 15 Rune Thread'))],
          'Requires the Blue Suede Hat pattern.'))
    add('tailoring','bags','Bags or belts',[[215,225]],'Mageweave Bag',
        o('belts','Runecloth Belt',[b(215,225,s(215,225,'10x Runecloth Belt - 30 Bolt of Runecloth, 10 Rune Thread'))],
          'Requires Artisan Tailoring, even though this step is below 225.',35))
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

    items.update({'Dense Grinding Stone':12644,'Iron Buckle':7071,'Cured Light Hide':4231,
        'Blue Power Crystal':11184,'Heart of Fire':7077,'Large Opal':12799,
        'Lesser Nether Essence':11174,'Truesilver Bar':6037})
    return groups
