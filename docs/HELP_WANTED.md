# Help wanted

We have an offline, version-pinned fullscreen candidate. We do not have a demonstrated way to load it on a matching NAC. The useful next contributions are bounded experiments with reproducible evidence.

## 1 Reversible access on matching hardware

Can a documented maintenance path or one-session boot argument control be established on the exact Wave 4 board/bootloader, without persistent modification? The original initramfs reads init=; that fact does not give control of the bootloader. Start with hardware identity and a passive boot log, including storage family, console routing and available HAB observations. No UART pin assignment or voltage has been verified by this project.

Provide board/bootloader identification, method provenance, observations, exact changes if independently authorized, and recovery evidence. Do not upload a whole flash dump, secret or VIN. A failing mount induced by damage is not a useful first experiment.

## 2 Explain the MediaVersion digest discrepancy

Reproduce complete CMS/S/MIME verification of the pinned original MediaVersion.ini, keeping exact input hash, tool version, canonicalization, flags and output. Host OpenSSL 3 reports a content digest failure. Explain any difference with target OpenSSL 1.0.2k or vendor processing. Verifying only signed attributes with content verification disabled is not a resolution or installation proof.

The original metadata is not bundled; its hash is in `installazione_v4/evidenze_installazione_v4.json`. Submit methods and derived results rather than keys or the complete distribution.

## 3 Independent candidate review

Review patch ranges, focus transitions, exact name guards, crop and QML bindings against the pinned files. Check exception/logging consequences, preserved calling convention and what the stubs conceal. New evidence must distinguish partial ARM execution from a complete process or compositor.

## 4 Runtime display and calibration

With independently authorized read access, document the effective `/opt/ui/UIFwkTelecoding/hmi-telecoding.ini`, actual QML/resource paths and relevant SurfaceManager rules. The archive's default geometry does not establish the live calibration. Redact unit identifiers.

## 5 Bench projection and vehicle-function acceptance

After access and recovery exist, separately demonstrate harmless temporary resource loading before trying the fullscreen candidate. Record negotiated video dimensions/margins, decoder output, crop, touch at all edges, focus handoff and priority screens. DHU, desktop Qt and a screenshot are useful partial evidence, not the entire acceptance test.

Climate, camera, parking sensors, audio/microphone, reconnect and suspend/resume must be tested on matching hardware. There is currently no on-car success report in this project.

Open a research issue or a focused PR. Link sources by commit/version and identify exactly what you personally ran. Please do not send speculative instructions to vehicle owners as if they were a verified installer.
