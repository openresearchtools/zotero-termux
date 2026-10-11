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

### Revision 0 and stricter dependency verification

The repaired source revision `6714251e9c48d5ec1472b21652f77c115c1fcfce`
passed both native builds and all existing gates:

- [amd64](https://github.com/openresearchtools/zotero-linux-build-amd64/actions/runs/38161580016)
- [arm64](https://github.com/openresearchtools/zotero-linux-build-arm64/actions/runs/38161579290)
- [collection and publication](https://github.com/openresearchtools/zotero-termux/actions/runs/38161566508)

The source-built `10.0.6-0` packages were published in `linux-10.0.6-r0`.
Both API checks and normal-socket OXT registration passed. Log review showed
that `/usr/bin/java` still selected the runner's preinstalled Temurin 17,
despite APT installing `default-jre`. Thus that run does not establish OXT
registration with the Java runtime supplied by our declared APT dependency.
Revision 1 resolves `default-jre-headless`'s actual OpenJDK package through
dpkg, then uses that package's Java executable/home explicitly for verification.
The test change does not alter the application or plugin. Revision 1 builds
and the stricter installed-Java checks are pending.

### Revision 1 — both native builders and publication passed

Actual candidate/source: `ec3a5463f8212411b46bec16d5065a013adf39e4`.
Packages: `zotero_10.0.6-1_amd64.deb` and `zotero_10.0.6-1_arm64.deb`.

- [amd64 native build and installed checks](https://github.com/openresearchtools/zotero-linux-build-amd64/actions/runs/38162029851): **passed**.
- [arm64 native build and installed checks](https://github.com/openresearchtools/zotero-linux-build-arm64/actions/runs/38162029640): **passed**.
- [source collection, re-verification and publication](https://github.com/openresearchtools/zotero-termux/actions/runs/38162016520): **passed**.
- [Stable Linux release](https://github.com/openresearchtools/zotero-termux/releases/tag/linux-10.0.6-r1).

Both runners built the application from the updated source with only the two
automation patches, verified the Linux ABI and complete external-library
mapping, installed the DEB and mandatory dependencies via APT without
recommendations, checked runtime linking, then launched fresh Zotero profiles
and libraries. API reads, unattended remembered-key authorization, key reuse
and rejection of unauthenticated writes passed. Both OXTs registered successfully
using **OpenJDK 21.0.12.1 supplied by default-jre's actual APT dependency**, with
ordinary Linux `unopkg`, private LibreOffice profiles and standard sockets.
The package validation also checks the APT update policy and omitted updater;
the update UI itself was not exercised. No Termux socket library is shipped.

Published SHA-256:

```text
8884595ff51a16e087bb97e4198dacaba4c3ef9005aaa256508e0e92c079354f  zotero_10.0.6-1_amd64.deb
d74f51a6de8093b48c9fed7f9f8edd6ea9b1adb81db4ee8cf58db37bb7257a97  zotero_10.0.6-1_arm64.deb
```

The existing Termux x86_64 builder was updated to the shared verifier that
supports the merged 10.0.6 release source and Linux packaging paths. No 10.0.6
Termux candidate or runtime pass is claimed. Live Writer Add/Edit Citation,
save/reopen, DOCX transfer and full desktop UI checks remain pending on both
Linux architectures; source/API/OXT checks do not replace that acceptance.

### APT catalogue delivery

[APT publication run 38162290643](https://github.com/openresearchtools/apt/actions/runs/38162290643)
completed successfully. The downloaded stable `Packages` index contains both
`zotero 10.0.6-1` architectures, points to the matching `linux-10.0.6-r1` release
assets, and records the exact SHA-256 hashes above and declared dependencies.
`gpgv` verified the `InRelease` signature against the existing public archive
key; the downloaded `Packages` digest and size also match that signed metadata.
No new archive key, separate APT source or user token setup is required.
