#!/usr/bin/env python3
"""Reassemble the fullscreen graphics instructions for the pinned Wave 4 firmware."""
import json
from pathlib import Path

from patch_fullscreen_lab import load_plan


ROOT = Path(__file__).resolve().parent
SOURCES = {
    0x37DA6A54: "native_geometry_guard.s",
    0x37D8EBFC: "native_crop_guard.s",
    0x378FDEA0: "native_status_guard.s",
}
WIDTH_ADDRESS = 0x37D8C65C
WIDTH_NAME = "native_width"


def assemble_graphics():
    from keystone import KS_ARCH_ARM, KS_MODE_ARM, KS_MODE_LITTLE_ENDIAN, Ks

    assembler = Ks(KS_ARCH_ARM, KS_MODE_ARM | KS_MODE_LITTLE_ENDIAN)
    blocks = {}
    for spec in load_plan()["files"]:
        for chunk in spec["chunks"]:
            address = int(chunk["elf_address"], 0)
            if address == WIDTH_ADDRESS:
                name, source = WIDTH_NAME, "b 0x37d8c678"
            else:
                filename = SOURCES[address]
                name, source = Path(filename).stem, (ROOT / filename).read_text(encoding="utf-8")
            encoded, _ = assembler.asm(source, addr=address)
            code = bytes(encoded)
            code += bytes(-len(code) % 4)
            remaining = chunk["length"] - len(code)
            if remaining < 0 or remaining % 4:
                raise ValueError(f"Invalid size for {name}")
            code += bytes.fromhex("00f020e3") * (remaining // 4)
            if code != bytes.fromhex(chunk["after_hex"]) or name in blocks:
                raise ValueError(f"Assembly differs from the reviewed plan for {name}")
            blocks[name] = code
    if len(blocks) != len(SOURCES) + 1:
        raise ValueError("Incomplete assembly verification")
    return blocks


def main():
    blocks = assemble_graphics()
    results = [
        {"source": name, "matches_pinned_plan": True, "bytes_with_padding": len(blocks[Path(name).stem])}
        for name in SOURCES.values()
    ]
    print(json.dumps({
        "scope": "Assembly reproducibility only, not a device test",
        "results": results,
        "width_instruction_verified": True,
    }, indent=2))


if __name__ == "__main__":
    main()
