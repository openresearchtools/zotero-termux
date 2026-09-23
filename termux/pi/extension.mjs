// SPDX-License-Identifier: AGPL-3.0-only
import { Type } from 'typebox';
import { libreOffice } from './libreoffice.mjs';

export default function zoteroTermux(pi) {
  pi.registerTool({
    name: 'zotero_libreoffice',
    label: 'Zotero LibreOffice',
    description: 'Check native Termux Zotero/LibreOffice prerequisites and extension registration, or install/reinstall Zotero’s bundled LibreOffice extension. Read the zotero-libreoffice skill. Installation requires LibreOffice to be closed; this tool never closes documents or installs OS packages.',
    parameters: Type.Object({ action: Type.Union([Type.Literal('status'), Type.Literal('install')]) }),
    async execute(_id, { action }, signal) {
      const result = await libreOffice(action, { signal });
      return {
        content: [{ type: 'text', text: JSON.stringify(result) }],
        details: result,
        isError: !result.ok,
      };
    },
  });
}
