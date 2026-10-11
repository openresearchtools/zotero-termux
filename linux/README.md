# Native Linux Zotero packages

The same Zotero fork builds native Debian/Ubuntu **amd64** and **arm64** packages.
`main` contains the updated **10.0.6 release source**, merged at exact upstream
commit `536244c2771f590abab9c09a3c27e615e0b318ff`. The official stable download
and [changelog](https://www.zotero.org/support/changelog) identify 10.0.6,
released on 7 October 2026. Upstream had not published its `10.0.6` Git tag when
checked on 11 October. The recorded source commit has `10.0.6.SOURCE` and the
matching Gecko update; builds never follow its moving `10.0` branch.

These are **application source builds**, not repackaged Zotero downloads. Each
builder checks the source against the pinned upstream commit, applies the two
shared automation patches from `termux/packages/zotero`, runs `npm ci` and
Zotero's own `fetch_xulrunner`, `npm run build`, `prepare_build` and `app/build.sh`.
As in upstream's build, official Mozilla Gecko binaries are a separate input;
`upstream.json` pins ESR 140.17.0, per-architecture URLs and SHA-256 checksums.
The Bionic library/path/launcher patches and Termux LibreOffice socket-shortening
library are **not** applied on Linux. The normal Linux installer, official OXT,
native citation integration, launcher behavior and file associations remain.

## Dependencies and installation

The package is named `zotero` and uses Debian architectures, with a version such
as `10.0.6-0`. It is available through the existing
[Open Research Tools APT repository](https://github.com/openresearchtools/apt)
once both Linux packages are published in a non-prerelease release:

```sh
sudo apt update
sudo apt install zotero
```

APT automatically installs `default-jre`, `libreoffice-java-common`,
`libreoffice-writer` and their own dependencies, plus the GTK/X11, audio,
graphics, secret-storage and font packages declared in `dependencies.json`.
Users do not need to discover or install these prerequisites separately, even
with `--no-install-recommends`. A desktop keyring provider and FFmpeg are
recommended for credential storage and additional media support.

The dependency list was compared with the maintained
[community Debian packaging](https://github.com/retorquere/zotero-pkg/blob/07185f7edc96da36aad9f4f1c98d38e2505abc21/config.yml),
Zotero's [system requirements](https://www.zotero.org/support/system_requirements),
and the native libraries in both official 10.0.6 Linux archives. Every build
scans every shipped ELF's actual `DT_NEEDED` entries, subtracts bundled private
libraries, and refuses an unknown external library. Both native runners install
the resulting DEB using APT without recommendations, check runtime linking,
launch Zotero and register the LibreOffice OXT with system Java. Modern `t64`
and older Debian library names are expressed as APT alternatives.

Save documents and close LibreOffice, then use Zotero **Settings → Cite → Word
Processors → Install/Reinstall LibreOffice Add-in**. Restart Writer and verify
Add/Edit Citation. Registration alone is not a live citation test. Updates
are owned by APT: `DisableAppUpdate` policy is installed and the standalone
self-updater is omitted. User profiles, libraries and documents are not changed
by package installation or upgrades.

## Automation

Local API access and automatic remembered-key authorization have the same
defaults as Termux. Any application able to reach Zotero's localhost API can
request a write key without a dialog. Normal localhost binding, validation,
server identity, authorization-key requirements and rate limiting remain.
Turn off **Allow other applications on this computer to communicate with
Zotero** to disable the API, or set
`extensions.zotero.httpServer.localAPI.autoAuthorize=false` in Config Editor
to restore confirmation for new keys. Existing keys require normal revocation.

Library and attachment changes use the normal local API. Writer citations
remain live through the bundled Zotero LibreOffice plugin and desktop
automation. This package adds no arbitrary-code endpoint or remote protocol.
The optional existing Pi package is included at `/usr/share/zotero/pi`; load
it through Pi's normal package mechanism:

```sh
pi install /usr/share/zotero/pi
```

Its shared `zotero-libreoffice` skill and `zotero_libreoffice` helper use ordinary
Linux `unopkg`; the pipe compatibility helper remains Termux-only. No Pi profile
is modified by installing Zotero. To preserve editable DOCX citations, use
Bookmarks or Zotero's transfer-document workflow; ODT supports ReferenceMarks.

## Build repositories and publication

- [amd64 builder](https://github.com/openresearchtools/zotero-linux-build-amd64)
- [arm64 builder](https://github.com/openresearchtools/zotero-linux-build-arm64)

Each has only an exact-commit-pinned wrapper workflow and its own cache/artifacts.
All source, recipes, dependency policy, patches and licenses live in this fork.
Builds run natively on `ubuntu-24.04` or `ubuntu-24.04-arm`, without emulation.
They upload packages only after their installed smoke checks pass; they do not
publish releases. The source workflow dispatches both builders, verifies their
source SHA, checksums, package dependencies and ABI again, then collects the
packages. The existing `TERMUX` fine-grained token needs access to both new
repositories: **Actions read/write, Contents read, Metadata read**, in addition
to the existing Termux x86_64 builder. No secret is copied into build repositories.

```sh
# Build/collect only:
gh workflow run linux-build.yml --repo openresearchtools/zotero-termux
# Build/collect both, then publish a stable Linux release:
gh workflow run linux-build.yml --repo openresearchtools/zotero-termux -f publish=true
```

Release tags are `linux-<version>-r<revision>` and point to the actual shared
source commit. A release contains both DEBs, SHA256SUMS and per-architecture
source/build manifests. The existing APT catalogue already indexes this fork's
`zotero_*.deb` assets for all supported architectures and refreshes hourly.
Advance the package revision before publishing a changed binary with the same
upstream version. Application builds are not acceptance of the full desktop UI;
keep unresolved runtime/citation tests visible in `VALIDATION.md`.

## Source and licenses

The updated upstream source and full AGPL text are in this repository, with
original attribution retained. Downstream patches and exact recursive submodule
revisions are recorded in the package documentation. The source release tag
provides matching fork source; `.gitmodules` and its Git links pin Zotero's
integration, reader, translator and other dependency sources. The Mozilla
runtime's corresponding source is
https://archive.mozilla.org/pub/firefox/releases/140.17.0esr/source/firefox-140.17.0esr.source.tar.xz
with SHA-256 recorded in `upstream.json`. Zotero/Gecko's offline license pages
and all integration notices remain bundled; original licenses govern each
third-party component. This is an unofficial Zotero package.
