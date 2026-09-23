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

Cloud sync, browser connectors, Word/LibreOffice integration, printing, audio
speech output, and every desktop feature have not been runtime-tested on
Android. Tests used the standard Termux prefix; custom app prefixes use the
official framework's substitution and require rebuilding all dependencies for
that prefix. This is an unofficial port, not an upstream-supported Android
desktop build.
