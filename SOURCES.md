# Source provenance

Snapshot date: **2026-11-12**. Recipe names, skill ranges, estimated craft counts,
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
both Engineering 135–150 components are required. Reviewed alternate branches
are defined in `tools/alternate_routes.py`, including linked replacements. Cooking
table options retain ingredient facts and vendor/quest locations, not guide prose.
Sparse suggestions without verifiable ingredients are not compiled as recipes.
Where the source gives ingredients but no craft count, explicit minimum estimates
are marked in the compiled data and UI. Lesser Agility 165–185 uses 22 crafts,
inferred from the source alternative shopping list (39 Soul Dust minus the rod
and oil requirements). Smoked Bear Meat uses the upper end of its source range.
Tailoring 265–300 has no source recipe and is deliberately unavailable. The
Leatherworking 1–30 estimate of 100 scraps for 33 crafts is normalized to the
actual whole-craft ratio of three scraps. Fire Oil produces two per craft.

Client compatibility was cross-checked against installed Forever addons' use of
`C_SkillInfo`, legacy skill APIs and profession APIs, and ItemFarmingTool 0.2.2's
actual command handler. This is compatibility evidence, not a live client test.

Icon lookup signatures were checked against Blizzard's generated API definitions
in the [UI source mirror](https://github.com/Gethe/wow-ui-source/tree/live/Interface/AddOns/Blizzard_APIDocumentationGenerated).
Recipe fallback paths reference Blizzard icon names in the guide links. These
are client texture references; no website images or Blizzard image files ship
with the addon.
