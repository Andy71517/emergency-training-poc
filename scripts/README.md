# Local scripts

Run scripts from the repository root after installing the declared dependencies.
[Current status](../docs/current-status.md) separates executed evidence from code.

| Area | Entry points |
| --- | --- |
| Web studio | `run_web_demo.py --port 8772` builds/serves the one-port app; default without the option remains 8765 |
| Session demos | `run_local_demo.py`, `run_menu_demo.py` (presentation pacing), `run_menu_demo.py --fast`, `run_fake_trainee.py` |
| Replay/review | `replay_session.py LOG`, `summarize_log.py LOG`, session comparison helpers |
| Session-client contract | `run_unreal_contract_harness.py`, `preview_unreal_display.py`, `write_unreal_debug_text.py` |
| Blender chair baseline | `blender/repair_hunyuan_chair_backrest.py`, `complete_hunyuan_chair_collisions.py`, `export_hunyuan_chair_unreal.py` |
| Blender rooms | `blender/assemble_scenario_rooms.py`, `blender/studio_worker.py` |
| Generic furniture | `blender/prepare_unreal_asset.py` runs through the backend MCP worker; `prepare_furniture_variant.py` retains the earlier staging CLI |
| Repository checks | `check_json_files.py`; test/lint commands in the CI guide |
| PDFs | `build_doc_pdfs.py` plus the report/deck builders in `docs/` |

The browser is the usual entry point for room and asset work. Do not invoke native
workers with guessed private paths or modify accepted assets in place. ARC job
scripts live in [arc](../arc/README.md); engine scripts live in [unreal](../unreal/README.md).

Session demo helpers use deterministic toy rules. Spatial workers launch real
applications; remote generation uses allocation resources. Saved plans, generated
models and observations remain review evidence, not clinical or operational authority.

- [Workspace setup](../docs/arc-workspace-runbook.md)
- [Asset automation](../docs/asset-automation-runbook.md)
- [Checks](../docs/development/ci.md)
- [PDF rebuilds](../docs/reports/README.md)
