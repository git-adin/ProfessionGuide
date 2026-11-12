# ProfessionGuide 0.2.0

An independent WoW Forever addon (Interface 16001) with character-aware profession
routes and optional, explicit exports to ItemFarmingTool. No addon dependency,
network access, library or developer tool is needed in game.

## Install and use

Extract `dist/ProfessionGuide.zip` into `_forever_/Interface/AddOns/`. The resulting
path must be `AddOns/ProfessionGuide/ProfessionGuide.toc`. Enable ProfessionGuide
and type `/pg` after logging in.

1. Click the profession button to cycle through your learned professions.
2. Enter the **profession skill** you want to reach (1–300), then click **Plan route**.
3. Select a step in the left route list to see its recipes, estimated crafts and
   ingredients on the right. The shopping table always covers the entire target,
   with separate **Have**, **Need** and **Short** columns and item tooltips.
4. Open **Training & notes** for trainer locations, rank requirements and source
   details. Warnings about the chosen route also appear above the shopping table.
5. If ItemFarmingTool is loaded, click **Export to ItemFarmingTool** to
   add its material goals. Nothing is exported by login, changing targets,
   bag/skill updates, or reloading.

The guide detects profession skill, trained maximum, character level and faction.
All six crafting professions, Mining, Herbalism, Skinning, First Aid, Cooking,
Fishing and Lockpicking are covered. Gathering guides show activities and zones
instead of invented material quantities. Trainer pairs are Alliance / Horde.
Targets and window position are saved per character. Drag the background/title to
move the window; Close or Escape hides it. `/pg reset` restores the position.
The Workshop window uses separate scrolling for the route list and recipe/shopping
details. The selected step survives bag updates and advances when completed.

| Command | Action |
| --- | --- |
| `/pg` or `/professionguide` | Open guide |
| `/pg hide` | Hide guide |
| `/pg select first aid` | Select a detected profession |
| `/pg target 150` | Save the selected profession's target; does not export |
| `/pg reset` | Restore position and show window |

## Estimates and limitations

The bundled factual route snapshot comes from [WoW-Professions.com's Forever
guides](https://www.wow-professions.com/forever), retrieved November 12, 2026.
Instructions are condensed and rewritten; this is not the full website, its maps,
or its alternative routes. See [SOURCES.md](SOURCES.md).

- **Tailoring ends at 265**, matching the available source route. A higher target
  shows an explicit coverage warning. Other default crafting routes reach 300.
- Several source routes at higher skill are provisional. In particular,
  Blacksmithing's Imperial Plate quest skill gates are unverified in the source;
  that route requires character level 50. Check availability before purchasing.
- Each band uses the source's estimated craft count. Partial bands scale that
  count and round up whole crafts. Yellow/green recipes can require more or less.
  These are shopping estimates, not a skill-up probability simulation or live
  auction-house cost comparison.
- Keep intermediate crafts. The planner nets their output against later
  consumption, then expands missing intermediates using recipe ingredients.
  Carried intermediate stock reduces those requirements; banked intermediates
  are not included. Raw leather and metal bars are shopping inputs.
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

Tested against the local ItemFarmingTool **0.2.2**. Uses its existing slash-command
handler, checks its saved goals read-only, and never writes its database directly.
`OptionalDeps` only establishes load order when installed; it is not required.

Exports set **minimum total goals**, preserving existing higher quantities and
unrelated entries. Repeated exports do not add the same quantity again. Existing
goals are not removed when you change/clear a target or finish a band. Review and
remove obsolete goals in ItemFarmingTool yourself. Shared items for two profession
plans use the higher exported goal, **not the sum**; export is one selected route
at a time. The full batch is checked against its 100-item capacity before any
writes. Its own Bags + bank / Bags only setting controls inventory accounting.

## Engineering and validation

Modules have separate responsibilities: data and routes, game API detection,
pure route planning with inventory reads, optional integration, UI, and lifecycle.
Game events batch refreshes; no per-frame polling. The other addons in this
workspace are unchanged.

From this repository's root, run with Python 3 and `lupa` (Lua 5.1):

```powershell
python -m pip install --target .tools -r tests/requirements.txt
python tests/test_addon.py
python tools/package.py
```

The suite executes the shipped Lua, checks every route and item ID, exercises
UI callbacks and detection fallbacks, and tests opt-in exports against both a
test double and the actual sibling ItemFarmingTool when present. The packager
checks the ZIP's contents and CRCs and writes SHA-256 checksums.

For a source refresh, install `beautifulsoup4` for development, run
`tools/inspect_source.py` with the eight crafting-guide slugs listed in
`tools/build_data.py`, then run `tools/build_data.py`. Review all changed ranges,
recipe yields, branches, IDs, trainer/quest notes and source dates before shipping.
The compiler rejects coverage gaps and unresolved IDs are reported. Cached web
pages are ignored and never packaged.

**In-game validation remains necessary:** verify detection on your characters,
window wrapping/scrolling/dragging, rank training messages, a partial target,
skill-ups, reload persistence, and export with and without ItemFarmingTool.
No live WoW client session was used to verify this build.

GPL-3.0-or-later for addon code; see LICENSE. Website text/images are not licensed
or bundled as addon code. This project is not affiliated with WoW-Professions.
