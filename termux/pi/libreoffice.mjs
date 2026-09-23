// SPDX-License-Identifier: AGPL-3.0-only
// Agent-facing operations share the packaged wrapper used by Zotero's UI.
import { access } from 'node:fs/promises';
import { constants } from 'node:fs';
import { spawn } from 'node:child_process';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

async function exists(path, mode = constants.R_OK) {
  try { await access(path, mode); return true; } catch { return false; }
}

function run(file, args, signal) {
  return new Promise((resolve, reject) => {
    const child = spawn(file, args, {
      signal, env: { ...process.env, LC_ALL: 'C' },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stdout = '', stderr = '';
    child.stdout.setEncoding('utf8').on('data', data => { stdout += data; });
    child.stderr.setEncoding('utf8').on('data', data => { stderr += data; });
    child.on('error', reject);
    child.on('close', (code, signal) => resolve({ code, signal, stdout, stderr }));
  });
}

export async function libreOffice(action, { signal } = {}) {
  if (!['status', 'install'].includes(action)) throw new Error('Expected status or install');
  const prefix = process.env.PREFIX;
  if (!prefix || !prefix.startsWith('/') || process.getuid?.() === 0) {
    return { ok: false, error: 'Run as the normal Termux application user with PREFIX set.' };
  }
  const wrapper = join(prefix, 'lib/zotero/libreoffice-unopkg');
  const unopkg = join(prefix, 'bin/unopkg');
  const extension = join(prefix, 'lib/zotero/integration/libreoffice/Zotero_LibreOffice_Integration.oxt');
  const requirements = [
    [wrapper, 'zotero >= 10.0.3-2', constants.X_OK],
    [join(prefix, 'lib/zotero/libreoffice-pipe-compat.so'), 'zotero >= 10.0.3-2'],
    [extension, 'zotero >= 10.0.3-2'],
    [unopkg, 'libreoffice', constants.X_OK],
    [join(prefix, 'lib/jvm/java-21-openjdk/bin/java'), 'openjdk-21', constants.X_OK],
    [join(prefix, 'lib/jvm/java-21-openjdk/lib/libawt_xawt.so'), 'openjdk-21-x'],
    [join(prefix, 'bin/pgrep'), 'procps', constants.X_OK],
  ];
  const missing = [];
  for (const [path, pkg, mode] of requirements) {
    if (!await exists(path, mode)) missing.push({ path, package: pkg });
  }
  if (missing.length) return { ok: false, action, missing };
  const running = await run(join(prefix, 'bin/pgrep'), ['-x', 'soffice.bin'], signal);
  if (![0, 1].includes(running.code)) {
    return { ok: false, action, error: 'Could not check whether LibreOffice is running.', process: running };
  }
  const libreOfficeRunning = running.code === 0;
  if (libreOfficeRunning) {
    return {
      ok: action === 'status', action, prerequisitesReady: true, libreOfficeRunning,
      registration: null,
      message: 'Save documents and close LibreOffice before checking registration or installing. No processes were stopped.',
    };
  }
  if (action === 'install') {
    const install = await run(wrapper, [unopkg, 'add', '--force', extension], signal);
    if (install.code !== 0) return { ok: false, action, libreOfficeRunning, install };
  }
  const listing = await run(wrapper, [unopkg, 'list', 'org.Zotero.integration.openoffice'], signal);
  const listed = listing.code === 0 && listing.stdout.includes('org.Zotero.integration.openoffice');
  const enabled = listed && /is registered:\s*yes/i.test(listing.stdout);
  return {
    ok: action === 'status' ? [0, 1].includes(listing.code) : enabled,
    action, prerequisitesReady: true, libreOfficeRunning,
    registration: { listed, enabled, ...listing },
    message: enabled
      ? 'Extension registered. Start LibreOffice normally. Verify a citation operation in Writer; registration alone is not a functional document test.'
      : 'Extension is not confirmed registered. Inspect the installer output before retrying.',
  };
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    const result = await libreOffice(process.argv[2] || 'status');
    process.stdout.write(JSON.stringify(result, null, 2) + '\n');
    if (!result.ok) process.exitCode = 1;
  } catch (error) {
    process.stdout.write(JSON.stringify({ ok: false, error: error.message }) + '\n');
    process.exitCode = 1;
  }
}
