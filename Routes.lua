-- SPDX-License-Identifier: GPL-3.0-or-later
local _, ns = ...
ns.Order = {"alchemy", "blacksmithing", "enchanting", "engineering", "leatherworking",
    "tailoring", "mining", "herbalism", "skinning", "first-aid", "cooking", "fishing", "lockpicking"}
ns.Professions = {
    alchemy={id=171, name="Alchemy", spell=2259},
    blacksmithing={id=164, name="Blacksmithing", spell=2018},
    enchanting={id=333, name="Enchanting", spell=7411},
    engineering={id=202, name="Engineering", spell=4036},
    leatherworking={id=165, name="Leatherworking", spell=2108},
    tailoring={id=197, name="Tailoring", spell=3908},
    mining={id=186, name="Mining", spell=2575, gathering=true},
    herbalism={id=182, name="Herbalism", spell=2366, gathering=true},
    skinning={id=393, name="Skinning", spell=8613, gathering=true},
    ["first-aid"]={id=129, name="First Aid", spell=3273},
    cooking={id=185, name="Cooking", spell=2550},
    fishing={id=356, name="Fishing", spell=7620},
    lockpicking={id=633, name="Lockpicking", spell=1804},
}
ns.TrainerHints = {
    alchemy="Expert: Ainethil, Darnassus (Alliance) / Doctor Herbert Halsey, Undercity (Horde). Artisan: Kylanna Windwhisper, Feralas / Rogvar, Stonard.",
    blacksmithing="Expert: Bengus Deepforge, Ironforge / Saru Steelfury, Orgrimmar. Artisan: Brikk Keencraft, Booty Bay. Imperial Plate recipes: Derotain Mudsipper, Tanaris; level 50. Complete A Blue Light Bargain first to unlock the recipe quests.",
    enchanting="Expert: Kitta Firewind, Tower of Azora / Hgarth, Sun Rock Retreat. Artisan: Annora, Uldaman.",
    engineering="Expert: Springspindle Fizzlegear, Ironforge / Roxxik, Orgrimmar. At skill 200, visit Buzzek Bracketswing in Gadgetzan for Artisan recipes (level 35). Keep a Blacksmith Hammer.",
    leatherworking="Expert: Telonis, Darnassus / Una, Thunder Bluff. At skill 205, Nightscape Pants require an Artisan trainer: Drakk Stonehand, Aerie Peak / Hahrana Ironhide, Camp Mojache (level 35).",
    tailoring="Expert: Georgio Bolero, Stormwind / Josef Gregorian, Undercity. Artisan recipes start at 200: Timothy Worthington, Theramore / Daryl Stack, Tarren Mill. Runecloth Cuffs pattern: Pexmit, Mount Hyjal. Past 280, check rare pattern availability before buying materials.",
    ["first-aid"]="Expert book: Deneb Walker, Arathi Highlands / Balai Lok'Wein, Dustwallow Marsh. Buy Heavy Silk and Mageweave manuals too. Triage needs skill 225 and level 35 despite the quest's level 45 label: Doctor Gustaf VanHowzen, Theramore / Doctor Gregory Victor, Hammerfall. Major Healing Potion manual: Pexmit (8 gold), or the Horde quest A Rest Without Pain after Herbs for the Bruised and Weary.",
    cooking="Expert Cookbook: Shandrina, Ashenvale / Wulan, Desolace. Artisan: Dirge Quikcleave's Clamlette Surprise, Gadgetzan (skill 225, level 35). Buy fish recipes from vendors; cook beside a fire.",
    mining="Junior starting-area trainers stop at 75; visit the full trainer or a capital for Journeyman. Optional Alliance bonus: Twilight Mine Light (+4 Mining), reward from A Miner Problem in Riverglades.",
    herbalism="Junior starting-area trainers stop at 75. Dwarves and gnomes can visit Reyna Stonebranch in Ironforge after the junior trainer.",
    skinning="Junior starting-area trainers stop at 75. Optional Horde bonus: Keen Skinning Knife (+3 Skinning), reward from Unwelcome Guests in The Barrens.",
}
ns.ItemIDs["Giant Egg"],ns.ItemIDs["Zesty Clam Meat"],ns.ItemIDs["Alterac Swiss"]=12207,7974,8932
-- Original compact instructions; factual ranges/locations from the linked guides.
local function route(slug, rows, cap)
    local steps = {}
    for _, row in ipairs(rows) do
        steps[#steps+1] = {from=row[1], to=row[2], action=row[3], alliance=row[4], horde=row[5]}
    end
    ns.Guides[slug] = {cap=cap or 300, steps=steps,
        source="https://www.wow-professions.com/forever/"..slug.."-leveling-guide"}
end
route("mining", {
    {1,65,"Mine Copper. Carry a Mining Pick and enable Find Minerals.","Elwynn Forest", "Durotar"},
    {65,125,"Mine Copper and Tin; Silver unlocks at 75.","Westfall or Wetlands", "Silverpine Forest or Hillsbrad Foothills"},
    {125,175,"Mine Iron; Gold unlocks at 155. Around character level 30, prefer Thousand Needles.","Thousand Needles or Arathi Highlands", "Thousand Needles or Arathi Highlands"},
    {175,245,"Mine Mithril; Truesilver unlocks at 230. Avoid elite areas and crowded caves.","Tanaris or The Hinterlands", "Tanaris or The Hinterlands"},
    {245,275,"Mine small Thorium veins and Mithril.","Un'Goro Crater or Felwood", "Un'Goro Crater or Felwood"},
    {275,300,"Mine Thorium, including rich veins.","Un'Goro Crater or Winterspring", "Un'Goro Crater or Winterspring"},
})
route("herbalism", {
    {1,70,"Gather starter herbs. Enable Find Herbs.","Starting zones", "Starting zones"},
    {70,115,"Gather Mageroyal and Briarthorn; Stranglekelp unlocks at 85.","Loch Modan or Darkshore", "Silverpine Forest"},
    {115,170,"Gather Bruiseweed, Wild Steelbloom and Stranglekelp. Kingsblood needs 125; Liferoot needs 150.","Hillsbrad Foothills or Stonetalon Mountains", "Hillsbrad Foothills or Stonetalon Mountains"},
    {170,205,"Gather Kingsblood, Liferoot, Fadeleaf and Goldthorn.","Arathi Highlands or Stranglethorn Vale", "Arathi Highlands or Stranglethorn Vale"},
    {205,230,"Gather Purple Lotus and Firebloom. Train Artisan before leaving town.","Tanaris or Searing Gorge", "Tanaris or Searing Gorge"},
    {230,270,"Gather Sungrass and Purple Lotus; Ghost Mushroom needs 245.","The Hinterlands", "The Hinterlands"},
    {270,300,"Gather high-level herbs, including Dreamfoil and Plaguebloom.","Felwood", "Felwood"},
})
route("skinning", {
    {1,75,"Skin starter beasts. Keep a Skinning Knife in your bags.","Northshire Valley", "Valley of Trials"},
    {75,150,"Skin beasts appropriate to your skill: level 16-17 until 80, then level 18.","Loch Modan, then Wetlands at 130", "The Barrens"},
    {150,160,"In Hillsbrad, skin bears and mountain lions outside Foothill Caverns before moving to higher-level yetis.","Hillsbrad Foothills", "Hillsbrad Foothills"},
    {160,225,"Skin yetis or worgen. For beasts level 20+, required skill is five times their level.","Hillsbrad Foothills or Duskwood", "Hillsbrad Foothills or Duskwood"},
    {225,280,"Skin the yetis around Feral Scar Vale (beast levels 43-46).", "Feralas", "Feralas"},
    {280,300,"Skin dinosaurs (beast levels 50-55).", "Western Un'Goro Crater", "Western Un'Goro Crater"},
})
route("fishing", {
    {1,75,"Equip a Fishing Pole, apply a lure, and fish in a starting zone rather than a capital."},
    {75,150,"Learn Journeyman, then fish in a capital city. Use Nightcrawlers if needed."},
    {150,225,"Expert book: Old Man Heming, Booty Bay (skill 125, level 20). Fish in Dustwallow Marsh with Bright Baubles."},
    {225,300,"Artisan: Nat Pagle's Angler Extreme (skill 225, level 35), starts in Dustwallow Marsh. Catch Savage Coast Blue Sailfin on western Stranglethorn's coast, Sar'theris Striker on the Desolace coast, Misty Reed Mahi Mahi along Misty Reed Strand in Swamp of Sorrows, and Feralas Ahi in the Verdantis River west of the road bridge. Use Bright Baubles in Feralas. Then fish in Feralas, Tanaris or The Hinterlands with lures."},
})
route("lockpicking", {
    {1,100,"Practice on quickly respawning boxes.","Practice Lockboxes, north of Lake Everstill in Redridge", "Buccaneer's Strongboxes inside the ship near Ratchet"},
    {100,150,"Open Waterlogged Footlockers on shore. At 110, you can also open the higher-level ones underwater.","Zoram Strand, Ashenvale", "Zoram Strand, Ashenvale"},
    {150,225,"Open upstairs footlockers at 150, then downstairs ones at 175. Source reports the downstairs locks give reliable points until 215 and can be used to 225.","Angor Fortress, Badlands", "Angor Fortress, Badlands"},
    {225,300,"Open Dented Footlockers in the Slag Pit. Lower locks need 200; upper locks need 225. Stay with the upper locks after lower ones stop giving points. Source reports upper locks remain yellow to 290, then green through 300. If the Slag Pit is crowded, open Dented Footlockers at Lost Rigger Cove instead.","The Slag Pit or Lost Rigger Cove", "The Slag Pit or Lost Rigger Cove"},
})

-- Rank thresholds are not necessarily route boundaries.
function ns.RankRequirements(slug)
    if slug=="lockpicking" then return {} end
    local gathering = ns.Professions[slug].gathering
    local secondary = slug=="cooking" or slug=="first-aid"
    return {
        {cap=75, skill=50, level=(gathering or secondary) and 1 or 10, name="Journeyman"},
        {cap=150, skill=125, level=(gathering or secondary) and 1 or 20, name="Expert"},
        {cap=225, skill=(secondary or slug=="fishing") and 225 or 200,
            level=gathering and 1 or 35, name="Artisan"},
    }
end
