"""Stage menu data in a NEW output directory. No EXE patch or game launch."""
import argparse
import hashlib
import json
from pathlib import Path

from build_static_custom_menu import (archive_entry, custom_menu_scene,
                                     custom_mission_scene, custom_text_tables,
                                     split_custom_catalogues,
                                     EXPECTED_SOURCE_SHA256, PROJECT)
from custom_mission_packages import load_library


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original", type=Path, required=True)
    parser.add_argument("--library", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    original, library, output = args.original.resolve(), args.library.resolve(), args.output.resolve()
    if output.exists():
        raise SystemExit("Output must be a new directory; existing files are never overwritten.")
    if output == original or original in output.parents or library in output.parents:
        raise SystemExit("Output cannot be an installation or mission library directory.")
    if PROJECT not in output.parents:
        raise SystemExit("This experimental preparation is confined to the project directory.")
    original_exe = original / "HD2_SabreSquadron.exe"
    if hashlib.sha256(original_exe.read_bytes()).hexdigest().upper() != EXPECTED_SOURCE_SHA256:
        raise SystemExit("Unsupported original client. Nothing generated.")
    packages = load_library(library, write_registry=False)
    module = PROJECT / "build/HD2.CustomMenu.experimental.asi"
    files = {
        "Models/singleplayer.4ds": custom_menu_scene(archive_entry(original, "Models\\singleplayer.4ds")),
        "Models/single mission 2.4ds": custom_mission_scene(
            archive_entry(original, "Models\\single mission 2.4ds")
        ),
        "scripts/HD2.CustomMenu.asi": module.read_bytes(),
    }
    for name, data in split_custom_catalogues(
        archive_entry(original, "GameData\\Gamedata01.gdt"), packages).items():
        files["GameData/" + name] = data
    for path, data in custom_text_tables(original, packages).items():
        files[path.relative_to(original).as_posix()] = data
    # No official catalogue (00/01) or commercial executable may enter this output.
    assert not any(name.lower().endswith(".exe") for name in files)
    assert not any(name.lower() in ("gamedata/gamedata00.gdt", "gamedata/gamedata01.gdt") for name in files)
    manifest = {
        "status": "experimental_not_gui_validated",
        "game_launched": False,
        "installed": False,
        "original_exe_sha256": EXPECTED_SOURCE_SHA256,
        "mission_library": str(library),
        "package_count": len(packages),
        "note": "Menu files only; not a distributable package. Mission payloads are not copied.",
        "files": {name: hashlib.sha256(data).hexdigest() for name, data in files.items()},
    }
    output.mkdir(parents=True)
    for name, data in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    (output / "PREPARATION_ONLY.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(json.dumps({"output": str(output), "files": len(files), "status": manifest["status"]}))


if __name__ == "__main__":
    main()
