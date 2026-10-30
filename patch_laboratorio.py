#!/usr/bin/env python3
"""Patch parziale per COPIE LOCALI. Non installa firmware e non sblocca da sola il fullscreen."""
import argparse
import hashlib
import json
import os
import stat
from pathlib import Path

FIRMWARE = "44.07.33.32_NAC-r0"
HMI_SHA256 = "729c8f66ad835ce6fb62833311e635474a32213dfac0545257f925da29a98585"
HMI_SIZE = 518940
OFFSET = 0x3C65C
ADDRESS = 0x37D8C65C
BEFORE = bytes.fromhex("0500009a")  # ARM: bls 0x37d8c678
AFTER = bytes.fromhex("050000ea")   # ARM: b   0x37d8c678
# Set after deriving the candidate from the hash-pinned original; checked in both directions.
PATCHED_SHA256 = "c4f9f14e9789ec788983333cb6bd76104eefcc0ac9993e3f5dbe8229d2dd0a9f"

def digest(data):
    return hashlib.sha256(data).hexdigest()

def candidate(data, restore=False):
    wanted = PATCHED_SHA256 if restore else HMI_SHA256
    if len(data) != HMI_SIZE or digest(data) != wanted:
        raise ValueError("Dimensione o SHA256 incompatibile: operazione rifiutata.")
    old, new = (AFTER, BEFORE) if restore else (BEFORE, AFTER)
    if data[OFFSET:OFFSET + 4] != old:
        raise ValueError("Istruzione attesa assente.")
    result = data[:OFFSET] + new + data[OFFSET + 4:]
    expected = HMI_SHA256 if restore else PATCHED_SHA256
    if digest(result) != expected:
        raise ValueError("SHA256 del risultato inatteso.")
    return result

def read_copy(path):
    path = Path(path)
    if not stat.S_ISREG(path.lstat().st_mode):
        raise ValueError("Serve un file regolare locale, senza collegamenti simbolici.")
    return path.read_bytes()

def write_new(path, data, restore=False):
    path = Path(path)
    suffix = ".restored.so" if restore else ".offline.so"
    if not path.name.endswith(suffix):
        raise ValueError("La destinazione deve terminare con " + suffix)
    # Exclusive creation: no input, previous result, or existing library is overwritten.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as out:
            out.write(data)
    except BaseException:
        path.unlink(missing_ok=True)
        raise

def describe(data):
    sha = digest(data)
    return {
        "firmware_analizzato": FIRMWARE,
        "file": "usr/lib/ovip/AAuto/libAAutoHMILib.so.1.0.0",
        "dimensione": len(data), "sha256": sha,
        "originale_compatibile": sha == HMI_SHA256 and len(data) == HMI_SIZE,
        "candidato_riconosciuto": sha == PATCHED_SHA256 and len(data) == HMI_SIZE,
        "funzione": "AAutoHMIUIFwkAdaptor::getVisibleArea()",
        "indirizzo_ELF": hex(ADDRESS), "offset_file": hex(OFFSET),
        "byte_originali": BEFORE.hex(), "byte_candidati": AFTER.hex(),
        "effetto_limitato": "Salta la riduzione a 1280 e il ricentramento, se l'area ricevuta e piu larga.",
        "fullscreen_completo": False, "installabile_verificato": False,
        "prove_veicolo": False,
    }

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("azione", choices=("inspect", "prepare", "restore-copy"))
    ap.add_argument("input", type=Path)
    ap.add_argument("output", type=Path, nargs="?")
    a = ap.parse_args()
    try:
        data = read_copy(a.input)
        if a.azione == "inspect":
            if a.output is not None:
                raise ValueError("inspect non accetta una destinazione.")
            result = describe(data)
            if not (result["originale_compatibile"] or result["candidato_riconosciuto"]):
                raise ValueError("File incompatibile.")
        else:
            if a.output is None:
                raise ValueError("Manca il nuovo file di destinazione.")
            restore = a.azione == "restore-copy"
            out = candidate(data, restore=restore)
            write_new(a.output, out, restore=restore)
            result = describe(out)
            result["output_locale"] = str(a.output.resolve())
            result["input_modificato"] = False
        print(json.dumps(result, indent=2))
    except (OSError, ValueError) as exc:
        ap.exit(2, str(exc) + "\n")

if __name__ == "__main__":
    main()
