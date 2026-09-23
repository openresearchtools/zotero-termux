# Native validation

## Zotero 10.0.3-2

Validated on 2026-09-23 in the actual Termux app sandbox on Cuttlefish Android
17/API 37, aarch64, using Termux:X11 and Openbox. The upstream stable base is
unchanged: Zotero 10.0.3, commit
`80bc5565e000c3f24c37e0020713a41ec9f42e09`.

### Signed APT repository

The [repository publisher](https://github.com/openresearchtools/apt/actions/runs/35916100330)
passed after adding Zotero to `openresearchtools/apt` at commit
`a239bd86c31f49467b05a770704dec021c5a05e7`. Its hourly refresh tracks stable
`zotero_*_aarch64.deb` release assets. Both revision 1 and revision 2 are indexed;
APT selects **10.0.3-2**.

On the native Termux device, the official Open Research Tools Termux keyring
package installed the signed source definition. `apt-get update` verified the
repository, and `apt-get install --reinstall zotero` downloaded **104,228,812
bytes** from the repository into an empty package cache and installed them.
The downloaded SHA-256 matched the release checksum below. The `InRelease`
signature and its `Packages` checksum were also independently verified.

With Zotero and Java omitted only from a copy of the package status database,
`apt-get --simulate install zotero` selected the repository's 10.0.3-2 package,
`openjdk-21`, `openjdk-21-x`, and Java certificates automatically. The actual
installed packages and user profiles were preserved.

The repository-installed build was then opened through the normal desktop
entry. Zotero's Settings → Cite installer detected LibreOffice and reported
Installation Successful with the normal user profiles. Writer's desktop
launcher opened the real DOI test document; Add/Edit Citation changed the
Miller locator to page 86, and Refresh succeeded. The saved ODT independently
retained both live citation fields, a live bibliography, the DOI metadata, and
APA style. Neither process used a custom profile, Java environment override,
or compatibility preload.

### Final build and package

- [Final GitHub Actions build](https://github.com/openresearchtools/zotero-termux/actions/runs/35897999361):
  passed, source commit `5b1efd84bb502ac34b46863a38e0fa7871bdb06b`.
- Released package: `zotero_10.0.3-2_aarch64.deb`.
- SHA-256: `111e88a2d2ddde693ba8e6dad84dcea8a239bb6b05496b23b2a5f2c39a25675b`.
- Official Termux recipe lint, pinned upstream comparison, packaged UI/license,
  API preferences, installer paths, and Pi package contents: passed.
- All **14 application runtime ELF files**, including the new installation
  helper, passed the AArch64/Bionic audit. The exact upstream portable JNA
  resource exception described below remains unchanged.
- The completed Gecko component was restored and verified. The build log
  reports `Skipping already built dependency zotero-gecko@140.15.0-1`.
  Its fingerprint, package checksum and separately downloadable archive remain
  unchanged from revision 1.

Termux package metadata declares **openjdk-21** and **openjdk-21-x** as required
`Depends`, with LibreOffice optional. A native APT simulation used a copy of the
installed-package status database excluding Zotero and both Java packages.
Installing only the final local Zotero `.deb` selected `openjdk-21`,
`openjdk-21-x`, and `ca-certificates-java` automatically. The real installed
Java packages were not removed for this check. The final package was then
installed successfully through APT in the real Termux app sandbox.

### Normal installation and citation workflow

The tested versions were LibreOffice **26.8.0.3**, OpenJDK **21.0.12**, and the
unchanged bundled Zotero LibreOffice Integration **9.0.2**.

| Check | Result |
| --- | --- |
| Stock Zotero installer | Settings → Cite → Word Processors → Install/Reinstall detects the Termux `unopkg` path and reports Installation Successful |
| Clean extension installation | The UI installer and Pi installer each registered the extension in a separate initially empty LibreOffice profile |
| Default user workflow | Final package UI installation also passed with the existing normal profiles, launched through the installed Zotero desktop entry |
| Ordinary Writer startup | Installed Writer desktop entry works without profile arguments, `JAVA_HOME`, `XDG_CONFIG_HOME`, `SAL_USE_VCLPLUGIN`, or an added `LD_PRELOAD` |
| Real APA citation | Existing Miller and Shannon DOI citations and the bibliography display correctly; Add/Edit Citation opens the existing live field |
| Save and reopen | Citation edits persist as live Zotero ReferenceMarks with the bibliography and APA preference intact |
| Default localhost API | Final package smoke check passed reads, automatic authorization, reusable key, normal empty-payload rejection, and missing-key rejection |

The UI and Pi clean-install checks used temporary profiles to distinguish
fresh registration from an already installed extension. The final acceptance
check used normal desktop launchers and the normal user profiles; no temporary
profile or environment workaround is needed by the user. The saved desktop
workflow document independently retained two live citation fields, both real
DOIs, a live bibliography, APA style, and the edited Miller locator, page 85.

The compatibility library is compiled during packaging and loaded only by the
extension installation process tree. LibreOffice binaries and the stock OXT
remain unchanged. Normal Zotero and Writer processes run without this preload;
no compiler or manual registration script is required on the device.

### Pi integration

The packaged `termux/pi` module was tested with **Pi 0.86.1** from Bashkitten,
using Pi's native package manager, extension loader, skill loader, and actual
`zotero_libreoffice` tool calls. Status detected the missing extension in a
fresh profile; install succeeded; subsequent status reported registration.
Writer then opened and edited a real citation, saved it, and reopened it.
The final installed Pi package also passed status/install/status on the normal
profile. While Writer was running, the tool refused installation and the
packaged wrapper returned exit 75 without closing Writer. Bashkitten's source
and the user's Pi settings were not changed.

Installer source checks also exercised the standard prefix and a custom app
prefix, missing Java, missing X11 Java support, and complete Java detection.
The custom prefix was not separately built or runtime-tested on Android.

The earlier PDF and DOCX conversion checks below used revision 1. Revision 2
retested installation and live ODT citations; the unchanged Gecko engine and
upstream document-conversion logic were reused. Microsoft Word and Google Docs
themselves were not run.

## Original 10.0.3-1 validation

Validated on 2026-09-23 in Cuttlefish, Android 17/API 37, aarch64. Zotero ran
inside the actual `com.termux` application sandbox (UID 10122,
`untrusted_app_27`), with Termux:X11 and Openbox. Test data and preference
overrides were kept in an isolated profile. The package targets Android API 24;
older Android versions have not been runtime-tested.

### Source and build evidence

- Stable upstream: Zotero **10.0.3**, commit
  `80bc5565e000c3f24c37e0020713a41ec9f42e09`.
- Source-built runtime: Firefox ESR **140.15.0**, Termux package revision **1**.
- [Gecko and application build](https://github.com/openresearchtools/zotero-termux/actions/runs/35874262096),
  commit `b3a093750015f094490247afef0dcf6b9498de21`: passed.
- [Final application build with cached Gecko](https://github.com/openresearchtools/zotero-termux/actions/runs/35884041307),
  commit `3c6d9fb23df581c766e6140469423135be135a83`: passed in nine minutes.
  This run produced the released `zotero_10.0.3-1_aarch64.deb`.
- Official Termux recipe lint, stable upstream source comparison, package
  metadata, license, packaged UI, and packaged local API preferences: passed.

The final package SHA-256 is
`ca790c743cd363e5b770d44e3e4c36515dec8aac7b0b799adb3ae7c8d01dc6f8`.
Later validation documentation and smoke-test corrections do not change the
package recipes, source pins, patches, or runtime inputs used by that build.

### Cache evidence

The Gecko build recorded **2,833 compiler-cache hits and 698 misses**: 80.23%
overall, including 521 Rust hits (93.20%). A previous build failure also left
successful compiler outputs reusable by the next run.

The final application run restored the verified completed component and skipped
the Gecko build step. Its Termux dependency log explicitly reports:

```text
Skipping already built dependency zotero-gecko@140.15.0-1
```

Completed component fingerprint:
`5437efd53ac0857625b6cd7cb538a0ce60cfbefc7b04b229cc6e5fc363983dc2`.
Gecko package SHA-256:
`323d1e21d7c3c8bae0fca508a68615566f8a06a0d77730cbd1afff99422b95c1`.

The separate release asset `zotero-gecko-aarch64.tar.gz` contains that package,
its manifest, and checksums. Bundle/unpack round trips preserve the package
bytes. Changed build inputs, altered checksums, traversal paths, and symlink
archive entries are rejected. The release fallback is available after the
90-day Actions artifact retention period.

### Runtime checks

| Check | Result |
| --- | --- |
| Native process | Runs as the Termux app UID; maps Android Bionic `libc.so`, `linker64`, and bundled `libxul.so` |
| Library UI | Opens and displays local items |
| RIS import | Stock import wizard imports the synthetic journal article |
| Export and bibliography | Local API returns correct RIS and formatted CSL bibliography |
| PDF | Attachment indexed; full text returned; stock reader renders the one-page fixture and its text |
| Default local API | Reads succeed without changing the packaged API preference |
| Automatic authorization | `POST /api/local/authorize` returns a remembered key without a dialog |
| Actual writes | Journal item and child note created and read back using the same key |
| Restart | Remembered key and server ID remain valid; another write succeeds |
| Write request validation | Missing/invalid key: 401; wrong server ID: 412; missing server ID: 428 |
| Disable automatic authorization | Setting `localAPI.autoAuthorize=false` restores the stock dialog; one-time Allow works and consumed key reuse returns 401 |
| Disable local API | Stock Advanced checkbox makes API requests return 403; re-enabling restores access |

The PDF reader requires Gecko's Web Speech API to exist during initialization.
The runtime now enables that API; no Zotero reader source changes were needed.
A system speech-dispatcher backend is not included.

Automatic authorization applies to **all localhost callers**, including other
Android applications that can reach the port. An `appName` is a display label,
not verified caller identity. Normal keys, server IDs, loopback/Host checks, and
the upstream authorization rate limit remain in place. Disabling automatic
authorization affects new grants; existing remembered keys must be revoked
through Zotero's authorization controls.

### ABI scope and limitations

All **13 Zotero runtime ELF files** passed the AArch64/Bionic audit: no glibc
dependencies or `GLIBC_*` symbol versions, and Android's linker for executables.
The standalone Gecko component's 15 ELF files were also checked. Application
archives are scanned recursively.

The complete upstream LibreOffice installer is preserved. Its external JVM
resource `external_jars/jna.jar` contains binaries for multiple desktop
platforms, including glibc. Zotero does not load those resources as its runtime.
The audit allows only this exact upstream JAR and SHA-256:
`34ed1e1f27fa896bca50dbc4e99cf3732967cec387a7a0d5e3486c09673fe8c6`.
A modified JAR or an unexpected nested glibc ELF fails validation.

Cloud sync, browser connectors, Microsoft Word integration, printing, audio
speech output, and every desktop feature have not been runtime-tested on
Android. Tests used the standard Termux prefix; custom app prefixes use the
official framework's substitution and require rebuilding all dependencies for
that prefix. This is an unofficial port, not an upstream-supported Android
desktop build.

### LibreOffice

Additional native UI validation on 2026-09-23 used the official Termux
`libreoffice` **26.8.0.3** package, `openjdk-21`/`openjdk-21-x` **21.0.12**, and
Zotero's unchanged bundled LibreOffice Integration **9.0.2**. Writer and its
Java VM ran under the actual Termux UID, using Bionic. No PRoot Linux
distribution or desktop glibc runtime was used.

Zotero's Add Item by Identifier UI fetched these real DOI records into a
collection named **LibreOffice APA validation**:

- Miller, G. A. (1956), *The magical number seven, plus or minus two: Some
  limits on our capacity for processing information.* DOI `10.1037/h0043158`.
- Shannon, C. E. (1948), *A Mathematical Theory of Communication.* DOI
  `10.1002/j.1538-7305.1948.tb01338.x`.

Writer's Zotero toolbar opened the citation dialog and Document Preferences.
APA Style 7th edition generated `(Miller, 1956)` and `(Shannon, 1948)` and a
two-entry bibliography. The following document operations were performed
through the UI, with exported files independently inspected afterward:

| Operation | Result |
| --- | --- |
| Save native ODT | Two live Zotero citation ReferenceMarks, a live bibliography section, DOI metadata, and APA style preference retained |
| Refresh | Native plugin refresh succeeds |
| Export PDF | Both formatted citations and the bibliography remain readable |
| Switch to a Different Word Processor | DOCX contains Zotero's transfer marker, both complete citation payloads, bibliography payload, and document preferences |
| Reopen transfer DOCX and Refresh | Zotero detects the transfer and restores live citations; saving as ODT retains both citation fields and bibliography |
| Bookmarks → DOCX | Reopened formatted DOCX keeps Zotero bookmarks and citation metadata in document properties |
| Edit reopened DOCX citation | Existing Miller citation opens in Zotero; adding page 81 updates it to `(Miller, 1956, p. 81)` and persists in the saved DOCX |

Microsoft Word and Google Docs themselves were **not** run. The transfer was
validated by serialization, reopening, and restoration in LibreOffice. The
[upstream transfer instructions](https://www.zotero.org/support/kb/moving_documents_between_word_processors)
describe how to complete the handoff in those applications. Plain DOCX export
with ReferenceMarks is insufficient; use the transfer workflow or Bookmarks.

#### Registration failure and workaround

The initial Tools → Extensions → Add installation reached a reproducible
`Connector: couldn't connect to pipe` error. LibreOffice's random component
pipe IDs can produce a **114-byte** pathname with Termux's temporary-directory
prefix; Unix socket paths can hold at most 107 bytes plus a terminator. See
[LibreOffice's pipe length check](https://github.com/LibreOffice/core/blob/libreoffice-26.8.0.3/sal/osl/unx/pipe.cxx)
and the [Termux path patch](https://github.com/termux/termux-packages/blob/147df9263fb80af1be00d05bb309e9bdfed5764f/x11-packages/libreoffice/0016-fix-hardcoded-paths-for-termux.patch).
A clean-profile retest confirmed that restarting alone could leave a visible,
apparently enabled extension whose citation buttons did nothing.

The initial prototype compiled a temporary compatibility library and loaded
it only for `unopkg add --force` and its child registration processes. It maps overflowing ASCII UNO pipe IDs to deterministic 128-bit
digests without changing socket permissions or transport. The untouched stock
`.oxt` then registers successfully. The temporary library is removed when the
installer exits. This was tested with the final helper inside the real Termux
application sandbox.

After registration, Writer was restarted without `LD_PRELOAD`; process maps
confirmed no compatibility library was loaded. The native plugin then opened
Zotero's citation UI, and the document tests above ran without a preload.
The workaround affects installation only. Revision 2 packages this library
and uses it through Zotero's normal installer and the optional Pi helper,
superseding the removed compile-on-device script. Gecko remains unchanged.
