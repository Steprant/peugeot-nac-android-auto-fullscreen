# Checkpoint — 3 November 2026

Work paused at the user's request after an independent offline review. No hardware was connected or modified, and no installable update was produced. Continue from [the review](INDEPENDENT_REVIEW_2026-11-03.md), rather than repeating the old isolated CMS experiment.

## Durable results

- The MediaVersion NULL-content worker path uses the SMIME_read_CMS BIO and flags `0x2000`. The old `0x2040` result is restricted to the external-file branch.
- Host OpenSSL and original ARM OpenSSL/libcrypto under QEMU reproduce the content-digest failure on the exact pinned metadata. No skip of content checking is a solution.
- The original SWL initramfs has a distinct root account policy, but no reachable maintenance login has been established.
- Revision 3 AA candidate bytes, hashes and local restoration remain unchanged. WHD compatibility of the actual 2008 panel is unconfirmed.
- CarPlay delegation reproduces; the zero-immediate claim does not. CarPlay logic QML already exists in the ui-app module and uses mirroring API dimensions.

[Validation records](validation/independent-2026-11-03) preserve newly reproduced firmware-dependent results and the new public tests. [The reply to nickpearce95](REPLY_TO_NICKPEARCE95.md) is a prepared draft, not a posted issue comment.

## Resume with these bounded questions

1. Obtain the exact MediaVersion from the alternate official Majestic archive, compare its hash/signature with CloudFront, and establish a fully verified original baseline. The initial HashList matches, but that MediaVersion comparison is unfinished.
2. Ask for documented entry into the original signed SWL environment on matching identified bench hardware, with no implicit storage writes and recovery established. Empty root password metadata is not an entry method. Do not initiate a car update to explore it.
3. Identify the reference vehicle's NAC board/storage, panel part number, active mode, logical ScreenInfo class and effective HMI calibration. No firmware version or diagonal substitutes for these observations.
4. After access/recovery, demonstrate loading and removing a benign temporary resource. Only then design the real AA/decoder/compositor/touch/priority experiment.
5. Compare the contributor's CarPlay scanner and inspect the API mirroring dimensions. Keep a CarPlay candidate separate from the pinned AA revision until independently validated.

Original firmware inputs, the generated candidate and host emulator were kept outside Git. They may need to be reacquired. The repository contains exact hashes, tools, commands and results needed to reproduce the work; it contains no firmware images, complete libraries/QML, keys or certificates.
