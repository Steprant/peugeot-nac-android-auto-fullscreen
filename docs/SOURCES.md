# Sources and evidence

Public references retained from the 30 October 2026 investigation. Binary findings are tied to the exact hashes in the repository, not to unobserved live hardware.

## Initial investigation

- [1] [WebPortal v1 Infotainment System e schema WHD](https://developer.groupe-psa.io/webportal/v1/overview/infotainment-system/) — Stellantis.
- [2] [Desktop Head Unit sezione Video configuration](https://developer.android.com/training/cars/testing/dhu#video-configuration) — Google.
- [3] [arduino psa diag codice e protocollo UDS](https://github.com/ludwig-v/arduino-psa-diag/tree/c1409e60798f66bb63149505826170b5eb3c163f) — Ludwig V.
- [4] [Configurazioni e calibrazioni NAC RCC CIROCCO](https://github.com/ludwig-v/arduino-psa-nac_rcc_cirocco/tree/d21cc90b425f1464941f6343ec4a8e74b96ec5cd) — Ludwig V.
- [5] [Reverse engineering firmware schema nac json e chiavi](https://github.com/ludwig-v/psa-nac-firmware-reverse-engineering/tree/4ce14d0ff528cf4127dcf141463c3a946d6c8997) — Ludwig V.
- [6] [Risposta del 24 ottobre 2021 post 2765 sul fullscreen della 2008 GT](https://www.forum-peugeot.com/Forum/threads/tuto-t%C3%A9l%C3%A9codage-et-calibration-dun-nac-rcc-cirocco-cmb_num-sans-diagbox-via-arduino.121767/page-93) — VLud.
- [7] [Esperimento personale e208 del 25 e 26 dicembre 2024](https://forums.automobile-propre.com/topic/mise-%C3%A0-jour-personnalis%C3%A9e-e208-64864/) — Thomas03.
- [8] [FAQ ufficiale sul supporto alla proiezione fullscreen](https://www.aawireless.io/en/support/topics-faq-aawireless/product-info) — AAWireless.
- [9] [HDV NAC12 e HDA NAC12 manuale 8 ottobre 2026 pagine 6 e 7](https://www.navlinkz.de/artikel/HDA-NAC12/ins_eng_HDA-NAC12.pdf) — NavLinkz.
- [10] [Sorgente del configuratore ParamsForm cs e MainForm cs](https://github.com/dragouf/PSA-Arduino-NAC-RCC/tree/fbca1d80d3b7d764dec9d965a99b538202c2a3c5) — dragouf.
- [11] [Pacchetto firmware pubblico analizzato fonte D1](https://ds4emloty3shq.cloudfront.net/CONTINENTAL/NAC_EU/ovip-int-firmware-version/PSA_ovip-int-firmware-version_44-07-33-32_NAC-r0_NAC_EUR_WAVE4.tar) — Continental e PSA.
- [12] [Pagina ufficiale dei componenti a sorgente aperto dei sistemi infotainment](https://www.peugeot.com/en/oss-source-codes.html) — Peugeot.
- [13] [UBI Reader strumento di estrazione utilizzato versione 0 8 16](https://github.com/onekey-sec/ubi_reader) — ONEKEY.
- [14] [Ricognizione hardware NAC Wave 3 e Wave 4 del 2025](https://www.forum-peugeot.com/Forum/threads/diff%C3%A9rences-nac-wave-3-vs-wave-4.140505/) — Marcheur45.
- [15] [Tutorial ufficiale della API di emulazione](https://www.unicorn-engine.org/docs/tutorial.html) — Unicorn Engine.
- [16] [Sorgenti Qt Base v5.5.0 per QRC QString QMap e QList](https://github.com/qt/qtbase/tree/v5.5.0/src/corelib) — Qt Project.
- [17] [Specifica primaria wl_touch: coordinate locali alla superficie e valori fixed](https://wayland.freedesktop.org/docs/html/apa.html#protocol-spec-wl_touch) — Wayland Project.

## Installation and boot investigation

- [V4-1] [Linux v3.10 decompress_unlzo.c](https://github.com/torvalds/linux/blob/v3.10/lib/decompress_unlzo.c). Lzop header and block format; not exact Stellantis kernel source.
- [V4-2] [OpenSSL 1.0.2k CMS header](https://github.com/openssl/openssl/blob/OpenSSL_1_0_2k/crypto/cms/cms.h). CMS flag definitions corresponding to target version literal.
- [V4-3] [Peugeot OSS sources](https://www.peugeot.com/en/oss-source-codes.html). Lists Wave 4 42.x bundles; exact 44.07.33.32 source not located there.
- [V4-4] [PSA NAC firmware reverse engineering](https://github.com/ludwig-v/psa-nac-firmware-reverse-engineering/tree/4ce14d0ff528cf4127dcf141463c3a946d6c8997). Public decryption and extraction tools; does not establish custom installation.
- [V4-5] [NAC hardware comparison](https://www.forum-peugeot.com/Forum/threads/diff%C3%A9rences-nac-wave-3-vs-wave-4.140505/). Original hardware discussion, not a validated UART pinout.
- [V4-6] [Thomas03 e208 customization attempt](https://forums.automobile-propre.com/topic/mise-%C3%A0-jour-personnalis%C3%A9e-e208-64864/). Original incomplete installation attempt; no working patched package.
- [V4-7] [Official firmware archive analyzed](https://ds4emloty3shq.cloudfront.net/CONTINENTAL/NAC_EU/ovip-int-firmware-version/PSA_ovip-int-firmware-version_44-07-33-32_NAC-r0_NAC_EUR_WAVE4.tar). Binary archive source; matching hashes do not attest full CMS authenticity.

## Derived evidence

`patch_fullscreen_plan.json` and `sviluppo_integrato_v3.json` describe the candidate. `integrita_moduli.json` identifies decoded modules. `installazione_v4/firmware_pins.json`, `esito_audit_accesso.json`, `esito_firma_arm.json`, `hashlist_kernels.json` and `evidenze_installazione_v4.json` describe the later checks.

Forum reports are attributed observations, not independent vehicle validation. OpenSSL upstream flag definitions and Linux decompression source explain the relevant formats; they are not a complete source attestation of the vendor build.
