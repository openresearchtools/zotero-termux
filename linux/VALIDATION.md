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

### Initial source build and corrected test fixture

Source revision `f26ffb2d0af02f11736099ac84f5e3e849a9fd04`:

- [amd64 run](https://github.com/openresearchtools/zotero-linux-build-amd64/actions/runs/38161321349)
- [arm64 run](https://github.com/openresearchtools/zotero-linux-build-arm64/actions/runs/38161323120)

Both application source builds, package/ABI/dependency/checksum checks and APT
installation without recommendations passed. The fresh Zotero API checks passed
on amd64. The final LibreOffice registration fixture failed: it passed
`--env:UserInstallation` rather than LibreOffice's `-env:UserInstallation`, so
the intended private profile was not selected and a default-profile lock blocked
registration. This is not a LibreOffice integration pass. The corrected fixture
also selects APT's `/usr/bin/java`, rather than a runner-provided Java on PATH,
and explicitly isolates the Zotero data directory. Repaired runs are pending.
