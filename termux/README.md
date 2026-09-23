# Zotero for native Termux

Unofficial, aarch64-only packaging of Zotero 10.0.3 for Android's **Bionic libc**.
This GitHub fork retains Zotero’s complete upstream source and history. The
`termux/` directory contains normal Termux `build.sh` recipes and patches. It uses
the official `termux/termux-packages` framework, Android NDK toolchain, dependency
handling, prefix substitution, ELF cleanup, and Debian packaging.

**Port status: build and runtime validation in progress.** A green artifact build
alone is not a claim that every desktop integration works on Android.

## Packages

* `zotero-gecko`: Firefox ESR 140.15.0 compiled for Bionic using Termux's Firefox
  140 port. This is a build dependency, isolated from an installed Firefox.
* `zotero`: the upstream Zotero application, including its UI, reader, editor,
  translators, styles, icons, licenses, and integrations. The upstream `npm run
  build`, `prepare_build`, `fetch_xulrunner`/`modify_omni`, and `app/build.sh`
  perform application assembly. The recipe builds the pinned upstream release tag
  from this fork and applies the Termux patches during packaging.

The requested behavior change is one preference:

```js
pref("extensions.zotero.httpServer.localAPI.enabled", true);
```

This enables Settings → Advanced → “Allow other applications on this computer
to communicate with Zotero” by default. It remains a normal preference, so users
can turn it off. Zotero's existing localhost binding, request validation, and
API behavior are retained. It does not expose arbitrary remote JavaScript
execution. Bashkitten agents in Termux can use the ordinary local API at
`http://127.0.0.1:23119/api/` while Zotero is running.

Zotero 10 keeps its normal authorization for writes: an application calls
`POST /api/local/authorize` with its `appName`, the user allows it in Zotero,
and the application uses the returned local key and `Zotero-Server-ID` header.
Enabling the checkbox does not bypass this upstream authorization dialog.

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
Gecko package and checksums as release assets.

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

Once a validated package is available, in aarch64 Termux:

```sh
pkg install x11-repo
pkg update
apt install ./zotero_10.0.3_aarch64.deb
```

Start a Termux:X11 session (the Android Termux:X11 APK is also required):

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

`python termux/scripts/smoke-local-api.py` (from the repository root) checks real library reads and verifies that
unauthorized writes remain rejected. `--expect-disabled` checks the user's
ability to disable the API through the existing preference.

Android applications share the device's loopback network. The default enables
the same local-app access as Zotero's own settings checkbox.

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
