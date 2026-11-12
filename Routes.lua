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
    blacksmithing="Expert: Bengus Deepforge, Ironforge / Saru Steelfury, Orgrimmar. Artisan: Brikk Keencraft, Booty Bay. Imperial Plate recipes: Derotain Mudsipper, Tanaris; level 50. Their lowered quest skill requirements remain unverified.",
    enchanting="Expert: Kitta Firewind, Tower of Azora / Hgarth, Sun Rock Retreat. Artisan: Annora, Uldaman.",
    engineering="Expert: Springspindle Fizzlegear, Ironforge / Roxxik, Orgrimmar. At skill 200, visit Buzzek Bracketswing in Gadgetzan for Artisan recipes (level 35). Keep a Blacksmith Hammer.",
    leatherworking="Expert: Telonis, Darnassus / Una, Thunder Bluff. At skill 205, Nightscape Pants require an Artisan trainer: Drakk Stonehand, Aerie Peak / Hahrana Ironhide, Camp Mojache (level 35).",
    tailoring="Expert: Georgio Bolero, Stormwind / Josef Gregorian, Undercity. Artisan: Timothy Worthington, Theramore / Daryl Stack, Tarren Mill.",
    ["first-aid"]="Expert book: Deneb Walker, Arathi Highlands / Balai Lok'Wein, Dustwallow Marsh. Buy the Heavy Silk and Mageweave manuals too. Artisan requires Triage (skill 225, level 35). Major Healing Potion needs a drop-only manual.",
    cooking="Expert Cookbook: Shandrina, Ashenvale / Wulan, Desolace. Artisan: Dirge Quikcleave's Clamlette Surprise, Gadgetzan (skill 225, level 35). Buy fish recipes from vendors; cook beside a fire.",
}
ns.ItemIDs["Giant Egg"],ns.ItemIDs["Zesty Clam Meat"],ns.ItemIDs["Alterac Swiss"]=12207,7974,8932
-- Original compact instructions; factual ranges/locations from the linked guides.
local function route(slug, rows)
    local steps = {}
    for _, row in ipairs(rows) do
        steps[#steps+1] = {from=row[1], to=row[2], action=row[3], alliance=row[4], horde=row[5]}
    end
    ns.Guides[slug] = {cap=300, steps=steps,
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
    {70,115,"Gather Mageroyal, Briarthorn and Bruiseweed.","Loch Modan or Darkshore", "The Barrens or Silverpine Forest"},
    {115,170,"Gather Bruiseweed, Wild Steelbloom and Kingsblood.","Hillsbrad Foothills or Ashenvale", "Hillsbrad Foothills or Ashenvale"},
    {170,205,"Gather Kingsblood, Liferoot, Fadeleaf and Goldthorn.","Arathi Highlands or Stranglethorn Vale", "Arathi Highlands or Stranglethorn Vale"},
    {205,230,"Gather Purple Lotus and Firebloom. Train Artisan before leaving town.","Tanaris or Searing Gorge", "Tanaris or Searing Gorge"},
    {230,270,"Gather Sungrass and Purple Lotus; Ghost Mushroom needs 245.","The Hinterlands", "The Hinterlands"},
    {270,300,"Gather high-level herbs, including Dreamfoil and Plaguebloom.","Felwood", "Felwood"},
})
route("skinning", {
    {1,75,"Skin starter beasts. Keep a Skinning Knife in your bags.","Northshire Valley", "Valley of Trials"},
    {75,150,"Skin beasts appropriate to your skill: level 16-17 until 80, then level 18.","Loch Modan, then Wetlands at 125", "The Barrens"},
    {150,225,"Skin yetis or worgen. For beasts level 20+, required skill is five times their level.","Hillsbrad Foothills or Duskwood", "Hillsbrad Foothills or Duskwood"},
    {225,280,"Skin the yetis around Feral Scar Vale (beast levels 43-46).", "Feralas", "Feralas"},
    {280,300,"Skin dinosaurs (beast levels 50-55).", "Western Un'Goro Crater", "Western Un'Goro Crater"},
})
route("fishing", {
    {1,75,"Equip a Fishing Pole, apply a lure, and fish in a starting zone rather than a capital."},
    {75,150,"Learn Journeyman, then fish in a capital city. Use Nightcrawlers if needed."},
    {150,225,"Expert book: Old Man Heming, Booty Bay (skill 125, level 20). Fish in Dustwallow Marsh with Bright Baubles."},
    {225,300,"Artisan: Nat Pagle's Angler Extreme quest in Dustwallow Marsh (skill 225, level 35). Then fish in Feralas, Tanaris or The Hinterlands with lures."},
})
route("lockpicking", {
    {1,100,"Practice on quickly respawning boxes.","Practice Lockboxes, north of Lake Everstill in Redridge", "Buccaneer's Strongboxes inside the ship near Ratchet"},
    {100,150,"Open Waterlogged Footlockers.","Zoram Strand, Ashenvale", "Zoram Strand, Ashenvale"},
    {150,200,"Open upstairs footlockers at 150; downstairs ones need 175.","Angor Fortress, Badlands", "Angor Fortress, Badlands"},
    {200,250,"Open lower-area footlockers until 225, then the upper area. Pickpocket for junkboxes.","The Slag Pit, Searing Gorge", "The Slag Pit, Searing Gorge"},
    {250,300,"Pick locks on Blackrock Depths doors and the Shadowforge Lock. Pickpocket Heavy Junkboxes; dungeon entry limits apply."},
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
