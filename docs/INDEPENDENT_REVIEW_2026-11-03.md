# Independent review: CMS content, maintenance access and deployment

Review of repository `79c854bb877a361f560a652a02368132f3ee409d`, issues [#1](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/issues/1) and [#2](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/issues/2), on 3 November 2026. AI-assisted analysis with newly acquired local firmware inputs. **No installable solution, hardware access or vehicle test has been obtained.**

All 84 files in the starting tree were inventoried and matched against their Git blob IDs. Source, tests, documentation and archived evidence were reviewed. Historical logs were treated as reports to reproduce, rather than fresh measurements. The revision 3 patch plan and its compatibility hashes remain unchanged.

## Findings that change the investigation

### 1. The previous production CMS flag conclusion was wrong

The old `Flags.evaluate()` starts at `0x3776f84c`, inside the branch for an explicitly supplied external content **file**. It correctly observes `0x2040` there, but that entry point omits the earlier branch. Its result was incorrectly labelled production-wide.

The pinned `libswlprodext.so` caller passes NULL for external content. The original `secVerifySignature` wrapper preserves that NULL at worker parameter offset `+8`. Newly traced original worker instructions establish:

| Worker input | Content BIO supplied to CMS | Flags at the call |
|---|---|---|
| External content is NULL, as in the examined MediaVersion caller | BIO returned through `SMIME_read_CMS` | `0x2000`, CMS_NOCRL |
| External content file is supplied | BIO opened from that file; parsed content BIO freed | `0x2040`, CMS_NOCRL plus CMS_DETACHED |

Relevant static addresses in `libsecuUtils.so`, SHA256 `952dbf6e8a96144131960815919236963ece6d681a8db61d2f406491c8b22485`:

- `SMIME_read_CMS` call: `0x3776f4c8`, output BIO slot `[sp+0x14]`.
- External-file decision: `0x3776f7d8`–`0x3776f7e0`, reads worker parameter `+8`.
- NULL branch: `0x3776fd34`, then `0x3776fd4c` loads original flags and `0x3776fd50` loads the parser BIO into `r3`.
- External-file branch adds `0x40` at `0x3776f854`.
- Common `CMS_verify` call: `0x3776f874`.

`ContentSource` now traces the worker from its entry to the CMS call, rather than selecting only the external-file fragment. BIO creation, S/MIME parsing, secure time and X509 setup are explicit substitutes. Execution stops before CMS. This proves the exercised pointer/flag flow, **not cryptography or live updater acceptance**. A negative secure-time case never reaches CMS. The full live caller/wrapper/updater has not been run.

OpenSSL documents that cleartext multipart S/MIME produces a detached-content BIO through `SMIME_read_CMS`. A detached CMS object therefore does not imply a proprietary reconstructed INI preimage. The examined NULL-content path supplies the parser BIO unchanged; it does not establish nickpearce95's proposed reconstruction. Vendor parser behaviour can be checked separately, as below.

CMS_NOCRL ignores CRLs embedded in the CMS when store CRL checks are enabled. It is not a general certificate/revocation bypass. Content, attribute and signer verification skip bits remain absent in both branches. The worker also sets a verification callback and secure time; reproducing the complete trust policy is a separate task.

The old `esito_firma_arm.json`, `evidenze_installazione_v4.json`, `test_esiti_v4.txt` and report snapshot remain historical records. Their generalized `0x2040` interpretation is superseded by this review and the new dataflow evidence.

### 2. The content-digest failure is real, including in the original ARM OpenSSL

The currently retrieved CloudFront metadata reproduces the contributor's exact values:

| Observation | Independently reproduced value |
|---|---|
| MediaVersion.ini SHA256 / size | `ad322b19b5ab5f479e6db3f41c41f29c2007f0cccfb5fae8d0013e808f0e1317` / 4524 bytes |
| CMS digest algorithm | SHA256, despite MIME `micalg=sha1` |
| CMS signing time attribute | `2026-01-27T15:21:05Z` |
| Signed messageDigest attribute | `d3687899c18e66b88950d1c2a23908b73deacb0330fb8c8ee3ba1cd695d68235` |
| OpenSSL reconstructed content | 656 bytes, SHA256 `5be730d1c7d016e855aeaa0a9bae637ab8116e3024bb8213c38a131efbec126c` |
| HashList.ini SHA256 | `4215b23fa1a94f373fa9b0e8b111d57478f72b757fff1f463f8037e1404a4b4b` |

Host OpenSSL 3.0.13 and the **original ARM OpenSSL 1.0.2k/libcrypto from this rootfs**, run in QEMU user mode, both return failure in `cms` and `smime` verification. The ARM CLI emits the same 656 bytes and digest. The ARM OpenSSL executable SHA256 is `5cdeec875409979ff6087c9c41421578fa517be66e22c4fddc3cb9bf9073ab70`; libcrypto SHA256 is `8d74fa9d78f6e71febb4fcd0e34fba5e89c079254bae71dbc53e137314400074`. No crypto calls are mocked in those CLI executions. Neither Linux nor the NAC updater is booted, and no hardware is connected.

The diagnostic CLI uses `-noverify` to separate the content signature from certificate-chain trust. It never disables content or signed-attribute checking. A failure returns a nonzero shell status. A matching HashListChecksum is an integrity link in **unauthenticated metadata**, not a verified signature-to-payload authenticity chain. The signed preimage and cause of this mismatch remain unknown. Finite canonicalization searches cannot exhaustively rule out every preimage, damaged/stale metadata, alternative archive or transformation.

The official Majestic URL listed below serves a differently ordered TAR with the same advertised length, and its initial HashList matches. It did not honor the requested HTTP byte ranges in this environment. A bounded streaming comparison was stopped for low throughput before reaching MediaVersion; that copy's signature was **not tested**. The community updater's “good versus broken” size heuristic was not accepted as proof: the observed CloudFront archive is already 6,312,212,480 bytes. Compare exact metadata hashes and content signatures, not just version or length.

Recovering a valid original signature would establish an original baseline. It would still not sign a modified HashList or patched payload. A public decryption key is not the OEM code-signing key.

### 3. The SWL maintenance image has a different account policy

The production rootfs selects the closed passwd variant, as previously reported. However, **both original SWL initramfs variants** contain a separate regular `/etc/passwd`: root has UID 0, an empty password field and `/bin/sh`. Its file SHA256 is `85983a8fccc16b484187e545e38aa54df74fb9655b45c0916c09c633421b5087`. This is not an unused alternate passwd file in the main rootfs.

That is a useful maintenance lead, not a login demonstration. Both SWL images lack the SSH daemon and SSH service, although a dangling factory-USB target wants-link names that service. A BusyBox telnetd applet link exists, but no listening service, authentication behaviour or reachable console was established. The examined getty service templates are absent. **Do not start an update in the car to search for a shell.** Entry into a factory/update state can write storage before an operator gains control.

The audit now inventories these distinctions directly from the pinned CPIO streams, without extracting links, exposing password hashes or starting a service. A documented entry into the original signed SWL environment, with writes prevented and recovery established, is a more specific research question than assuming the production image offers root login.

The main initramfs still parses `init=`, mounts the real root read-only and has an ash rescue branch on mount failure. The eMMC partition wait can precede that branch. There is still no demonstrated way to control per-session boot arguments or safely reach the rescue shell. Deliberately damaging a filesystem or interrupting power is not a proposed experiment.

The examined HW2019_HD bootloader hash reproduces `dd1816ae000ee7d71e91a64530e1d280bf59083116ab80d4a4329e56474b12f1`. Its strings identify `Bootloader V4.9.2 IMX6 CortexA9`, command-line handling and HAB. These are static implementation clues, not an unlocked U-Boot prompt, fuse reading or proof of the installed board's identity. No bootloader, fuse or partition was changed.

### 4. WHD support is conditional; the reference vehicle remains unidentified

The original ScreenAreas configuration independently confirms WHD `FULLSCREEN=(320,0,1280,720)` and HD9 `FULLSCREEN=(0,0,1280,720)`. The AA candidate is specifically designed for logical WHD 1920×720. A 10-inch diagonal, GT trim and firmware version do not determine that logical class or the physical panel timing.

On a confirmed HD9 display, this candidate has no demonstrated side area to reclaim. On WHD, the archive supports the proposed geometry, but the actual panel, scaling, decoder, compositor, calibration and touch path still require measurements. The safe answer for this particular 2008 is **not yet determined**, rather than “1920-wide confirmed”.

The proposed read-only collector now includes storage and framebuffer/DRM observations. It has **not** been run on a NAC and still requires independently obtained authorized access. A virtual framebuffer can include stacked buffers: it must be correlated with the active mode, panel part number and live ScreenInfo class, not read as a panel datasheet.

### 5. CarPlay: delegation confirmed; the zero-hit claim did not reproduce

The contributor's `CarPlayHMIUIFwkAdaptor::getVisibleArea(bool)` address and 84-byte function size reproduce. The ScreenAreas lookup and shared parent-container constraint remain relevant. This does not establish the absence of other constraints in the complete stack.

The exact two CarPlay libraries were newly hashed and scanned with Capstone ARM32. The claimed zero hits for the selected inline constants did not reproduce. Examples inside named dynamic functions include `mov r2,#640` at `0x37d5e804` in `CCarPlayConfigurationManager::setClientProperties`, and `add r7,sp,#320` at `0x37caca78` in `CarPlayHMIScreenManagerAdaptor::registerScreens`. These immediates can be offsets or other unrelated values; **they do not prove a clamp**. A complete no-clamp conclusion also cannot follow from a negative immediate scan.

The existing decrypted `ui-app-data-resource.tar.gz` already contains CarPlay logic QML. `INTERNET_0008SkinLogic.qml` and `INTERNET_6003SkinLogic.qml` derive from FullscreenContentScreen and use `CarPlayApi.mirroringStartX`, `mirroringWidth` and `mirroringHeight` in their mask geometry. Thus API-provided mirroring dimensions must be reviewed as well as the shared container. This does not finish inspection of every pixel-universe/style asset or demonstrate a CarPlay patch. The new review tool publishes exact library/QML hashes and bounded scan results.

## Installation decision and next experiments

| Route | Current result | Evidence required before an installation claim |
|---|---|---|
| Modified SWL/USB package | Blocked: no accepted package or signing authority | Complete original verification baseline, then a legitimate acceptance route for changed authenticated content |
| Original signed SWL maintenance environment | Specific new static lead; no reachable shell | Documented entry on an identified bench, no implicit storage writes, actual console/authentication and recovery evidence |
| Temporary override after privileged access | Technically plausible, not executed | Verified privilege source, mount namespace, integrity policy and harmless resource reload; removal and original restart measured |
| Boot arguments / recovery | Parser and rescue code exist; entry not demonstrated | Board-specific passive boot evidence and documented per-session control without persistent environment changes |
| Phone/DPI/USB adapter alone | Does not establish control of the Peugeot compositor | No verified route from those settings to the constrained HMI rectangle |

The first physical work should identify NAC board/storage/panel and record an original passive boot on a matching bench. Obtain documented maintenance-entry information, especially for the signed SWL image; do not infer a usable console from an empty password. Establish recovery before any resource substitution. This review performs none of those hardware actions.

Only after those gates should a benign temporary resource prove actual loading. A later AA experiment must measure the 1920×1080 stream with total vertical margin 360, visible crop 1920×720, edge touch, focus/priority transitions, climate access, camera/parking, audio/microphone, reconnect, suspend and return to the exact original state. A bind mount alone does not reload mapped libraries. The vendor UnionFS enable script changes persistent init and is unsuitable as the first temporary experiment.

## Reproduce the new work

Run public checks using root `requirements.txt` and a host OpenSSL installation. Synthetic signatures use ephemeral test keys/certificates only; none are committed.

```bash
python tools/run_public_tests.py
python tools/audit_media_signature.py /local/MediaVersion.ini --hashlist /local/HashList.ini
```

The second command is expected to return **1** on the pinned failing metadata. It prints the digest and signature diagnostics. `--detached-content /local/candidate.bin` checks exact candidate bytes in DER/binary mode, including the real content signature. `--ca-file` additionally requests host chain validation; it does not reproduce the target's trust policy automatically.

With independently obtained pinned local firmware and host qemu-arm:

```bash
python tools/verify_target_smime.py --rootfs /local/rootfs --qemu-arm qemu-arm /local/MediaVersion.ini
python installazione_v4/prove_firma_arm.py --rootfs /local/rootfs
python installazione_v4/audit_accesso.py --rootfs /local/rootfs --decrypted /local/decrypted
python installazione_v4/test_installazione.py --rootfs /local/rootfs --decrypted /local/decrypted
```

The target CLI command is likewise expected to return **1** on this metadata. It copies only the pinned OpenSSL executable to a host temporary directory, uses the original library sysroot, disables OpenSSL configuration and never invokes the updater. QEMU user mode is not a hardware emulator or a security sandbox for untrusted programs.

For the optional CarPlay scan, install `requirements-asm-laboratorio.txt`:

```bash
python tools/review_carplay_geometry.py --rootfs /local/rootfs --ui-module /local/ui-app-data-resource.tar.gz
python verifica_asm.py
```

New results are in [the dated validation directory](validation/independent-2026-11-03). The historical 53-test V3 and 25-test V4 suites were first reproduced without skips from the newly acquired NAND rootfs and six kernel containers. The corrected V4 suite adds worker-path and maintenance-account coverage. The public suite adds real synthetic CMS negative tests and execution of the published geometry/crop/branch intervals. These are separate scopes, not a combined hardware-validation count. The eMMC rootfs comparison was not re-extracted in this review; the eMMC kernel containers were independently checked.

No firmware, complete libraries/QML, certificate, key, private calibration, signed update or vehicle installer is committed. The generated local candidate remains `installable=false` and is outside the repository.

## Primary sources and independently obtained inputs

- [OpenSSL 1.0.2 CMS_verify](https://docs.openssl.org/1.0.2/man3/CMS_verify/) and [SMIME_read_CMS](https://docs.openssl.org/1.0.2/man3/SMIME_read_CMS/): content BIO and verification semantics.
- [OpenSSL 1.0.2k CMS flags](https://github.com/openssl/openssl/blob/OpenSSL_1_0_2k/crypto/cms/cms.h).
- [Stellantis WebPortal screen classes](https://developer.groupe-psa.io/webportal/v1/overview/infotainment-system/): logical application areas, not identification of this vehicle.
- [Google DHU video/margins](https://developer.android.com/training/cars/testing/dhu#video-configuration): protocol/profile feasibility, not NAC decoder acceptance.
- [Peugeot 2019 2008 announcement](https://www.media.stellantis.com/it-it/peugeot/press/nuovo-suv-peugeot-2008-n-next-gen-suv): up-to-10-inch screen, no exact panel timing.
- [Peugeot OSS index](https://www.peugeot.com/en/oss-source-codes.html): no exact 44.07.33.32 source bundle identified in the listed NAC releases.
- [Ludwig's extraction/decryption research, pinned revision](https://github.com/ludwig-v/psa-nac-firmware-reverse-engineering/tree/4ce14d0ff528cf4127dcf141463c3a946d6c8997): local extraction only, not custom-update acceptance.
- [CloudFront archive actually sampled](https://ds4emloty3shq.cloudfront.net/CONTINENTAL/NAC_EU/ovip-int-firmware-version/PSA_ovip-int-firmware-version_44-07-33-32_NAC-r0_NAC_EUR_WAVE4.tar): ETag `10d55f4c74a6c7d8b860d523279afe42-121`, length 6,312,212,480 bytes. Selected members retrieved with HTTP ranges; complete TAR not downloaded.
- [Alternate official Majestic URL](https://majestic-web.mpsa.com/nas/eu/mjb00/PSA/mjbsu/PSA_ovip-int-firmware-version_44-07-33-32_NAC-r0_NAC_EUR_WAVE4.tar): initial HashList checked, MediaVersion comparison incomplete.
- [Community updater source](https://github.com/hjertmann/nac-infotainment-updater): original report about alternate distributions, treated as a lead, not a signature attestation.
- [Original UART reference](https://www.forum-peugeot.com/Forum/threads/nac-acc%C3%A8s-uart.119265/): linked by VLud's original tutorial, but retrieval returned 404 during this review. No pinout or current Wave 4 access procedure was inferred from it.
