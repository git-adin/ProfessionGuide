-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
-- Coordinates: installed ForeverDB NPC snapshot, 2026-11-18; see SOURCES.md.
-- Missing coordinates deliberately remain unpinned (including dungeon contacts).
local function trainer(role,name,location,faction,map,x,y,note)
    return {role=role,name=name,location=location,faction=faction,map=map,x=x,y=y,note=note}
end
local t=trainer
ns.Trainers={
    alchemy={
        t("Expert","Ainethil","Darnassus","Alliance",1457,55,24),
        t("Expert","Doctor Herbert Halsey","Undercity","Horde",1458,47.8,72.8),
        t("Artisan","Kylanna Windwhisper","Feathermoon Stronghold, Feralas","Alliance",1444,32.6,43.8),
        t("Artisan","Rogvar","Stonard, Swamp of Sorrows","Horde",1435,48.5,55.8)},
    blacksmithing={
        t("Expert","Bengus Deepforge","Ironforge","Alliance",1455,52.1,41.7),
        t("Expert","Saru Steelfury","Orgrimmar","Horde",1454,82.3,22.8),
        t("Artisan","Brikk Keencraft","Booty Bay, Stranglethorn Vale",nil,1434,29,75.6),
        t("Imperial Plate recipes","Derotain Mudsipper","Gadgetzan, Tanaris",nil,nil,nil,nil,"Level 50; complete A Blue Light Bargain first.")},
    enchanting={
        t("Expert","Kitta Firewind","Tower of Azora, Elwynn Forest","Alliance",1429,65,70.7),
        t("Expert","Hgarth","Sun Rock Retreat, Stonetalon Mountains","Horde",1442,49.2,57.1),
        t("Artisan","Annora","Inside Uldaman",nil,nil,nil,nil,"Dungeon location; no outdoor pin.")},
    engineering={
        t("Expert","Springspindle Fizzlegear","Ironforge","Alliance",1455,68.5,43.9),
        t("Expert","Roxxik","Orgrimmar","Horde",1454,76.1,25.1),
        t("Artisan","Buzzek Bracketswing","Gadgetzan, Tanaris",nil,1446,52.3,27.7,"Visit at skill 200; level 35 required.")},
    leatherworking={
        t("Expert","Telonis","Darnassus","Alliance",1457,64.2,21.6),
        t("Expert","Una","Thunder Bluff","Horde",1456,41.8,42.8),
        t("Artisan","Drakk Stonehand","Aerie Peak, The Hinterlands","Alliance",1425,13.4,43.5,"Nightscape Pants at 205 require Artisan; level 35."),
        t("Artisan","Hahrana Ironhide","Camp Mojache, Feralas","Horde",1444,74.4,43.1,"Nightscape Pants at 205 require Artisan; level 35.")},
    tailoring={
        t("Expert","Georgio Bolero","Stormwind","Alliance",1453,53.2,81.4),
        t("Expert","Josef Gregorian","Undercity","Horde",1458,70.4,30.3),
        t("Artisan","Timothy Worthington","Theramore, Dustwallow Marsh","Alliance",1445,66.2,51.8),
        t("Artisan","Daryl Stack","Tarren Mill, Hillsbrad Foothills","Horde",1424,63.7,20.8),
        t("Runecloth Cuffs pattern","Pexmit","Mount Hyjal")},
    ["first-aid"]={
        t("Expert book","Deneb Walker","Stromgarde, Arathi Highlands","Alliance",1417,27,58.8),
        t("Expert book","Balai Lok'Wein","Brackenwall Village, Dustwallow Marsh","Horde",1445,36.5,30.5),
        t("Artisan / Triage","Doctor Gustaf VanHowzen","Theramore, Dustwallow Marsh","Alliance",1445,67.8,49),
        t("Artisan / Triage","Doctor Gregory Victor","Hammerfall, Arathi Highlands","Horde",1417,73.4,36.9),
        t("Major Healing Potion manual","Pexmit","Mount Hyjal",nil,nil,nil,nil,"Manual costs 8 gold.")},
    cooking={
        t("Expert Cookbook","Shandrina","Silverwind Refuge, Ashenvale","Alliance",1440,49.6,67.1),
        t("Expert Cookbook","Wulan","Shadowprey Village, Desolace","Horde",1443,26.1,69.7),
        t("Artisan quest","Dirge Quikcleave","Gadgetzan, Tanaris",nil,1446,52.6,28.1,"Clamlette Surprise: skill 225, level 35.")},
    fishing={
        t("Expert book","Old Man Heming","Booty Bay, Stranglethorn Vale",nil,1434,27.4,77.1,"Skill 125, level 20."),
        t("Artisan quest","Nat Pagle","Dustwallow Marsh",nil,1445,58.6,60.1,"Nat Pagle's Angler Extreme: skill 225, level 35.")},
    herbalism={t("Full trainer","Reyna Stonebranch","Ironforge","Alliance",1455,55.6,59.1)},
}
ns.TrainingTips={
    engineering={common="Keep a Blacksmith Hammer for crafting."},
    tailoring={common="Artisan recipes begin at skill 200. Check rare pattern availability before buying materials for the route past 280."},
    ["first-aid"]={common="Buy the Heavy Silk and Mageweave manuals too. Triage requires skill 225 and level 35 despite the quest's level 45 label.",Horde="The Major Healing Potion manual is also a reward from A Rest Without Pain after Herbs for the Bruised and Weary."},
    cooking={common="Buy fish recipes from vendors and cook beside a fire."},
    mining={common="Junior starting-area trainers stop at 75; visit a full trainer or a capital for Journeyman.",Alliance="Optional bonus: Twilight Mine Light (+4 Mining), from A Miner Problem in Riverglades."},
    herbalism={common="Junior starting-area trainers stop at 75; visit a full trainer for Journeyman."},
    skinning={common="Junior starting-area trainers stop at 75; visit a full trainer for Journeyman.",Horde="Optional bonus: Keen Skinning Knife (+3 Skinning), from Unwelcome Guests in The Barrens."},
    lockpicking={common="Skill cap is five times your character level, up to 300. Use Angor Fortress through 225, then upper Slag Pit footlockers through 300. Reader reports underpin the final range."},
}
function ns.TrainersFor(slug)
    local faction=ns.player and ns.player.faction
    local list={}
    for _,entry in ipairs(ns.Trainers[slug] or {}) do
        if not entry.faction or entry.faction==faction then list[#list+1]=entry end
    end
    return list
end
function ns.PinTrainer(entry)
    if entry.faction and entry.faction~=ns.player.faction then return false,"This trainer is for the other faction." end
    local location=entry.location..(entry.x and (" ("..entry.x..", "..entry.y..")") or "")
    if not entry.map or not entry.x or not entry.y then return false,"No verified map pin for "..entry.name..". "..location end
    if not C_Map or type(C_Map.SetUserWaypoint)~="function" or not UiMapPoint
        or type(UiMapPoint.CreateFromCoordinates)~="function"
        or ns.Safe(C_Map.CanSetUserWaypointOnMap,entry.map)~=true then
        return false,"Map pin unavailable here: "..entry.name..", "..location
    end
    local point=ns.Safe(UiMapPoint.CreateFromCoordinates,entry.map,entry.x/100,entry.y/100)
    if not point or ns.Safe(C_Map.SetUserWaypoint,point)~=true then
        return false,"Could not place map pin: "..entry.name..", "..location
    end
    ns.Safe(C_SuperTrack and C_SuperTrack.SetSuperTrackedUserWaypoint,true)
    if ns.Safe(InCombatLockdown)~=true then ns.Safe(C_Map.OpenWorldMap,entry.map) end
    return true,"Map pin placed: "..entry.name..", "..location..". Replaces your previous waypoint."
end
