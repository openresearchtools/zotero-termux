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
| 2026-09-23 | 10.0.3 | `80bc5565e000c3f24c37e0020713a41ec9f42e09` | 140.15.0esr | Build and runtime validation in progress |

Append a row for each stable upstream upgrade, including major upgrades.
Update `upstream.lock` and the package recipe pins in the same versioned commit.
Publish a Termux release tag only after its build and runtime checks pass.
