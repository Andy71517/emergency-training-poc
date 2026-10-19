"""Background Blender 5.1 worker. Inputs are data paths, never generated code."""
import json
import sys
from pathlib import Path


def main(package, chair, output):
    import bpy
    # Also works when these two scripts are extracted together from a portable batch.
    sys.path.insert(0,str(Path(__file__).resolve().parent))
    from assemble_scenario_rooms import assemble
    output=Path(output)
    output.mkdir(parents=True,exist_ok=True)
    report=assemble(package,chair,output/'rooms.blend')
    scene=bpy.context.scene
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU'
    scene.cycles.samples=16
    scene.render.resolution_x=1280
    scene.render.resolution_y=720
    scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG'
    scene.render.filepath=str(output/'preview.png')
    bpy.ops.render.render(write_still=True)
    report['scene_count']=len(report['rooms'])
    report['physics_simulated']=False
    (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')


if __name__=='__main__':
    args=sys.argv[sys.argv.index('--')+1:]
    if len(args)!=3:
        raise SystemExit('Expected package folder, chair blend, output folder.')
    main(*args)
