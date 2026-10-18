# Hunyuan chair cleanup and texture batch

Start with the successful shape run `8052814` (2026-10-18). Its raw GLB has 134,104 vertices and 268,228 triangles. Four collapsed triangles create nonmanifold edges; removing those four yields a watertight mesh with consistent winding and unchanged bounds. The preview shows a recognisable chair; partially filled backrest gaps remain a visual limitation. Scale and physics are still unverified.

This batch preserves the raw run and writes a new texture result. The full-resolution cleaned mesh is retained as `chair-cleaned.glb`; an 80,000-face working copy is used for UV unwrapping and painting. Review that reduction visually before using it for the final demo. There is no remeshing of the chair during painting, and this batch does not regenerate shape.

## Build

From the repository root in Open OnDemand, switch to `codex/arc-hunyuan-textures` and run:

```bash
bash arc/scripts/check_hunyuan_texture_access.sh
bash arc/scripts/submit_hunyuan_texture.sh build
```

The access check sends small HEAD requests for paint, DINOv2, and Real-ESRGAN weights before allocating a GPU. The build clones the working shape environment into `hunyuan21/texture-environment`, copies the pinned source into `hunyuan21/texture-source`, installs UV/paint dependencies, and compiles the CUDA rasterizer and C++ inpainting helper. It then verifies imports and CUDA. Plan for additional project storage for the cloned environment and model caches. The existing shape runtime is preserved.

Monitor `squeue -j JOB_ID`, then `sacct -j JOB_ID -X --format=JobID,State,ExitCode,Elapsed`. Build logs are `arc/results/hunyuan-texture-build-JOB_ID.{out,err}`. Continue only after `COMPLETED`, `0:0`, and `Hunyuan texture imports and CUDA: OK` in the output.

The separate paint source receives recorded fixes: resize all generated views rather than just two; pin the paint checkpoint revision; defer the optional `bpy` import until its Blender converter is called. Our own GLB exporter replaces that converter for this lane. BasicSR receives a runtime compatibility alias for torchvision's removed `functional_tensor` import. The source diff and package freeze are saved under `hunyuan21/metadata`.

## Paint the existing chair

```bash
bash arc/scripts/submit_hunyuan_texture.sh paint 8052814
```

The source ID is explicit so a different raw chair cannot be selected accidentally. The job uses its saved foreground reference, six views at 512 resolution, and final texture maps at 1024 square. Paint and DINOv2 model revisions are pinned. Initial downloads occur on the compute node; weights remain cached for subsequent attempts.

Logs are `arc/results/hunyuan-paint-JOB_ID.{out,err}`. Results go to `$ARC_PROJECT_WORKSPACE/hunyuan21/outputs/wooden-chair-textured-JOB_ID/`:

- `chair-raw.glb`, `source-manifest.json`: copies of the source evidence; the original run remains untouched.
- `chair-cleaned.glb`: full generated geometry with four collapsed triangles removed.
- `chair-paint-input.obj`: the reduced working copy used for UV unwrapping.
- `chair-textured.obj`, `.mtl`, and generated `.jpg` maps: upstream paint output.
- `chair-textured.glb`: explicit embedded base-color and metallic/roughness maps. glTF packs roughness in green and metallic in blue. UVs and material maps are checked after reloading the exported GLB.
- `metallic-roughness.png`: the packed material map for inspection.
- `preview.png`, `turntable.mp4`: a lightweight base-color preview sampled from the GLB's UVs, with simple diffuse shading. This preview does not evaluate the full PBR shader; inspect roughness/metallic appearance in Blender.
- `manifest.json`: cleanup counts, model revisions, source hash, stage, material checks, and preservation status.
- `LICENSE`, `Notice.txt`, `source-patches.diff`: provenance and upstream notices.

A failure during preview generation must not trigger another paint inference run: first inspect the exported GLB and manifest stage. Keep the OBJ and texture maps together when transferring them; the GLB is self-contained.

## Review and next batch

Download the textured GLB, preview, turntable, and manifest through Open OnDemand. Check wood appearance, seams, back surfaces, and whether reduction changed the chair silhouette. Once this passes, continue to Blender for physical scale, orientation, final cleanup, and simple collision geometry, then Unreal/Chaos. No mass, friction, physical scale, or collision behavior has been validated by generating a closed mesh or PBR maps.

Prepared scripts have local syntax checks and direct mesh/export checks. Actual texture extension compilation and model execution still require ARC. The original geometry generation succeeded; texture generation is not yet a completed milestone.
