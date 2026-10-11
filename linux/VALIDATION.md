# Linux validation record

## 11 October 2026 — initial native Linux source build setup

Upstream source: Zotero 10.0.6 release-source commit
`536244c2771f590abab9c09a3c27e615e0b318ff`; Gecko 140.17.0esr.
The source merge is `0f1f63169`. This record must be updated with actual builder
run links, source revisions and outcomes; a workflow dispatch is not a pass.

Both official Linux 10.0.6 archives were inspected for their external native
library requirements. amd64 and arm64 have the same library set apart from the
architecture-specific glibc loader. The Java/LibreOffice dependencies were
compared with Zotero's documentation and community Debian package sources.

Required builder gates: source pin, automation patches, source application
build, native ABI/library coverage, DEB dependencies and checksums, installation
through APT without recommendations, fresh-profile API checks, system Java and
stock LibreOffice OXT registration. Initial builds and these gates are pending.
Live Writer citation editing, save/reopen and desktop UI acceptance are pending
on both Linux architectures. Historical Termux validation does not establish
Linux acceptance or new 10.0.6 Termux acceptance.
