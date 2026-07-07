# Collapsed Bookshelf POC Object

**Status:** scenario metadata only. No mesh exists yet.

The blocked-exit hallway scenario includes a collapsed bookshelf as a deterministic obstacle.

What matters now:

- `blocks_path`: whether it blocks the primary exit path
- `moved`: whether the obstacle has been moved aside
- `location`: where the scenario says the object is

Metadata for later:

- collision shape
- rough dimensions
- mass estimate
- material assumption
- whether it is visual-only or a future collision candidate

There is no real bookshelf asset, collision, weight, tipping, force, Unreal import, or physics simulation yet.

## Future asset notes

If this becomes a generated asset later, keep it simple:

- visibly a bookshelf or shelving unit
- believable hallway scale
- not overly detailed
- no branded/logged/personal text
- stable flat-ish contact with the floor
- simple collision shape possible later

This object is useful because it makes blocked-path review easier to understand.

It is not evidence of real hazard modeling.

