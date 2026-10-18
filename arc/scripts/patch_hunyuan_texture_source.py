"""Apply recorded inference-only fixes to the separate paint source checkout."""

import argparse
from pathlib import Path


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    if new in text:
        return
    if text.count(old) != 1:
        raise RuntimeError(f"Pinned source does not match expected patch: {path}")
    path.write_text(text.replace(old, new, 1))


def patch_source(root: Path) -> None:
    replace_once(
        root / "hy3dpaint/textureGenPipeline.py",
        "        for i in range(len(enhance_images)):",
        "        # Modified for ARC POC: resize every view, not the two map types.\n"
        '        for i in range(len(enhance_images["albedo"])):',
    )
    replace_once(
        root / "hy3dpaint/utils/multiview_utils.py",
        "            repo_id=config.multiview_pretrained_path,",
        "            # Modified for ARC POC: pin downloaded paint weights.\n"
        "            repo_id=config.multiview_pretrained_path,\n"
        '            revision=os.environ["HUNYUAN_PAINT_REVISION"],',
    )
    replace_once(
        root / "hy3dpaint/DifferentiableRenderer/mesh_utils.py",
        "import bpy\n",
        "# Modified for ARC POC: bpy is optional; our exporter writes the PBR GLB.\n",
    )
    replace_once(
        root / "hy3dpaint/DifferentiableRenderer/mesh_utils.py",
        '    """Convert OBJ file to GLB format using Blender."""\n',
        '    """Convert OBJ file to GLB format using Blender."""\n'
        "    global bpy\n"
        "    import bpy  # Modified for ARC POC: only needed by this optional converter.\n",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    patch_source(parser.parse_args().source)
