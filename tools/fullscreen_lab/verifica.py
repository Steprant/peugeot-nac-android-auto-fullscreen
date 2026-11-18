"""Verifica la build grafica di laboratorio estratta su PC."""
from pathlib import Path

from config_laboratorio import render_cfg
from patch_fullscreen_lab import PROFILE, QML_DELTA, load_plan


ROOT = Path(__file__).resolve().parent
BLOCKS = {
    "0x37d8c65c": "native_width.bin",
    "0x37da6a54": "native_geometry_guard.bin",
    "0x37d8ebfc": "native_crop_guard.bin",
    "0x378fdea0": "native_status_guard.bin",
}


def verifica():
    rows = [chunk for item in load_plan()["files"] for chunk in item["chunks"]]
    addresses = [row["elf_address"] for row in rows]
    if len(addresses) != len(BLOCKS) or set(addresses) != set(BLOCKS):
        raise ValueError("Il piano non contiene i quattro blocchi attesi.")
    for row in rows:
        filename = BLOCKS[row["elf_address"]]
        binary = (ROOT / "arm" / filename).read_bytes()
        if len(binary) != row["length"] or binary != bytes.fromhex(row["after_hex"]):
            raise ValueError(f"Blocco grafico diverso dal riferimento: {filename}")
    graphics = ROOT / "grafica"
    if (graphics / "AAutoScreen.qml.inc").read_bytes() != QML_DELTA.encode("utf-8"):
        raise ValueError("La modifica QML è diversa dal riferimento.")
    if (graphics / "profilo_WHD.cfg").read_bytes() != render_cfg(PROFILE).encode("ascii"):
        raise ValueError("Il profilo video è diverso dal riferimento.")


if __name__ == "__main__":
    try:
        verifica()
    except (OSError, ValueError) as exc:
        raise SystemExit(f"Verifica fallita. {exc}")
    print("Verificati i quattro blocchi ARM, la modifica QML e il profilo video.")
