# Project overview

FIELDWORK is a local proof of concept moving toward natural-language emergency
environments and an adaptive training platform. [Current status](current-status.md)
records evidence and open checks; [full vision](full-project-vision.md) describes
the destination.

## Three connected workflows

1. **Room studio:** a hosted ARC model proposes a structured plan. The backend
   validates it, creates seeded chair layouts, persists the batch and produces
   previews/packages. Local Blender and Unreal workers assemble those layouts.
2. **Furniture:** a description requests a generated reference and Hunyuan model
   on ARC. The backend retrieves a bound package, then Blender MCP prepares a
   source-preserving copy, collision proxies, editable `.blend` and Unreal package.
   Its first live automated couch run still needs SSH setup and remote verification.
3. **Session baseline:** manual/scripted actions enter a deterministic YAML engine,
   receive toy-rule findings, update state and produce replayable JSONL review.

The workflows share backend ownership and traceable artifacts. Spatial generation
does not automatically create a playable or validated training scenario. Existing
room workers use the reviewed wooden chair; mixed-furniture resolution and bindings
remain a coordinated extension.

## What has been demonstrated

The user confirmed hosted planning, the generated/reviewed chair, Blender room
assembly, Unreal 5.8 maps and Chaos batches. Real Blender MCP/CoACD preparation
passed on a synthetic fixture. The new automated couch job, generic engine importer
and first live recording still need their distinct checks.

## Boundaries

The app is local and single-user. Rules are software fixtures, models are review
candidates, and physics parameters are demo assumptions. There is no clinical or
protocol validation, production multi-user deployment, live sensing, projection
mapping or validated adaptive training loop.

Use the [documentation index](README.md), [scope](poc-scope.md),
[gap map](full-system-gap-map.md) and [roadmap](roadmap.md) to choose the next step.
