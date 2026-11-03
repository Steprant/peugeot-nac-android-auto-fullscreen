# Reproducing the research

Use Python 3.10 or newer for the pinned dependencies. All commands below operate on local host copies unless explicitly described as a future hardware procedure. The project does not supply the required original firmware files.

## Public suite without proprietary fixtures

```bash
python -m pip install -r requirements.txt
python tools/run_public_tests.py
python tools/verify_public_tree.py
```

The runner explicitly loads only the public synthetic-input and metadata test classes. If a selected test is skipped, the run fails. It does not invoke firmware-dependent classes and does not claim to reproduce the historical 53 or 25 full runs. CI runs this suite on Python 3.10 and 3.12.

## Obtain and identify inputs independently

Use `fonti.json`, `integrita_moduli.json`, the upstream extraction project and `installazione_v4/firmware_pins.json` to identify original inputs. Keep them outside the Git repository. Decryption is separate from code signing; no decryption or signing key is included here. Obtain the appropriate files and any required rights independently.

Preserve the original hierarchy inside an extracted NAND rootfs. For the candidate generator the two libraries are:

```text
usr/lib/ovip/AAuto/libAAutoHMILib.so.1.0.0
usr/lib/ovip/HMIInternal/HMIInternalApplication/libHMIInternalApplication.so.1.0.0
```

The AA QML comes from `media/datastore/ui/HMIApplications/AAuto/qml/AAutoHMILib/INTERNET_0033SkinLogic.qml` in the UI resource archive. Additional fixture-dependent tests need the other pinned components listed in `confronto_NAND_eMMC.json` and the respective audit scripts. Do not replace missing fixtures with the generated candidate.

## Generate and restore the revision 3 candidate on the PC

```bash
python patch_fullscreen_lab.py prepare \
  --rootfs /absolute/path/to/extracted-rootfs \
  --ui-file /absolute/path/to/INTERNET_0033SkinLogic.qml \
  --output /absolute/path/to/new-candidate
```

The output must not exist. The tool verifies exact input and plan hashes, produces new `.offline.so`/candidate copies, a cfg and DHU profile, and a manifest with `installable=false` and `vehicle_tested=false`. It neither writes the input files nor constructs an accepted SWL update. `restore-copy` reconstructs new local original copies; the complete component commands are in `PROCEDURA_LABORATORIO.md`. This does not recover an ECU or restore an unknown live cfg.

## Historical revision 3 fixture-dependent suite

Install `requirements-laboratorio.txt` and `requirements-qt-laboratorio.txt`. With all required original inputs:

```bash
NAC_LAB_ROOTFS=/absolute/path/to/extracted-rootfs \
NAC_LAB_UI_FILE=/absolute/path/to/INTERNET_0033SkinLogic.qml \
python -m unittest test_audit_statico test_laboratorio test_fullscreen_coordinato -v
```

The explicit module names select the historical 53-test suite. Missing firmware or Qt causes skips in the historical runner; a skipped run does not reproduce the archived complete result. The public runner is a different suite.

Optional assembly regeneration uses `requirements-asm-laboratorio.txt` and `python verifica_asm.py`. It checks source assembly against the exact plan; it does not execute on a device.

## Revision 4 kernel and signature experiments

Install `installazione_v4/requirements.txt`. Keep all six decrypted kernel NBX files under the AUTO hierarchy documented in its pins, and supply the original extracted rootfs:

```bash
python installazione_v4/audit_accesso.py --rootfs /absolute/path/to/rootfs --decrypted /absolute/path/to/decrypted-modules
python installazione_v4/prove_firma_arm.py --rootfs /absolute/path/to/rootfs
python installazione_v4/test_installazione.py --rootfs /absolute/path/to/rootfs --decrypted /absolute/path/to/decrypted-modules
```

This separate complete suite has 25 tests and requires matching proprietary fixtures. It validates original bytes/checksums and executes selected ARM fragments with explicitly mocked crypto calls. It does not verify a real CMS signature in the target library or prove update acceptance.

The CPIO parser reads entries without extracting links. Absolute rootfs symlinks resolve inside the stable extracted image, not the host root. Keep the extraction unchanged while reading; concurrent filesystem modification is outside the path resolver's guarantee.

## Hardware work not executed

Read `installazione_v4/PROVA_BANCO_DA_ESEGUIRE.md` and `docs/HELP_WANTED.md`. The existing collection script is a proposed read-only stdout collector, not an access method or autorun installer. It has not been executed on a NAC. Hardware identity, electrical interface, authorized access and recovery must be established independently before experimentation.

## 3 November independent checks

The root requirements now include ASN.1 parsing for the public CMS tests; a host `openssl` command is required. The public runner also executes bounded published ARM intervals without OEM ELFs. [The independent review](INDEPENDENT_REVIEW_2026-11-03.md#reproduce-the-new-work) documents the diagnostic CMS tool, original ARM OpenSSL under optional host QEMU, corrected worker/maintenance tests and optional CarPlay scan. The old 25-test V4 log is preserved; the corrected suite adds coverage rather than treating the old isolated 0x2040 fragment as the complete production path. No hardware test is implied by these checks.
