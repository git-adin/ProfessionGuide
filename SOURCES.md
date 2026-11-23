# Source provenance

Snapshot date: **2026-11-23**. Recipe names, skill ranges, estimated craft counts,
ingredient quantities and location facts were checked against the pages below.
Guide prose and maps are not bundled. UI instructions are original summaries.
Upstream guides describe beta-derived and untested higher-level content; the
addon exposes this limitation and does not silently fill missing routes.

- https://www.wow-professions.com/forever
- https://www.wow-professions.com/forever/alchemy-leveling-guide
- https://www.wow-professions.com/forever/blacksmithing-leveling-guide
- https://www.wow-professions.com/forever/enchanting-leveling-guide
- https://www.wow-professions.com/forever/engineering-leveling-guide
- https://www.wow-professions.com/forever/leatherworking-leveling-guide
- https://www.wow-professions.com/forever/tailoring-leveling-guide
- https://www.wow-professions.com/forever/first-aid-leveling-guide
- https://www.wow-professions.com/forever/cooking-leveling-guide
- https://www.wow-professions.com/forever/mining-leveling-guide
- https://www.wow-professions.com/forever/herbalism-leveling-guide
- https://www.wow-professions.com/forever/skinning-leveling-guide
- https://www.wow-professions.com/forever/fishing-leveling-guide
- https://www.wow-professions.com/forever/lockpicking-leveling-guide

Item IDs primarily come from upstream Wowhead item links; ordinary intermediate
and vendor-supply IDs are explicitly mapped in the compiler. Spell IDs come from
the guide's recipe links. No whole shopping list is copied as a fixed goal:
requirements are calculated from the remaining steps and chosen target.

Default branch policy: first continuous recipe branch, the active Strange Dust
Enchanting tab, First Aid bandages at low skill and the first cooking-table option;
both Engineering 135â€“150 components are required. Reviewed alternate branches
are defined in `tools/alternate_routes.py`, including linked replacements. Cooking
table options retain ingredient facts and vendor/quest locations, not guide prose.
Sparse suggestions without verifiable ingredients are not compiled as recipes.
Where the source gives ingredients but no craft count, explicit minimum estimates
are marked in the compiled data and UI. Lesser Agility 165â€“185 uses 22 crafts,
inferred from the source alternative shopping list (39 Soul Dust minus the rod
and oil requirements). Smoked Bear Meat uses the upper end of its source range.
Tailoring now has a complete 1â€“300 route, with rare-pattern and station caveats.
Leatherworking 1â€“30 now uses the source's 35 crafts and 105 scraps. Fire Oil and
Stonescale Oil produce two per craft. See [SOURCE_UPDATE_AUDIT.md](SOURCE_UPDATE_AUDIT.md)
for changed ranges, removed branches, manual sources and gathering corrections.

Client compatibility was cross-checked against installed Forever addons' use of
`C_SkillInfo`, legacy skill APIs and profession APIs. The paired test exercises
the `ItemFarmingToolAPI` in ItemFarmingTool 0.2.5 for material-goal exports.

Icon lookup signatures were checked against Blizzard's generated API definitions
in the [UI source mirror](https://github.com/Gethe/wow-ui-source/tree/live/Interface/AddOns/Blizzard_APIDocumentationGenerated).
Recipe fallback paths reference Blizzard icon names in the guide links. These
are client texture references; no website images or Blizzard image files ship
with the addon.

## November 20 crafting route review

The updated guides change recipe ranges and material estimates. Cooking moves
from its late fish recipes to Nightfin Soup at 285. First Aid defaults to
Runecloth bandages, with Major Healing Potion still available from 275. The
Leatherworking light-hide and Enchanting oil alternatives now end at the
updated route boundaries. The First Aid potion path uses a scaled bandage
count, and the Greater Strength Enchanting alternate uses a minimum estimate.
The source manifest records hashes for the reviewed guide pages.

## November 20 gathering route review

The updated Skinning and Lockpicking guides above move the Loch Modan to
Wetlands transition to skill 130, add a Hillsbrad route for 150-160, and
document underwater locks at 110 and Lost Rigger Cove at 225-300. The recipe
snapshot date above refers to the compiled crafting routes.

## November 21 guide review

Fetched all 13 guide pages and regenerated the eight crafting routes. The
generated Lua matched the November 20 snapshot. The gathering notes now
include where to catch Nat Pagle's four quest fish and the optional Horde
Herbalism bonus from Apothecary Gloves.

## November 22 guide review

Blacksmithing 125–140 now defaults to 15 Silvered Bronze Gauntlets, with
15 Bronze Warhammers as the alternate. The planner accounts for the extra
Coarse Grinding Stones needed for the gauntlets. The source also lists rare
Blessed Plate plans without complete per-step craft estimates. The Enchanting
page removed a character-level claim and its compiled recipe route is unchanged.

## November 23 guide review

Blacksmithing starts the Mithril Spurs alternate at 210 and offers three
finishing routes from 270. Radiant Boots and Leggings are the default.
The planner charges the Imperial Plate recipe quest cost once per recipe,
including when the same bracers span two route bands. Leatherworking adjusts
the early hide, glove and pants ranges. Tailoring uses fewer wool bolts and
switches to Azure Silk Hood at 120. Cooking uses one catfish band from 100
to 150 and updates the clam estimate for 150–175.

## Trainer locations

Trainer roles and profession notes follow the Forever guides listed above.
The static trainer map IDs and coordinates in `Trainers.lua` were cross-referenced
against the installed ForeverDB `NPCs.lua` snapshot on 2026-11-18. Only coordinate
facts are included; no NPC database addon is required. Coordinates are approximate
points, not walking routes. Contacts without coordinates, including Annora inside
Uldaman and newer recipe vendors, remain text only. Map pins use the client's
native `C_Map` waypoint API and are created only by clicking a trainer name.
