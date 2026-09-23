# Native validation: Zotero 10.0.3-1

Validated on 2026-09-23 in Cuttlefish, Android 17/API 37, aarch64. Zotero ran
inside the actual `com.termux` application sandbox (UID 10122,
`untrusted_app_27`), with Termux:X11 and Openbox. Test data and preference
overrides were kept in an isolated profile. The package targets Android API 24;
older Android versions have not been runtime-tested.

## Source and build evidence

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

## Cache evidence

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

## Runtime checks

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

## ABI scope and limitations

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

## LibreOffice

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

### Registration failure and workaround

The initial Tools → Extensions → Add installation reached a reproducible
`Connector: couldn't connect to pipe` error. LibreOffice's random component
pipe IDs can produce a **114-byte** pathname with Termux's temporary-directory
prefix; Unix socket paths can hold at most 107 bytes plus a terminator. See
[LibreOffice's pipe length check](https://github.com/LibreOffice/core/blob/libreoffice-26.8.0.3/sal/osl/unx/pipe.cxx)
and the [Termux path patch](https://github.com/termux/termux-packages/blob/147df9263fb80af1be00d05bb309e9bdfed5764f/x11-packages/libreoffice/0016-fix-hardcoded-paths-for-termux.patch).
A clean-profile retest confirmed that restarting alone could leave a visible,
apparently enabled extension whose citation buttons did nothing.

`scripts/install-libreoffice-plugin.sh` compiles a small temporary compatibility
library and loads it only for `unopkg add --force` and its child registration
processes. It maps overflowing ASCII UNO pipe IDs to deterministic 128-bit
digests without changing socket permissions or transport. The untouched stock
`.oxt` then registers successfully. The temporary library is removed when the
installer exits. This was tested with the final helper inside the real Termux
application sandbox.

After registration, Writer was restarted without `LD_PRELOAD`; process maps
confirmed no compatibility library was loaded. The native plugin then opened
Zotero's citation UI, and the document tests above ran without a preload.
The workaround affects installation only; no new Zotero/Gecko build is needed.
