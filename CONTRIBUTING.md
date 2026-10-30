# Contributing

Start with `docs/HELP_WANTED.md`. Open a research issue with one bounded question, the exact firmware/source hashes, the observed code path and the smallest experiment capable of resolving it. English is preferred for shared technical discussion; Italian is welcome.

## Reproduce before extending

Run `python tools/run_public_tests.py` and `python tools/verify_public_tree.py` using Python 3.10 or newer and `requirements.txt`. These tests require no firmware. Read `docs/REPRODUCING.md` for the separate fixture-dependent tests. A green public CI run is not a firmware integration result.

Keep the original hash-pinned revision 3 plan unchanged when reviewing existing results. A change to the plan or candidate needs a distinct revision, new reviewed hashes and new output; do not loosen compatibility guards to make another version pass. Preserve the ability to reconstruct local originals byte for byte.

## Evidence in a pull request

Explain the problem, final change, exact inputs, tests actually run and remaining limits. Identify every stub, manually selected entry point or skipped call. Report missing inputs and skipped tests. Include source paths and static addresses for binary observations, while distinguishing static and runtime addresses.

Do not describe partial Unicorn execution, desktop Qt, a DHU session, a successful file conversion or an available diagnostic service as a demonstrated working NAC patch. Do not claim retained climate/camera/parking functions without measurements on matching hardware. Do not infer a CVE from a version banner alone.

Keep original firmware and private hardware data outside Git. Submit hashes, minimal necessary excerpts and redacted findings. Do not attach full dumps, VINs, keys, certificates or private vehicle backups. Do not introduce device-writing, flashing or persistent boot changes into a host-side test command.

## Hardware reports

State whether the result is static analysis, a proposed experiment, an independently authorized bench test or an on-vehicle result. Identify board revision, storage family, firmware and panel where available. Describe recovery and what was actually restored. Never mark a bench plan as executed merely because it exists in this repository.

Contributions of original project code are under the MIT license in `LICENSE`. Identify and preserve any third-party terms. AI-assisted contributions are welcome with disclosure and reproducible evidence; review responsibility remains with the contributor.
