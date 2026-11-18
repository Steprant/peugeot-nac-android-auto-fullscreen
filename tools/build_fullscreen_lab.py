#!/usr/bin/env python3
"""Build the PC lab ZIP from the project's reviewed graphics sources."""
import argparse
import hashlib
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from config_laboratorio import render_cfg
from patch_fullscreen_lab import PROFILE, QML_DELTA
from verifica_asm import assemble_graphics

FILENAME = "NAC_Fullscreen_Lab_44.07.33.32.zip"


def build_zip(output_dir, blocks):
    resources = ROOT / "tools" / "fullscreen_lab"
    members = {
        name: (ROOT / name).read_bytes()
        for name in ("patch_fullscreen_lab.py", "config_laboratorio.py", "patch_fullscreen_plan.json",
                     "LICENSE", "THIRD_PARTY_NOTICES.md")
    }
    for name in ("LEGGIMI.txt", "verifica.py"):
        members[name] = (resources / name).read_bytes()
    for name, code in sorted(blocks.items()):
        members[f"arm/{name}.bin"] = code
    members["grafica/AAutoScreen.qml.inc"] = QML_DELTA.encode("utf-8")
    members["grafica/profilo_WHD.cfg"] = render_cfg(PROFILE).encode("ascii")

    output_dir.mkdir(parents=True, exist_ok=True)
    destination = output_dir / FILENAME
    with TemporaryDirectory(dir=output_dir) as temp:
        stage = Path(temp)
        archive = stage / FILENAME
        with ZipFile(archive, "x") as zipped:
            for name, data in members.items():
                # The reference archive uses a fixed date, POSIX mode and entry order.
                info = ZipInfo(name, (2026, 11, 18, 0, 0, 0))
                info.create_system = 3
                info.external_attr = 0o100644 << 16
                zipped.writestr(info, data, compress_type=ZIP_DEFLATED, compresslevel=9)
        unpacked = stage / "check"
        with ZipFile(archive) as zipped:
            zipped.extractall(unpacked)
        subprocess.run([sys.executable, "-B", "verifica.py"], cwd=unpacked, check=True)
        archive.replace(destination)
    return destination


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path, help="Directory for the verified PC lab ZIP")
    path = build_zip(parser.parse_args().output_dir, assemble_graphics())
    print(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")


if __name__ == "__main__":
    main()
