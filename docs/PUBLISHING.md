# Maintaining the public project

The public repository is `Steprant/peugeot-nac-android-auto-fullscreen`. This document replaces the preparation-stage note about repository creation.

The initial public tree imports the offline research and adds English documentation, MIT licensing for original contributions, issue/PR templates and public-fixture CI. The firmware-dependent historical test results are preserved separately from the public suite.

Before publishing an update, run `python tools/run_public_tests.py` and `python tools/verify_public_tree.py` using the pinned requirements. Refresh `CHECKSUMS_SHA256.txt` deliberately when reviewed distributable files change. Public CI must not download proprietary firmware or require private hardware data.

Keep firmware inputs outside the repository and preserve the exact revision 3 plan hash unless a new candidate revision is explicitly reviewed. A green public workflow does not establish installation, cryptographic acceptance or operation on a real NAC.

The first collaboration issue asks for a demonstrated reversible access/deployment route on matching hardware. Further research questions and evidence requirements are in `docs/HELP_WANTED.md`.
