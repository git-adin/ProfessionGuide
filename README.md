# ProfessionGuide 0.6.0

An independent WoW Forever addon (Interface 16001) with character-aware profession
routes and optional, explicit exports to ItemFarmingTool. No addon dependency,
network access, library or developer tool is needed in game.

## Install and use

[Download ProfessionGuide.zip](https://github.com/git-adin/ProfessionGuide/releases/latest/download/ProfessionGuide.zip)
and extract it into `_forever_/Interface/AddOns/`. The resulting
path must be `AddOns/ProfessionGuide/ProfessionGuide.toc`. Enable ProfessionGuide
and type `/pg` after logging in.
You can also click the book button beside the minimap to open or close the Workshop.
Drag it around the minimap; its position and visibility are saved per character.
The compact **Guide** book button in the Blizzard professions window's title bar,
beside Close, opens the Workshop too. From a recipe tab it selects that profession; from the
overview it keeps your last selection. Opening the guide never sets a target or
exports farming goals.

1. Click the profession button to cycle through your learned professions.
2. Enter the **profession skill** you want to reach (1–300), then click **Plan route**.
   This also adds learned recipes in the chosen remaining route to Blizzard's
   recipe favorites when that profession is open. Existing favorites stay in
   place. Unlearned recipes are skipped; if the profession is closed, open it and
   click **Plan route** again. Bag updates and changing alternatives do not add
   favorites automatically; click **Plan route** to favorite a revised route.
3. Select a step in the left route list to see its recipes, estimated crafts and
   ingredients on the right. The shopping table always covers the entire target,
   with separate **In bags**, **Required** and **To get** columns and item tooltips.
   Where available, use **Recipe option** to choose an alternate and **Compare
   alternatives** to see requirements and material changes before switching.
4. Open **Training & notes** for trainer locations, rank requirements and source
   details. Warnings about the chosen route also appear above the shopping table.
5. If ItemFarmingTool is loaded, click **Export to ItemFarmingTool** to
   add its material goals. Nothing is exported by login, changing targets,
   bag/skill updates, or reloading.

The guide detects profession skill, trained maximum, character level and faction.
All six crafting professions, Mining, Herbalism, Skinning, First Aid, Cooking,
Fishing and Lockpicking are covered. Gathering guides show activities and zones
instead of invented material quantities. Trainer information follows your faction.
Targets and window position are saved per character. Drag the background/title to
move the window; Close or Escape hides it. `/pg reset` restores the position.
The Workshop window uses separate scrolling for the route list and recipe/shopping
details. The selected step survives bag updates and advances when completed.
Blizzard artwork identifies the profession, route steps, recipes, ingredients,
materials and main actions. Icons use the client's spell/item APIs, with legacy
fallbacks and built-in profession/recipe texture paths. Item icons can resolve
before their full tooltip data is cached; unavailable items refresh after their
data arrives. No icon images are downloaded or bundled with the addon.
Recipe artwork takes priority over spell textures because Forever can return a
generic logo for legacy recipe spell IDs.

| Command | Action |
| --- | --- |
| `/pg` or `/professionguide` | Open guide |
| `/pg hide` | Hide guide |
| `/pg select first aid` | Select a detected profession |
| `/pg target 150` | Save the selected profession's target; does not export |
| `/pg reset` | Restore position and show window |
| `/pg minimap` | Toggle minimap button visibility |
| `/pg minimap show` / `/pg minimap hide` | Show / hide minimap button |
| `/pg minimap reset` | Restore minimap button position and show it |

## Gathering routes

Mining, Herbalism, Skinning, Fishing and Lockpicking have a dedicated activity
view. Route steps name the ore, herbs, creatures or locks. The selected band shows
where to go, upcoming unlocks, the following route band and field instructions.
Zone suggestions appear even without a target, follow your faction where relevant,
and offer **Open map** for mapped zones. These buttons open zone maps, not exact
node pins or farming paths. Maps are not opened during combat.

The empty shopping list and crafting cost section are hidden for these activities.
An optional target limits the displayed route without inventing item quantities,
craft counts or farming goals. No other addon is needed for the gathering view.

## Training & trainer pins

Training & notes opens with your next rank and a specific readiness message,
followed by compact trainer cards. **All ranks & guide help** expands the rank
reference and planning help; it stays collapsed by default. Faction-specific trainers and tips follow
the detected Horde or Alliance faction; neutral contacts remain visible. If the
faction is unknown, only neutral contacts appear.

Click a blue trainer name to place and track a native map waypoint and open that
zone's map. This replaces your current waypoint. Locations without verified
coordinates stay plain text. If the map does not allow waypoints, the status line
gives the trainer's location instead. In combat the pin can be placed, but the map
is not opened. No map addon or NPC database is required at runtime.

## Craft cost estimates

Costs appear in a separate card with **Each craft** and **This step** columns.
The shopping list covers the entire remaining route; the cost card covers only
the displayed recipe's step. Hover the card for missing ingredients, price
limitations and details about owned supplies. The card footer names the provider,
scan time when available, and planned craft count. Missing prices are explicit,
and step totals stay blank until a target is planned.

Pricing addons are optional. Supported public APIs: AuctionPriceLite (scanned
quantity costs, with minimum-buyout estimates for older scans), Auctionator v1 (last scanned buyout),
TradeSkillMaster (`DBMinBuyout` and `DBMarket`), and Auctioneer Advanced
(`AucAdvanced.API.GetMarketValue`). Each recipe shows its material cost per craft
and the estimated total for its remaining crafts when a target is planned.
Recipes producing multiple items say how many they make.
Materials already owned are included. Vendor reagents and prepared materials need
their own saved prices; missing quotes are labeled incomplete, never priced as
zero. With AuctionPriceLite stock data, **Scanned buyouts** uses the cheapest
listings needed to fill each material quantity, matching WritCrateLite. The step
total is quoted separately for the entire step; it is not one-craft cost multiplied
by craft count. **Stock short** replaces totals that the saved scan cannot fill;
hover to see quantities found and required. Broad averages across all listings
are no longer shown for AuctionPriceLite. Older scans show **Stock unverified**;
run a new full Scan Prices to enable quantity-aware costs. Known scanned shortages
do not fall back to another provider's unverified unit price.

Without AuctionPriceLite stock data, each recipe uses one provider, choosing the best ingredient coverage;
ties prefer AuctionPriceLite, Auctionator, TradeSkillMaster, then Auctioneer.
Buyout estimates and market values have separate labels. The provider and
scan time (when available) are shown. AuctionPriceLite scan/lookup updates refresh
automatically; all providers refresh when the AH closes or you click Refresh.
Populate/update prices using your auction addon's normal scan or data update.
All guide and planning features work with none of these addons installed.

## Recipe alternatives

The crafting professions, Cooking and First Aid offer recipe alternatives.
The selector appears only for affected steps.
Use **Compare alternatives** to expand each option's recipe source, requirements
and ingredient changes for your full target. Counts do not compare auction prices.

Selections save per character and profession. Alchemy's finishing oil/mana route,
Enchanting's dust/essence paths and high-level Leatherworking choices change as
one choice, including later dependent steps. Enchanting now defaults consistently
to the source's active Strange Dust path. You can restore **Guide default** in
each selector. Different unrelated choice groups can be combined.
The source's 210–245 Mithril Spurs path is linked. Selecting it resets a conflicting
240-270 alternate, and selecting that alternate resets Spurs, preserving one
continuous route. The retired 130-165 Alchemy mana alternate is no longer offered.

Some informal alternates have no source craft estimate. Where ingredient amounts
are specified, these use an explicit one-point-per-craft **minimum**; the recipe,
comparison and shopping list warn that actual materials may be substantially
higher. The 165-185 Lesser Agility estimate is inferred from the source shopping
list. Recipe knowledge is not assumed. Source-noted faction restrictions prevent
selecting the wrong faction's option; level gates warn while allowing future plans.

Changing an option without a target changes the guide preview only. A target is
still required to calculate or export materials. Changing a choice never edits
ItemFarmingTool automatically.

## Estimates and limitations

The bundled factual route snapshot comes from [WoW-Professions.com's Forever
guides](https://www.wow-professions.com/forever), refreshed November 26, 2026.
Instructions are condensed and rewritten; this is not the full website, its maps,
or every informal recipe suggestion. See [SOURCES.md](SOURCES.md).

- **Tailoring now reaches 300**, but after 280 it requires a rare/world-drop
  pattern. Read the availability warnings before purchasing materials. All default
  crafting routes now reach 300. [Source review details](https://github.com/git-adin/ProfessionGuide/blob/main/SOURCE_UPDATE_AUDIT.md).
- **Lockpicking now reaches 300** through the upper Slag Pit footlockers after
  Angor Fortress at 150-225. The source bases this update on reader reports; the
  addon no longer uses BRD or the previous 270 coverage cap.
- Some high-level requirements remain provisional. Imperial Plate requires
  character level 50 and the prerequisite **A Blue Light Bargain** before the
  recipe quests. Check recipe and pattern availability before purchasing.
- Each band uses the source's estimated craft count. Partial bands scale that
  count and round up whole crafts. Yellow/green recipes can require more or less.
  The source now offers ranges for some full shopping lists; this addon uses the
  listed per-step craft estimates and does not promise a particular probability.
  These are shopping estimates, not a skill-up probability simulation or live
  auction-house cost comparison.
- Keep intermediate crafts. The planner nets their output against later
  consumption, then expands missing intermediates using recipe ingredients.
  Carried intermediate stock reduces those requirements; banked intermediates
  are not included. Raw leather and metal bars are shopping inputs.
  **Prepared supplies** shows each intermediate checked, how many carried items
  are credited, and how many are still needed after planned route output. For
  example, the refreshed 164–195 Leatherworking route needs 21 Cured Heavy Hides;
  11 carried leaves ingredients for 10: 10 Heavy Hides and 30 Salt.
  Raw Heavy Hides and Cured Heavy Hides use distinct
  item IDs; owning one never counts as owning the other. Inventory events update
  both the credit and the remaining raw-material totals.
- Materials show totals for the remaining route and your current carried count.
  Tools, recipe purchases, training fees and manuals are separate. Imperial Plate
  recipe quest bars are included unless `IsPlayerSpell` confirms the recipe is
  known; this can overestimate when the client cannot report knowledge. Artisan
  Cooking quest materials are included when that rank is not yet trained.
- The addon warns about character-level and rank gates, while allowing you to
  plan for a future rank. It does not craft, learn recipes, complete quests or
  choose specializations. Gathering recommendations are not combat-safe pathfinding.
- Modern profession APIs, `C_SkillInfo` and legacy skill-line APIs are supported.
  Skill IDs/localized profession spell names identify professions. On a legacy
  client, expand collapsed Skills categories if a profession is missing. The
  guide text itself is English.

## Optional ItemFarmingTool integration

Export requires ItemFarmingTool 0.2.5 or later with `ItemFarmingToolAPI`. If the
add-on is missing or needs an update, the planner and shopping list still work.
`OptionalDeps` establishes load order when both add-ons are enabled.

Exports set **minimum total goals**, preserving existing higher quantities and
unrelated entries. Repeated exports do not add the same quantity again. Existing
goals are not removed when you change/clear a target or finish a band. Review and
remove obsolete goals in ItemFarmingTool yourself. Shared items for two profession
plans use the higher exported goal, **not the sum**; export is one selected route
at a time. ItemFarmingTool checks the entire batch against its capacity before
applying it. Its own Bags + bank / Bags only setting controls inventory accounting.

The addon remembers material lists exported with version 0.3.0 onward. If a new
route needs fewer of those items, it lists the old tracked goals for **manual
review**. These reminders remain after re-exporting until the goals are removed
or adjusted. It cannot attribute goals created before that history existed, and
does not assume that an old goal belongs exclusively to ProfessionGuide.

## Engineering and validation

Modules have separate responsibilities: data and routes, saved recipe choices, game API detection,
pure route planning with inventory reads, optional integration, UI, and lifecycle.
Game events batch refreshes. Publish the ItemFarmingTool build with the public
API before releasing the ProfessionGuide build that uses it.

From this repository's root, run with Python 3 and `lupa` (Lua 5.1):

```powershell
python -m pip install --target .tools -r tests/requirements.txt
python tests/test_addon.py
python tests/test_package.py
python tools/package.py
```

The suite executes the shipped Lua, checks every route and item ID, exercises
UI callbacks and detection fallbacks, and tests opt-in exports against both a
test double and the actual sibling ItemFarmingTool when present. The packager
checks the ZIP's contents and CRCs and writes SHA-256 checksums.

Pull requests and pushes to `main` run both offline suites. A `vX.Y.Z` tag
matching the TOC version runs the same checks and publishes the verified ZIPs
and checksum manifest.

For a source refresh, install `beautifulsoup4` for development, then fetch fresh
pages without overwriting the previous cache:

```powershell
python tools/check_sources.py --date YYYY-MM-DD
python tools/build_data.py --cache-dir tools/.source-cache/checked-YYYY-MM-DD --source-date YYYY-MM-DD
```

Pass `--details` to the checker for changed passages. The old `inspect_source.py`
only fills missing cache files and must not be used to check for fresh updates.
After reviewing the changes, promote the checked HTML to the baseline cache and
record its manifest. Reviewed alternate branches
live in `tools/alternate_routes.py`; Cooking options are read from the source tables.
Review all changed ranges,
recipe yields, branches, IDs, trainer/quest notes and source dates before shipping.
The compiler rejects coverage gaps and unresolved IDs are reported. Cached web
pages are ignored and never packaged.

**In-game validation remains necessary:** verify detection on your characters,
window wrapping/scrolling/dragging, rank training messages, a partial target,
skill-ups, reload persistence, and export with and without ItemFarmingTool.
No live WoW client session was used to verify this build.

GPL-3.0-or-later for addon code; see LICENSE. Website text/images are not licensed
or bundled as addon code. This project is not affiliated with WoW-Professions.
