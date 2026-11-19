# ProfessionGuide

- Target WoW Forever. Keep the existing root-level TOC and Lua layout. Use the private add-on namespace and initialize per-character SavedVariables on the add-on's `ADDON_LOADED`.
- Keep route data, planning, presentation, and integration code in their existing modules. Preserve standalone planning and require explicit user action to export farming goals.
- Run `python tests/test_addon.py`, `python tests/test_package.py`, and `python tools/package.py`. For a release candidate pass `--tag vX.Y.Z` with the TOC version. Exercise the paired provider tests and record a live Forever smoke test when export behavior changes.
