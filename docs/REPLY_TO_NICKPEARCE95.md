# Draft reply to nickpearce95 — issue #2

Prepared for review; not posted as an issue comment.

Thank you for the independent checks. I obtained fresh local copies of the same CloudFront firmware members and reproduced the AA library/QML hashes, patch bytes, MediaVersion hash, SHA256 SignerInfo, signing-time attribute, detached CMS structure, 656-byte reconstructed content, digest mismatch and HashListChecksum link. The historical 53-test AA suite and 25-test access suite both reproduced without skips.

I found a mistake in our own earlier CMS analysis that changes Q2. The `0x2040` experiment entered the worker at `0x3776f84c`, inside the external-content-file branch. The MediaVersion caller actually passes NULL for external content, and the wrapper preserves it. Starting the original worker at `0x3776f468` gives:

| Input | BIO reaching CMS_verify | Flags |
|---|---|---|
| External content NULL | BIO returned by SMIME_read_CMS | `0x2000` |
| External content file supplied | BIO opened from that file | `0x2040` |

The NULL branch is at `0x3776fd34`; `0x3776fd50` loads the parsed BIO into `r3` and branches to the common verification setup. These new Unicorn traces stop before the CMS call and explicitly substitute BIO creation, parsing, secure time and X509 setup. They prove this branch/pointer flow, not a valid signature. I have corrected the tool and added regression tests rather than editing the historical logs.

There is now also a real target-crypto check: the original ARM OpenSSL 1.0.2k executable and pinned libcrypto were run under QEMU user mode. Both `cms -verify -noverify` and `smime -verify -noverify` fail with the same 656-byte output and SHA256 `5be730d1…bec126c`. No cryptographic calls are mocked in those CLI runs. This does not execute the updater or reproduce its complete certificate/time/revocation policy.

Together with OpenSSL's documented cleartext-S/MIME BIO behaviour, this does not support the proposed reconstructed-INI explanation for the examined NULL-content path. The preimage remains unknown. I would also describe the canonicalization results as exclusion of the tested candidates, rather than exhaustive exclusion of every possible preimage. The matching HashListChecksum is a useful integrity link, but the authenticity chain remains incomplete while the content signature fails. Recovering a valid original baseline would still not authorize a modified package.

For deployment, the new static lead is the original SWL initramfs: both NAND and eMMC variants have a separate root account with an empty password field and `/bin/sh`. That differs from the closed production rootfs. However, the SSH daemon/service and examined getty templates are absent; a dangling SSH wants-link and BusyBox telnetd applet do not establish a listener or reachable login. The useful collaboration question is a documented, reversible, write-controlled entry into that original signed maintenance environment on identified bench hardware. There is still no safe installer, demonstrated privileged entry or recovery result. No hardware actions were performed.

I also checked the CarPlay material. The 84-byte adaptor and stated getVisibleArea symbols reproduce. I could not reproduce the zero-inline-immediate result: for example, `mov r2,#640` occurs at `0x37d5e804` inside setClientProperties, and `add r7,sp,#320` at `0x37caca78` inside registerScreens. Those hits can be unrelated offsets/constants and do not establish a clamp. Please share the scanner and exact scope so we can compare the discrepancy.

The existing ui-app-data-resource module already contains `INTERNET_0008SkinLogic.qml` and `INTERNET_6003SkinLogic.qml`: both use FullscreenContentScreen and CarPlayApi mirroring dimensions in their masks. That gives us an immediate QML/API path to review alongside the shared parent. Pixel-universe/style resources and full video behaviour still need separate review.

For both cars, we still need the physical panel identity, active mode, logical ScreenInfo class and effective calibration. The archive confirms the WHD/HD9 distinction, but neither “2020” nor “10-inch” identifies either car's panel. I suggest collaborating on exact metadata variants/verification first, a separate bounded CarPlay issue for API/QML geometry, and identified bench evidence for maintenance access. Commands, hashes, explicit substitutes and JSON results are in [the independent review](INDEPENDENT_REVIEW_2026-11-03.md) and its dated validation directory. No firmware, private vehicle data, keys or certificates are included.
