---
name: zotero-libreoffice
description: Install or repair Zotero's bundled citation extension in native Linux or Termux LibreOffice, check its prerequisites, and verify live citations in Writer. Use for Zotero–LibreOffice setup or citation-plugin installation failures.
---

<!-- SPDX-License-Identifier: AGPL-3.0-only -->

Use `zotero_libreoffice` with `action: "status"` first. The tool reports missing
packages, whether LibreOffice is running, and extension registration. If only
the skill is loaded, run the equivalent helper relative to this skill:

```sh
node ../../libreoffice.mjs status
node ../../libreoffice.mjs install
```

Resolve those paths from this SKILL.md's directory, not the working project.
The helper needs Zotero from this fork. On native Linux, it uses standard
`/usr/bin/unopkg` and the ordinary desktop sockets. Only Termux uses the packaged
installer workaround (Zotero 10.0.3-2 or later), also used by Zotero Settings →
Cite → Word Processors → Install/Reinstall LibreOffice Add-in. No compiler or
repository checkout is needed. LibreOffice and the bundled official OXT remain
unchanged on both platforms.

Linux's APT package requires `default-jre`, `libreoffice-java-common` and
`libreoffice-writer`; APT installs their own dependencies too. Repair partial
installations with `sudo apt --fix-broken install`. Load the optional Pi package
from `/usr/share/zotero/pi`. All application updates come from APT.

On Termux, Zotero declares `openjdk-21` and `openjdk-21-x` as apt dependencies, so a normal
Zotero installation already supplies Java. Install `libreoffice` when setup is
requested and it is missing. If the tool reports missing Java after a partial or
manual installation, repair it with `pkg install openjdk-21 openjdk-21-x`. Use the configured Termux
prefix; desktop Debian/glibc packages do not work here. The tool does not install
these packages itself. Save documents and close LibreOffice before `install`;
do not kill Writer or discard unsaved work. A failed call is not success; inspect
its error and correct the cause before retrying.

After installation, start Writer normally on the active X11 display and test
Zotero Add/Edit Citation. A visible toolbar or an enabled extension entry alone
does not prove Java registration or communication works. Zotero must be running
for citation operations. Use the session's desktop controls; BashKitten's browser
tab tool does not control Writer. If no desktop is available, use a separately
owned Xvfb display and stop it when finished, preserving existing sessions.

For a citation test, import a real DOI into Zotero, select the requested style,
insert a citation and bibliography, save, reopen, and verify the citation remains
editable. Preserve the user's library and documents. ODT supports live ReferenceMarks;
for editable DOCX use Bookmarks or Zotero's “Switch to a Different Word Processor”
workflow. Saving ReferenceMarks directly as DOCX does not preserve live citations.
Zotero's localhost library API does not expose extension installation or Writer
document editing. Report which document applications were actually tested.
