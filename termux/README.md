# Zotero for native Termux

Unofficial, aarch64-only packaging of Zotero 10.0.3 for Android's **Bionic libc**.
This GitHub fork retains Zotero’s complete upstream source and history. The
`termux/` directory contains normal Termux `build.sh` recipes and patches. It uses
the official `termux/termux-packages` framework, Android NDK toolchain, dependency
handling, prefix substitution, ELF cleanup, and Debian packaging.

**Validated on aarch64 Android in native Termux with Termux:X11.** The library UI,
PDF reader, import/export, bibliography generation, unattended local API writes,
and LibreOffice citations have passed runtime checks. See [VALIDATION.md](VALIDATION.md) for build
links, cache evidence, test scope, and remaining desktop integration limitations.

## Packages

* `zotero-gecko`: Firefox ESR 140.15.0 compiled for Bionic using Termux's Firefox
  140 port. This is a build dependency, isolated from an installed Firefox.
* `zotero`: the upstream Zotero application, including its UI, reader, editor,
  translators, styles, icons, licenses, and integrations. The upstream `npm run
  build`, `prepare_build`, `fetch_xulrunner`/`modify_omni`, and `app/build.sh`
  perform application assembly. The recipe builds the pinned upstream release tag
  from this fork and applies the Termux patches during packaging.

As in upstream Zotero, Gecko is a separate build input that is bundled into the
finished application. Installing `zotero` includes its native Bionic runtime;
users do not need to install `zotero-gecko` separately. The preserved Gecko
artifact is for reusing that build input during later application builds.

The Termux build enables two preferences:

```js
pref("extensions.zotero.httpServer.localAPI.enabled", true);
pref("extensions.zotero.httpServer.localAPI.autoAuthorize", true);
```

This enables Settings → Advanced → “Allow other applications on this computer
to communicate with Zotero” by default. It remains a normal preference, so users
can turn it off. Zotero's existing localhost binding, request validation, and
API behavior are retained. It does not expose arbitrary remote JavaScript
execution. Bashkitten agents in Termux can use the ordinary local API at
`http://127.0.0.1:23119/api/` while Zotero is running.

Any application that can reach the localhost API can obtain a remembered write
key **without an approval dialog**. There is no distinction between agents and
other localhost callers. A client calls `POST /api/local/authorize` with its
`appName` and `Zotero-Server-ID`, then uses the returned `Zotero-API-Key` and
server ID for writes. Cache the key: the upstream limit of five authorization
requests per minute is retained. Writes without a key remain rejected.

Set `extensions.zotero.httpServer.localAPI.autoAuthorize` to `false` in Settings
→ Advanced → Config Editor to restore the upstream approval dialog for new
authorizations. Existing remembered keys remain valid until revoked using
Zotero's authorization controls. Disabling the local API checkbox disables
local API access altogether.

Other patches are platform adaptations: Bionic library names, Termux paths, the
launcher, and supplying a source-built runtime to Zotero's build. Package policy
disables desktop self-updates because those contain glibc binaries; update this
port through the package manager. Gecko uses Termux's GTK/X11 port configuration.

## Build like a Termux package

On an x86_64 Linux host with Docker:

```sh
git clone --branch main https://github.com/openresearchtools/zotero-termux
cd zotero-termux/termux
./scripts/prepare-builder.sh
cp scripts/ci-build.sh termux-packages/zotero-ci-build.sh
source upstream.lock
export TERMUX_BUILDER_IMAGE_NAME
cd termux-packages
./scripts/run-docker.sh bash ./zotero-ci-build.sh
```

Only `-a aarch64` is supported. Outputs are in `termux/termux-packages/output/` from the repository root.
GitHub Actions uses the same commands. Allow several hours and substantial disk
space for the full Gecko build. The host architecture does not change the
package ABI: executables are checked for AArch64 and `/system/bin/linker64`.

The check also scans nested application archives. The stock LibreOffice `.oxt`
installer retains its exact upstream multi-platform JNA jar, including desktop
glibc and other OS binaries. Those resources belong to an external LibreOffice
JVM; Zotero does not load them. The pinned integration uses JNA's native bridge
for Windows window activation. This explicitly hash-checked installer resource
is separate from Zotero's native Bionic runtime. The Java-based LibreOffice
plugin has also passed native Android citation and document-transfer tests;
see the installation instructions below for a Termux registration workaround.

To use an existing official framework checkout, copy `packages/zotero*` to its
`x11-packages/` directory, then build `zotero-gecko` followed by `zotero`.
The framework revision tested here and all upstream versions are in `upstream.lock`.

## Reusing long Gecko builds

Like Bashkitten’s Mozilla builds, CI enables Mozilla `sccache` with its GitHub
Actions backend for both C/C++ and Rust. Compiler results are stored as they
finish, so a later failure does not discard the successful compilations. The
builder uses stable paths, forwards the cache environment into its container,
and prints compiler-cache statistics on success or failure. Host Python is also
saved after failed Gecko builds once its installation is complete.

The finished runtime has a separate cache and **`zotero-gecko-aarch64` artifact**.
Its manifest fingerprints the Gecko recipe, patches, configuration, Termux
framework, and builder image independently of Zotero application changes. The
manifest, package metadata, and SHA-256 checksums are verified before reuse.
The artifact is uploaded before Zotero assembly, retained for 90 days, and can
be reused after a later app build fails or the Actions cache is evicted:

```sh
gh workflow run termux-build.yml --ref main -f gecko_run=RUN_ID
```

Select a run containing the standalone artifact; reuse fails if the current
Gecko inputs differ. Normal runs restore the matching completed component
automatically and skip Gecko compilation. A validated release also retains its
Gecko package, manifest, and checksums in `zotero-gecko-aarch64.tar.gz`. Reuse
that permanent release asset after an Actions artifact expires:

```sh
gh workflow run termux-build.yml --ref main -f gecko_release=termux-10.0.3-r1
```

Choose either `gecko_run` or `gecko_release`. Both paths verify the component
against the current Gecko inputs before restoring it. Release maintainers bundle
the verified component with:

```sh
python3 termux/scripts/gecko-component.py bundle gecko-component zotero-gecko-aarch64.tar.gz
```

To unpack a downloaded release component locally:

```sh
python3 termux/scripts/gecko-component.py unpack zotero-gecko-aarch64.tar.gz gecko-component
```

## One stable branch and recorded upgrades

**`main` is the only branch in this fork.** Its starting point is the official
Zotero **10.0.3** release tag at commit
`80bc5565e000c3f24c37e0020713a41ec9f42e09`. The permanent starting-point record
and subsequent version history are in [UPSTREAM_HISTORY.md](UPSTREAM_HISTORY.md).
`upstream.lock` records the version and commit currently being packaged.

The root source files, submodule definitions, `COPYING`, and upstream README
remain unchanged from the recorded release. CI fetches that release tag from
`zotero/zotero`, checks its exact commit, and rejects source differences outside
`termux/`, the added AGPLv3 `LICENSE`, and our separately named workflow. The
recipe builds the same release tag and applies the Termux patches during
packaging.

Future stable releases, including later 10.x and 11.x versions, are merged into
this same `main` history. Fetch upstream release tags, merge the selected stable
tag, update `upstream.lock` and the recipe’s version/commit checks, and update
Gecko when required. Review the patches and append the version and exact
upstream commit to `UPSTREAM_HISTORY.md` in a commit such as
`Update Zotero stable base to 10.x.y`.

Build and validate the aarch64 package, UI, and local API before publishing a
versioned Termux release. Release tags use the form
`termux-<Zotero version>-r<package revision>`, keeping them distinct from the
upstream release tags. Do not merge upstream development `main` or reset this
fork to upstream: the stable release history and downstream additions grow
together on our single branch.

Upstream `.github/workflows/ci.yml` is retained unchanged but disabled in this
fork’s Actions settings. Only `.github/workflows/termux-build.yml` builds
packages here. The initial packaging repository and build logs are archived at
https://github.com/openresearchtools/zotero-termux-build-history.

## Prefixes and app names

Recipes use `$TERMUX_PREFIX` and patches use `@TERMUX_PREFIX@`. Configure the app
package name, rootfs, and prefix through the official framework's
`scripts/properties.sh` before building, exactly as for other Termux packages.
The resulting package is built for that prefix; it is not a relocatable Linux
archive. All dependencies must be built for the same app/prefix. Official
prebuilt dependencies (`-I`) are suitable for the standard Termux prefix only.
For a custom app/prefix, use the framework's source dependency builds instead.

## Install and run

Download `zotero_10.0.3-1_aarch64.deb` from the
[Termux 10.0.3-r1 release](https://github.com/openresearchtools/zotero-termux/releases/tag/termux-10.0.3-r1).
In aarch64 Termux, from the download directory:

```sh
pkg install x11-repo
pkg update
pkg install termux-x11-nightly ttf-dejavu
apt install ./zotero_10.0.3-1_aarch64.deb
```

Install the [official Termux:X11 Android APK](https://github.com/termux/termux-x11/releases/tag/nightly)
as well as the Termux package above, then start a session:

```sh
termux-x11 :1 &
DISPLAY=:1 zotero
```

A window manager/desktop such as XFCE is optional and makes desktop dialogs
easier to use. Zotero must keep running for agents to access its local API:

```sh
curl -f -H 'Zotero-API-Version: 3' \
  http://127.0.0.1:23119/api/users/0/items
```

`python termux/scripts/smoke-local-api.py --expect-auto-authorize` (from the
repository root) checks library reads, automatic authorization, two empty
write requests reaching stock payload validation with the same key, and
rejection of writes without a key. It creates one remembered API key and leaves
library items unchanged. `--expect-disabled`
checks the user's ability to disable the API through the existing preference.

Android applications share the device's loopback network. Automatic authorization
therefore applies to other Android apps that can reach the port too.

## LibreOffice citations

Native Termux LibreOffice 26.8.0.3 and OpenJDK 21.0.12 were tested with Zotero's
unchanged bundled LibreOffice Integration 9.0.2. From package revision 2,
installation uses Zotero's normal settings UI. Termux apt automatically installs
Zotero's required `openjdk-21` and `openjdk-21-x` dependencies. Install LibreOffice
if it is not already present:

```sh
pkg update
apt install --no-install-recommends libreoffice
```

Save documents and close LibreOffice. In Zotero, open **Settings → Cite → Word
Processors → Install/Reinstall LibreOffice Add-in** and follow the existing
wizard. Termux's `unopkg` is detected automatically. The wizard checks Termux's
Java packages and can install missing Java components after you select Next.
Start Writer normally afterward:

```sh
DISPLAY=:1 SAL_USE_VCLPLUGIN=gtk3 libreoffice --writer
```

The package includes a compiled compatibility library. It shortens overflowing
internal UNO socket names only in the extension installer's process tree. This
avoids the “couldn't connect to pipe” error caused by Termux's long prefix.
Zotero and normal LibreOffice launches have no additional preload, and neither
LibreOffice's binaries nor the official OXT are modified. No compiler or manual
installation script is needed on the device.

### Pi / Bashkitten

The optional Pi package is maintained in [`pi/`](pi/) and installed with Zotero
at `$PREFIX/share/zotero/pi`. Load that directory through Pi's normal local
package mechanism, for example `pi install "$PREFIX/share/zotero/pi"`, then
reload Pi. Bashkitten can include the same package using its normal Pi package
configuration; this repository does not modify Bashkitten or user settings.

It provides the `zotero-libreoffice` skill and `zotero_libreoffice` tool with
`status` and `install` actions. The agent helper calls the same packaged wrapper
used by Zotero's UI. It reports prerequisites, refuses installation while
LibreOffice is running, and does not install OS packages or close documents.
Without the extension loader, the helper is also callable directly:

```sh
node "$PREFIX/share/zotero/pi/libreoffice.mjs" status
node "$PREFIX/share/zotero/pi/libreoffice.mjs" install
```

Registration is not a complete functional test: use Writer's Zotero toolbar to
verify a live citation. The localhost library API has no plugin-install endpoint.

APA 7th edition citations, bibliography insertion, PDF export, DOCX bookmark
editing after reopening, and a Zotero transfer-document round trip all passed
through the UI. For Word-compatible editable citations, use Bookmarks in
Zotero's Document Preferences or its “Switch to a Different Word Processor”
workflow. Simply saving ReferenceMarks as DOCX loses their active citation
links. [Full test scope and limitations](VALIDATION.md#libreoffice).

## Upstream and licensing

Zotero is an upstream project of the Corporation for Digital Scholarship. This
port is not an official Zotero or Termux release. Names, icons, attribution,
license notices, and upstream application assets remain intact.

* Zotero source: https://github.com/zotero/zotero (AGPL-3.0)
* Build documentation: https://www.zotero.org/support/dev/client_coding/building_the_desktop_app
* Local API: https://www.zotero.org/support/dev/web_api/v3/local_api
* Gecko source: https://archive.mozilla.org/pub/firefox/releases/140.15.0esr/source/
* Termux framework and original patches: https://github.com/termux/termux-packages

Zotero and the packaging additions use the GNU Affero General Public
License, version 3 (`LICENSE`), matching Zotero. The copied Termux patches retain
their upstream licensing (`licenses/termux-packages-LICENSE`). Zotero’s original
copyright and trademark notice is retained in `licenses/zotero-COPYING`.
Zotero, Mozilla, and third-party components keep their respective licenses.
The build records Zotero's exact commit and recursive submodule revisions in
`$PREFIX/share/doc/zotero/`; source URLs, checksums, and all downstream patches
are in this repository.
