# Zotero upstream release history

This fork has one branch, `main`, which advances through stable upstream
releases while retaining the Termux packaging and its Git history.

## Permanent starting point

- Upstream repository: https://github.com/zotero/zotero
- Starting release tag: **10.0.3**
- Starting upstream commit: **`80bc5565e000c3f24c37e0020713a41ec9f42e09`**
- First Termux packaging commit on that base: `5eaa4e215`
- Recorded on: 2026-09-23

Keep this starting-point record when updating the current version.

## Stable version record

| Recorded date | Zotero tag | Exact upstream commit | Gecko ESR | Native validation |
| --- | --- | --- | --- | --- |
| 2026-09-23 | 10.0.3 | `80bc5565e000c3f24c37e0020713a41ec9f42e09` | 140.15.0esr | [10.0.3-2: native UI, LibreOffice installer/citations, Pi helper, Java dependencies; original PDF and API validation](VALIDATION.md) |
| 2026-10-06 | 10.0.5 | `ca61760225d25191d0c65acbfd0c4f12a172d263` | 140.15.0esr | [10.0.5 testing prerelease: both native builds and package checks passed; runtime checks pending](VALIDATION.md#zotero-1005-testing-prerelease). |
| 2026-10-11 | 10.0.6 release source (upstream tag not yet published) | `536244c2771f590abab9c09a3c27e615e0b318ff` | 140.17.0esr | [Linux 10.0.6-1: both source builds, APT dependencies, API and Java/OXT registration passed; live Writer UI and new Termux checks pending](../linux/VALIDATION.md#revision-1--both-native-builders-and-publication-passed). |

The official stable download and changelog identify **10.0.6**, released on
7 October 2026. Upstream's `10.0` release branch at the exact commit above has
`version=10.0.6.SOURCE` and the matching Gecko security update. There was no
upstream `10.0.6` Git tag when checked on 11 October. The immutable fork tag
`zotero-release-source-10.0.6` records this source revision for Termux's Git
downloader; it is explicitly our source pin, not an upstream release tag.
CI fetches and verifies the exact upstream commit, never the branch head.
The full release-source changes are merged into `main`; downstream patches
are still applied separately during each platform's source build.

Append a row for each stable upstream upgrade, including major upgrades.
Update `upstream.lock` and the package recipe pins in the same versioned commit.
Publish stable Termux releases only after their build and runtime checks pass.
Testing prereleases must state which runtime checks remain unverified.

## Package revision 2

Recorded on 2026-09-23, with the same stable upstream commit and Gecko runtime.
Revision 2 adds the Termux LibreOffice UI installer, compiled installation
compatibility helper, optional Pi skill/extension, and required Java package
dependencies. [Build and native validation](VALIDATION.md#zotero-1003-2) record
the exact build commit and released package checksum.
