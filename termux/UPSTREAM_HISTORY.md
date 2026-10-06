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

| 2026-10-06 | 10.0.5 | `ca61760225d25191d0c65acbfd0c4f12a172d263` | 140.15.0esr | ARM64 and x86_64 builds pending; previous runtime validation remains specific to 10.0.3-2. |

Append a row for each stable upstream upgrade, including major upgrades.
Update `upstream.lock` and the package recipe pins in the same versioned commit.
Publish a Termux release tag only after its build and runtime checks pass.

## Package revision 2

Recorded on 2026-09-23, with the same stable upstream commit and Gecko runtime.
Revision 2 adds the Termux LibreOffice UI installer, compiled installation
compatibility helper, optional Pi skill/extension, and required Java package
dependencies. [Build and native validation](VALIDATION.md#zotero-1003-2) record
the exact build commit and released package checksum.
