# Upstream guide review — November 15, 2026

Compared fresh downloads of all **13 supported profession guides** with the
November 12 source cache. Refreshed the compiled routes and manually reviewed
the alternate definitions, trainer notes, and gathering recommendations.

| Guide | Findings applied |
| --- | --- |
| Alchemy | Elixir of Minor Force is now the starter default. Artisan route: Nature Protection to 235, Greater Intellect to 250, make Stonescale Oil at 250–260, Greater Intellect to 265, then Greater Defense. The mana alternate now changes 250–300 together. Stonescale Oil's two-item yield is accounted for. |
| Blacksmithing | Coarse Grinding Stone now covers 50–75; removed the copper gauntlet step. Silver Rod is the 75–80 default, with copper belts as alternate. Added spurs at 230–240. Replaced retired Ebon Shiv/Radiant Belt/Ornate Handaxe suggestions with current rapier/hammer/Thorium Bracers options. |
| Enchanting | Essence route now uses 49 Minor Absorptions at 70–109. Final route uses 40 Greater Stamina shield enchants to 299, then the Arcanite Rod; the extra shield alternate is explicitly a minimum estimate. |
| Engineering | Main craft counts are unchanged. Added vendor/bind-on-pickup instructions for Thorium Widget and Thorium Tube schematics. |
| Leatherworking | Refreshed the early hide path and all 130–195 ranges. Barbaric Shoulders extend to 170, Guardian Gloves to 185, then Barbaric Harness to 195. Added Blue Suede Shoes, bracers from 275, and hats from 280 with the Sewing Machine warning. Removed retired low-level alternate paths. |
| Tailoring | Route now reaches 300. Added leggings at 190, Artisan shoulders at 200, Runecloth bolts at 205, cuffs at 250, and shoulders at 280. Wizardweave Turban is selectable as the final alternate. Added pattern vendor and rare-pattern warnings. |
| First Aid | Craft counts unchanged. Major Healing Potion manual is available from Pexmit or the Mount Hyjal quest A Rest Without Pain; removed the obsolete drop-only instruction. |
| Cooking | Updated table defaults and quantities. Goblin Deviled Clams is the 150–175 default; Roast Raptor uses 55 crafts at 175–225. The last band is now 225–300 using about 140 Spotted Yellowtail or Filet of Redgill. Removed retired table recipes. |
| Mining | Reviewed existing ranges; added junior-trainer guidance and the optional Alliance Twilight Mine Light skill bonus. |
| Herbalism | Reviewed ranges and corrected the condensed recommendations: Stranglekelp at 70–115; Hillsbrad/Stonetalon at 115–170; updated Ironforge trainer guidance. |
| Skinning | Reviewed existing ranges; added the optional Horde Keen Skinning Knife bonus. |
| Fishing | Readable differences were formatting; no route/rank changes. |
| Lockpicking | Readable content unchanged. |

The source replaced list markup with route-step blocks. The compiler now handles
both formats, reads the final Tailoring recipe table, validates complete coverage,
and refuses unknown ingredient IDs. `tools/source_manifest.json` records the
download URLs, review date and HTML hashes; full downloaded pages remain ignored.

Remaining qualifications:

- The source still describes beta-derived information. Imperial Plate quest skill
  requirements remain unverified and its quests still need character level 50.
- Tailoring after 280 depends on rare patterns. The source's Loom/reputation routes
  are called out as additional conditional routes; they are not silently treated
  as trainer recipes. Blue Suede Hat requires access to another leatherworker's
  Sewing Machine before skill 300.
- Counts remain estimates, with explicit minimum labels where the source gives no
  full count. Prefixes of new linked branches use the same proportional estimate
  policy as partial bands.
- Retired saved options reset to the current guide default. Targets, prepared-item
  credits and export history are preserved. No ItemFarmingTool goals are changed
  by the refresh; review old exported goals against the new requirements.
- This audit verifies parity with the selected source, not live auction prices or
  actual skill-up probabilities. In-game validation of the refreshed routes remains
  necessary.
