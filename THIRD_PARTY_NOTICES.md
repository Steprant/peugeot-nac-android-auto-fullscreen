# Third-party material and provenance

The MIT grant covers original contributions to this research project. It does not relicense Stellantis/PSA/Continental firmware, Google Android Auto, Qt, Linux, OpenSSL, or third-party repositories cited by the analysis.

No complete proprietary image, library, QML resource, certificate, firmware decryption key or OEM signing key is included. The version-pinned patch plan includes short original/replacement byte intervals needed to identify and reverse the research transformation. Paths, symbols, hashes and configuration observations identify the analyzed inputs; they do not grant rights to distribute the underlying firmware. Any third-party portions retain their original rights.

No external project is vendored here. Public PSA diagnostic and extraction projects informed the research and are credited in `fonti.json`, `installazione_v4/fonti_v4.json` and `docs/SOURCES.md`. Do not copy their code into this project without preserving and checking its applicable license.

Python dependencies are installed separately and keep their own licenses. The public suite uses pyelftools, Unicorn and lzallright. Optional desktop and assembler experiments additionally use the dependencies in the existing requirements files. The repository's MIT license does not replace those dependency licenses.

Linux decompression format documentation and OpenSSL CMS flag definitions were used to interpret the analyzed binaries. References to their source do not assert that an upstream source tag is the exact source of the vendor's complete build.

Names and trademarks identify the systems studied. This is an independent community research project.
