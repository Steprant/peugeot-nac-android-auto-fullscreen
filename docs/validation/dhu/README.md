# Android Auto display geometry in the Desktop Head Unit

The `44.07.33.32_NAC-r0` archive gives the WHD layout a 1920 × 720 canvas and a central 1280 × 720 Android Auto rectangle beginning at x = 320. The HD9 rectangle begins at x = 0 and occupies its full 1280 × 720 canvas. The Peugeot 2008 brochure confirms the 10-inch HD option. The exact display part number and active mode of the reference 2008 GT still need direct evidence. [Archive findings](../../TECHNICAL_FINDINGS.md) · [Independent review](https://github.com/Steprant/peugeot-nac-android-auto-fullscreen/issues/2) · [Peugeot 2008 brochure](https://www.peugeot.fr/content/dam/peugeot/france/b2c/documentation/brochures/2008_FR_Cat_Decembre_2020.pdf)

| DHU configuration | Video frame | Crop at top and bottom per edge | Visible area | Purpose |
| --- | --- | --- | --- | --- |
| [central-720p.ini](central-720p.ini) | 1280 × 720 | 0 px | 1280 × 720 | Approximate the current central window |
| [whd-1080p.ini](whd-1080p.ini) | 1920 × 1080 | 180 px | 1920 × 720 | Test the proposed WHD video geometry |
| [wide-720p.ini](wide-720p.ini) | 1280 × 720 | 120 px | 1280 × 480 | Test the same 8:3 aspect ratio at a smaller frame size |

The 720p wide profile would require uniform 1.5× scaling to fill the 1920 × 720 canvas. Whether the NAC can use that profile and scale both axes uniformly remains open. The frame sizes and total margins follow Google's documented DHU options. The current NAC USB video mode remains unmeasured. [Google DHU video configuration](https://developer.android.com/training/cars/testing/dhu#video-configuration)

## Phone and desktop check

Install and connect the DHU using Google's instructions. Start one fresh session per file with the same Android Auto version, phone and connection method. From the DHU installation directory on Linux or macOS, point `--config` at the absolute path to the profile. Google also documents the Windows executable. [Google DHU setup and options](https://developer.android.com/training/cars/testing/dhu#run-dhu)

```sh
./desktop-head-unit --config=/absolute/path/to/whd-1080p.ini
```

Capture the Android Auto launcher and navigation view. Check whether navigation and the taskbar remain legible, whether controls near both side edges respond, and whether the UI fills the visible window without stretching. Record the phone model, Android Auto and DHU versions, profile, connection type and observed viewport. Omit locations, account details and device identifiers from shared captures.

The INI syntax and viewport arithmetic have been checked offline. A phone-to-DHU session is pending. A successful DHU comparison would establish what the phone renders in Google's emulator. NAC video decoding, composition and touch still require the original hardware.

## Evidence needed from a matching unit

Record the display and NAC part numbers, the hardware revision and the active display mode from an original label or supported read-only diagnostic output. Keep serial numbers and VINs private. Identify whether each observation comes from the reference 2008 GT, a donor bench unit or a related model.

On the matched bench, capture the factory baseline for Android Auto over USB, touch at both edges, audio and microphone, climate controls, reverse-camera and parking-sensor priority, disconnect and reconnect, suspend and restart. An identified stock baseline and a documented reversible deployment route remain prerequisites for evaluating the prototype on a matched bench unit.

## Video interface compatibility

NavLinkz lists the 2008 II NAC in the HDV-NAC12 manual and documents an external HDMI input. It also identifies limits on automatic factory-camera switching and parking graphics. That documentation leaves fullscreen Android Auto, factory touchscreen control of the external source and all native functions on the exact 2020 GT unverified. [NavLinkz manual, pp. 6–7 and 31–32](https://www.navlinkz.de/artikel/HDV-NAC12/ins_eng_HDV-NAC12.pdf)
