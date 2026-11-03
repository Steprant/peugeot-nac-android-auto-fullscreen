# Peugeot NAC Android Auto fullscreen research

[![Public offline checks](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/actions/workflows/public-checks.yml/badge.svg)](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/actions/workflows/public-checks.yml)

Open research into using the original panoramic display of a Peugeot 2008 GT (2020) for Android Auto, while retaining the original infotainment unit and vehicle functions.

**Status: offline research prototype. There is no verified installer and no demonstrated fullscreen operation on a real NAC.** This repository is intended for independent review and collaboration, not installation in a car.

**3 November independent review:** corrected the MediaVersion worker path (`0x2000` with parser content; `0x2040` only for an external file), reproduced the digest failure with original ARM OpenSSL under QEMU, and identified a separate SWL maintenance account policy. **No installer or reachable maintenance login is demonstrated.** [Findings, reproducible commands and remaining gates](docs/INDEPENDENT_REVIEW_2026-11-03.md).

**Collaboration:** [join the reversible-access and deployment investigation in issue #1](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/issues/1).

Target archive: **44.07.33.32_NAC-r0, NAC Wave 4**, UpdateID `001315031692686757`. Hardware part number, board revision, display model and live calibration of the reference vehicle have not been acquired. A firmware version alone does not establish hardware compatibility.

[Italian project notes](README.it.md) · [Technical findings](docs/TECHNICAL_FINDINGS.md) · [Help wanted](docs/HELP_WANTED.md) · [Reproduction](docs/REPRODUCING.md) · [Contributing](CONTRIBUTING.md)

## What the research found

The analyzed WHD configuration divides a 1920 × 720 layout into a 1280-pixel central area and two 320-pixel side panels. Peugeot's native graphics configuration and QML constrain Android Auto to that central container. This is an archive finding, not a measurement of the physical display or an Android Auto USB capture.

The revision 3 candidate coordinates two native libraries, the Android Auto QML screen and a video configuration. It expands the Android Auto container, changes sidebar consent according to native focus and adjusts crop for a 1920 × 1080 frame with 360 total vertical margin. It does not establish that the real decoder, compositor, phone or priority screens accept that profile.

Revision 4 analyzes the update signature path, six original kernel containers, embedded kernel configuration and initramfs. The original initramfs parses `init=` and has a recovery-shell branch. **The ability to control those boot arguments or reach that shell on the actual board has not been demonstrated.** Production account selection, missing SSH components and HAB references are documented separately.

Original ARM fragments reject simulated signature failures and pass CMS flags without disabling content or signer verification. A public firmware decryption key is not an OEM signing key. UnionFS support does not provide initial privileges, and the included vendor enable script would change the persistent init symlink; that is not proposed as a first experiment.

## Current blocker and the help we need

The immediate blocker is a **demonstrated, reversible way to obtain the necessary access and load replacement resources on the exact hardware**, with recovery established before changes. We do not have that access or a signing key.

We welcome independent reverse engineering, an identified matching bench unit, documented maintenance interfaces, review of the ARM/QML candidate, and reproducible measurements of rendering, touch and priority handling. Please start with [the specific research questions](docs/HELP_WANTED.md). Reports about other PSA generations are useful only when their applicability is established.

## Run the tests that need no firmware

Python **3.10 or newer**, plus the host `openssl` command:

```bash
git clone https://github.com/Steprant/peugeot-nac-android-auto-fullscreen.git
cd peugeot-nac-android-auto-fullscreen
python -m venv .venv
# POSIX; on Windows use .venv\Scripts\activate
. .venv/bin/activate
python -m pip install -r requirements.txt
python tools/run_public_tests.py
python tools/verify_public_tree.py
```

The public suite explicitly selects tests that use synthetic inputs, published ARM patch intervals and ephemeral synthetic CMS signatures. OpenSSL checks the real content signature in the CMS tests; they do not authenticate an OEM update. It does not silently skip proprietary-fixture tests and does not validate a NAC. CI runs this public suite, not firmware integration or vehicle tests. [Reproduction instructions](docs/REPRODUCING.md) describe the separate firmware-dependent runs and their limits.

## Test evidence and limits

| Evidence | What actually ran | What it does not prove |
|---|---|---|
| Revision 3 historical log | 53 tests with local firmware inputs, partial ARM execution and desktop Qt | Installation, full Linux boot, NAC Qt 5.5, decoder, complete Wayland or vehicle functions |
| Revision 4 historical log | 25 tests, including pinned original verification fragments and six kernel containers | Real cryptographic acceptance, root access, UART reachability or a signature bypass |
| Public CI suite | Synthetic parser, compatibility, path-resolution and metadata tests | Firmware-dependent tests or real hardware operation |

The 53 and 25 tests are separate historical executions. They are not one integrated 78-test NAC validation. Crypto, Qt and zone-monitor substitutes are identified in the relevant tools. Native touch execution stops before final delivery to Cinemo/the phone. Desktop Qt is 5.15.19 rather than NAC Qt 5.5. No handset, ECU, display or CAN connection was used for those results.

## Repository contents

| Path | Purpose |
|---|---|
| `patch_fullscreen_lab.py`, `patch_fullscreen_plan.json`, `native_*.s` | Hash-pinned revision 3 candidate generator, reversible patch intervals and original assembly sources |
| `prove_arm.py`, `prove_native_fullscreen.py`, `prove_qml_fullscreen.py` | Partial original ARM execution and desktop QML experiments with explicit substitutes |
| `installazione_v4/` | Version-pinned kernel/access audit, original signature control-flow experiments, results and proposed bench procedure |
| `docs/` | English technical findings, reproduction, collaboration questions, sources and the Italian report snapshot |
| `README_v2.md`, `README_v3.md`, `*_v2.*` | Earlier research; do not treat the old partial candidate or old parser stimuli as the current video profile |
| `*_esiti*.txt`, `esito_*.json`, `installazione_v4/esito_*.json` | Historical logs and derived evidence; these are not on-car results |

The candidate generator writes new files on the host PC and rejects mismatched inputs. Its manifest states `installable=false` and `vehicle_tested=false`. Local `restore-copy` reconstructs files; it is not an ECU recovery procedure. There is no SWL package, USB installer or CAN-writing tool here.

## Material boundaries and licensing

The repository contains project source, short patch intervals, hashes, derived metadata and documentation. Complete firmware images, original proprietary ELF/QML files, keys, certificates, VINs and private vehicle backups are excluded. Obtain any required original inputs independently and keep them outside the repository.

Original project contributions are released under the [MIT License](LICENSE). Referenced third-party material and small identification/interoperability excerpts retain their respective rights; see [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md). No Stellantis/PSA/Continental/Google affiliation or endorsement is claimed.

The initial implementation and research documentation were prepared with AI assistance. Independent review is needed. Confirmed source observations, partial emulation, hypotheses and hardware results must remain distinguishable in contributions.
