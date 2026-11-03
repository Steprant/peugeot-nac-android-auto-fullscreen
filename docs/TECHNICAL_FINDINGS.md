# Technical findings

## Scope and evidence

The reference request concerns a Peugeot 2008 GT (2020), original panoramic 10-inch display, firmware 44.07.33.32_NAC-r0 and a Xiaomi 14 with Android 16 over USB. These are user-supplied reference conditions. No live ECU identification, display measurement or phone session was performed.

The analyzed public archive identifies NAC_EUR_WAVE4 and includes multiple hardware/storage families. Its source, ETag, UpdateID, module hashes and analyzed paths are recorded in `integrita_moduli.json` and `installazione_v4/firmware_pins.json`. Matching a manifest hash is not a complete authenticity or installed-hardware attestation.

## Geometry and projection

`/usr/share/ovip/ScreenManager/ScreenAreas.ini` gives WHD MINISTATUSBAR, STATUSBAR and FULLSCREEN the same central rectangle: x=320, y=0, width=1280, height=720. The two QML sidebar components are 320 pixels wide, with the right panel starting at x=1600. The shared `Screen.qml` constrains the WHD child to x=320 and width=ScreenInfo.width-640.

The Android Auto screen is `INTERNET_0033SkinLogic.qml`. Hiding the sidebars alone would leave its central container constrained. The candidate changes the AA-specific screen and two native libraries, leaving shared ScreenAreas.ini and shared parent QML unchanged. The native sidebar guard is limited to exact Android Auto names and focus in the exercised paths.

`/usr/lib/ovip/Android/libAndroidAutoAppLogic.so` contains a reader for `/home/root/cfg`. Relevant keys are `readFromFile`, `screenWidth`, `screenHeight`, `widthMargin`, `heigthMargin`, `videoDPI` and `videoResolution`. The spelling `heigthMargin` is in the binary. This is a local internal file reader, not an exposed USB configuration or proven telecoding switch.

The candidate uses a 1920x1080 encoded frame, total vertical margin 360, horizontal margin 0, DPI 240 and a visible 1920x720 container. The specific crop guard produces y=-180. Physical aspect ratio, decoder support, negotiation and full input dispatch are unverified. WebPortal application dimensions should not be substituted for an observed Android Auto video stream.

## Candidate file compatibility

`patch_fullscreen_plan.json` fixes two original library hashes, candidate hashes, sizes, static locations and reversible intervals. The generator additionally pins the AA QML. It refuses incompatible files and an existing output directory. `patch_fullscreen_lab.py` pins the plan's own SHA256; changing that JSON without a separately reviewed generator revision is not a supported update.

The candidate changes 273 bytes in the AA HMI library and 239 bytes in HMIInternal, including replacement of some diagnostic logging. Preserved prologues, canaries and unwind sections do not prove complete exception behavior. Local restoration does not recover a non-booting ECU or restore a live cfg that was never collected.

## Signature path

In the pinned `usr/lib/libswlprodext.so`, `SwlProdValidateMedia` is at static address 0x11a9c. Its signature call is at 0x124b8. In the exercised fragment only return value 1 continues to 0x12934; failures stop on the cleanup path. In `usr/lib/libsecuUtils.so`, the wrapper at 0x377757b0 passes flags to the worker at 0x3776f468. The old isolated fragment at 0x3776f84c observes 0x2040 only in the external-content-file branch. The 3 November worker trace corrects the MediaVersion path: the caller/wrapper supply NULL external content, so the branch at 0x3776fd34 passes the SMIME_read_CMS content BIO and unchanged flags 0x2000 to CMS_verify at 0x3776f874. No cryptographic skip bits are set. See [the independent review](INDEPENDENT_REVIEW_2026-11-03.md).

The production path does not set the CMS flags that skip content, signed-attribute or signer-certificate verification. The flag definitions match OpenSSL 1.0.2k, the target library's version literal. The partial ARM runs replace cryptographic calls with explicit stubs: they demonstrate branches and arguments, not valid signatures or a bypass.

Host OpenSSL 3.0.13 and the original ARM OpenSSL 1.0.2k/libcrypto under QEMU user mode both fail content verification of the same downloaded MediaVersion.ini. The target CLI reconstructs the same 656 bytes and digest as the host. These CLI runs use -noverify to exclude certificate-chain checking, without skipping content verification. Signed attributes verify only with content checking explicitly disabled, which does not authenticate the metadata. Tested common body canonicalization variations did not resolve the digest mismatch. The cause and actual NAC acceptance remain unknown. Do not describe this discrepancy as a working unsigned-update route.

## Kernel, boot and access

All six analyzed main/SWL/TSW NAND/eMMC kernel containers yield the same 4,715,264-byte Linux body. Its SHA256 is `e62b0624c9034f4835e9b3925d344df713f04cecc2e19462a8f00a85d1af5a37`. The embedded configuration SHA256 is `095b8feeb7d84e8bacffbe8b289e09536c2e562357c14deea600f97b5bbc2d23`. LZOp checksums and the IKCONFIG gzip CRC validate. The kernel reports vendor-suffixed 3.10.53, built on 21 August 2023.

CONFIG_MODULE_SIG is not selected and CONFIG_UNION_FS=m. That does not grant the privilege to load a module or exclude userspace checks. The exact vendor build may contain backports; the version banner alone does not establish a vulnerability.

The main initramfs parses `init=` from /proc/cmdline and passes it to switch_root. It contains a recovery ash branch for a root mount failure without authentication in that function. However, controlled boot arguments, console input, watchdog behavior and safe reachability are not demonstrated. On eMMC a partition-existence wait precedes the mount, so a missing partition may cause a wait rather than a shell. Inducing filesystem damage or mount failure is not a proposed on-car procedure.

In the main production rootfs, the selected passwd symlink points to the closed variant with locked relevant accounts and /bin/false. stdOVIPuser has UID 0 in that archived configuration; the name does not establish non-root isolation. Alternative passwd files do not establish a usable login. Separately, both SWL initramfs archives have a regular passwd with root UID 0, empty password field and /bin/sh. No reachable console or listener has been demonstrated; the SSH daemon/service and examined getty templates are absent even there. The updated audit inventories this distinction directly.

The debug target names SSH, but the examined image paths lack the server and its service. SEM is present; the directly identified system() call uses a constant screenshot command, not a demonstrated arbitrary shell. Runtime reachability and authentication remain unknown.

HABInfo and the examined HW2019_HD bootloader reference HAB secure boot and OTP state. Actual fuse state and the reference vehicle's bootloader are not known. Generic U-Boot instructions or pinouts from other units cannot be assumed applicable.

The included UnionFS enable script persistently replaces /sbin/init. It requires privileges already and is not the proposed first temporary test. A per-file bind mount would also require established privileges, an understood process/mount namespace and actual resource reload. Existing processes may keep libraries mapped.

## Remaining acceptance criteria

A matching bench needs verified identity, original data and a demonstrated recovery path. First obtain passive original boot observations and determine whether a documented, reversible maintenance entry exists. Only after that should a harmless temporary resource prove that modified content is actually loaded.

Fullscreen then needs real Android Auto negotiation, 1080p decoding, complete composition, input mapping, focus transitions, audio/microphone, USB reconnection, suspend/resume and immediate climate access. Camera and parking-sensor priority must be measured rather than inferred from unchanged source files. None of those vehicle-function acceptance criteria has been demonstrated here.

For source links and derived records, see `docs/SOURCES.md`. The longer Italian report is in `docs/report-it.md`.
