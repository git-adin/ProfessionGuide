-- SPDX-License-Identifier: GPL-3.0-or-later
local _,ns=...
-- Presentation metadata for the existing, source-reviewed route bands.
local bands={
    mining={
        [1]={"Copper",2770},[65]={"Copper & Tin",2771,75,"Silver"},
        [125]={"Iron & Gold",2772,155,"Gold"},[175]={"Mithril",3858,230,"Truesilver"},
        [245]={"Small Thorium & Mithril",10620},[275]={"Thorium",10620}},
    herbalism={
        [1]={"Starter herbs"},[70]={"Mageroyal & Briarthorn",785,85,"Stranglekelp"},
        [115]={"Bruiseweed & Wild Steelbloom",2453,125,"Kingsblood"},
        [170]={"Kingsblood to Goldthorn",3356},[205]={"Purple Lotus & Firebloom",8831},
        [230]={"Sungrass & Purple Lotus",8838,245,"Ghost Mushroom"},[270]={"Dreamfoil & Plaguebloom",13463}},
    skinning={
        [1]={"Starter beasts"},[75]={"Level 16-18 beasts"},[150]={"Bears & mountain lions"},
        [160]={"Yetis & worgen"},[225]={"Feral Scar Vale yetis"},[280]={"Un'Goro dinosaurs"}},
    fishing={
        [1]={"Starting-zone fishing"},[75]={"Capital-city fishing"},
        [150]={"Dustwallow fishing"},[225]={"Artisan quest & fishing"}},
    lockpicking={
        [1]={"Practice lockboxes"},[100]={"Waterlogged Footlockers",nil,110,"Underwater footlockers"},
        [150]={"Angor Fortress locks",nil,175,"Downstairs footlockers"},[225]={"Dented Footlockers"}},
}
local preparation={
    mining="Carry a Mining Pick and enable Find Minerals.",
    herbalism="Enable Find Herbs before heading out.",
    skinning="Carry a Skinning Knife. Skin suitable defeated beasts.",
    fishing="Equip a Fishing Pole and use the lure recommended for the area.",
    lockpicking="Practice on suitable locks; your skill cap follows your character level.",
}
local fishingZones={[1]="Starting zones",[75]="Friendly capital",[150]="Dustwallow Marsh",
    [225]="Feralas or Tanaris or The Hinterlands"}
local maps={
    ["Elwynn Forest"]=1429,["Durotar"]=1411,["Westfall"]=1436,["Wetlands"]=1437,
    ["Silverpine Forest"]=1421,["Hillsbrad Foothills"]=1424,["Thousand Needles"]=1441,
    ["Arathi Highlands"]=1417,["Tanaris"]=1446,["The Hinterlands"]=1425,
    ["Un'Goro Crater"]=1449,["Western Un'Goro Crater"]=1449,["Felwood"]=1448,
    ["Winterspring"]=1452,["Loch Modan"]=1432,["Darkshore"]=1439,
    ["Stonetalon Mountains"]=1442,["Stranglethorn Vale"]=1434,["Searing Gorge"]=1427,
    ["Duskwood"]=1431,["Feralas"]=1444,["Dustwallow Marsh"]=1445,["The Barrens"]=1413,
}
function ns.IsGathering(slug) return bands[slug]~=nil end
function ns.GatheringInfo(slug,step,player)
    if not step or not bands[slug] then return end
    local source,index,steps
    steps=ns.GetGuideSteps(slug)
    for i,s in ipairs(steps) do
        if s.from<=step.from and s.to>=step.to then source,index=s,i; break end
    end
    if not source then return end
    local band=bands[slug][source.from] or {"Gathering activity"}
    local zone
    if source.alliance and source.alliance==source.horde then zone=source.alliance
    elseif player.faction=="Horde" then zone=source.horde
    elseif player.faction=="Alliance" then zone=source.alliance end
    zone=zone or (slug=="fishing" and fishingZones[source.from])
    local info={name=band[1],item=band[2],action=source.action,preparation=preparation[slug],zones={},milestones={}}
    if zone then
        for name in (zone.." or "):gmatch('(.-) or ') do
            info.zones[#info.zones+1]={name=name,map=maps[name]}
        end
    end
    if band[3] then info.milestones[#info.milestones+1]={skill=band[3],name=band[4]} end
    if slug=="herbalism" and source.from==115 then info.milestones[#info.milestones+1]={skill=150,name="Liferoot"} end
    local following=steps[index+1]
    if following then
        local nextBand=bands[slug][following.from]
        info.nextStep={skill=following.from,name=nextBand and nextBand[1] or "Next route step"}
    end
    return info
end
function ns.OpenGatheringMap(mapID)
    if ns.Safe(InCombatLockdown)==true then return false,"Open the zone map after leaving combat." end
    if not mapID or not C_Map or type(C_Map.OpenWorldMap)~="function" or not ns.Safe(C_Map.GetMapInfo,mapID) then
        return false,"Zone map is unavailable in this client session."
    end
    local ok=pcall(C_Map.OpenWorldMap,mapID)
    return ok,ok and "Opened the recommended zone. Gathering locations vary; no node waypoint was placed."
        or "Could not open the zone map."
end
