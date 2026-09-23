#!/usr/bin/env python3
"""Fingerprint, preserve, and verify the independently reusable native Gecko build."""
import hashlib
import json
import pathlib
import re
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PREFIX = '/data/data/com.termux/files/usr'


def sha256(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()


def fingerprint():
    pins = dict(line.split('=', 1) for line in (ROOT / 'upstream.lock').read_text().splitlines()
                if line and not line.startswith('#'))
    # App versions and app-only patches do not invalidate an identical runtime.
    inputs = {key: pins[key] for key in (
        'TERMUX_PACKAGES_COMMIT', 'TERMUX_BUILDER_IMAGE_NAME',
        'TERMUX_FIREFOX_PATCH_COMMIT', 'GECKO_VERSION')}
    inputs.update(format=1, architecture='aarch64', prefix=PREFIX)
    inputs['recipe_files'] = {
        str(path.relative_to(ROOT)): sha256(path)
        for path in sorted((ROOT / 'packages/zotero-gecko').rglob('*')) if path.is_file()
    }
    return hashlib.sha256(json.dumps(inputs, sort_keys=True).encode()).hexdigest()


def metadata(package):
    def field(name):
        return subprocess.check_output(['dpkg-deb', '-f', str(package), name], text=True).strip()
    assert field('Package') == 'zotero-gecko', 'Not a Zotero Gecko package'
    assert field('Architecture') == 'aarch64', 'Wrong component architecture'
    recipe = (ROOT / 'packages/zotero-gecko/build.sh').read_text()
    version = re.search(r'^TERMUX_PKG_VERSION="?([^"\n]+)', recipe, re.M).group(1)
    revision = re.search(r'^TERMUX_PKG_REVISION=(\d+)', recipe, re.M)
    expected = version + ('-' + revision.group(1) if revision and revision.group(1) != '0' else '')
    assert field('Version') == expected, 'Wrong component version'
    return expected


def one_package(directory):
    packages = list(directory.glob('zotero-gecko_*_aarch64.deb'))
    assert len(packages) == 1, f'Expected one Gecko package in {directory}'
    return packages[0]


def record(output):
    source = one_package(output)
    version = metadata(source)
    dest = output / 'gecko-component'
    dest.mkdir(exist_ok=True)
    package = dest / source.name
    shutil.copy2(source, package)
    manifest = {
        'format': 1, 'architecture': 'aarch64', 'prefix': PREFIX,
        'input_sha256': fingerprint(), 'package': package.name,
        'package_version': version, 'package_sha256': sha256(package),
        'build_commit': subprocess.check_output(
            ['git', '-C', str(ROOT), 'rev-parse', 'HEAD'], text=True).strip(),
    }
    manifest_path = dest / 'manifest.json'
    manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + '\n')
    (dest / 'SHA256SUMS').write_text(''.join(
        f'{sha256(path)}  {path.name}\n' for path in (manifest_path, package)))
    verify(dest)


def verify(directory):
    package = one_package(directory)
    manifest_path = directory / 'manifest.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['format'] == 1
    assert manifest['architecture'] == 'aarch64' and manifest['prefix'] == PREFIX
    assert manifest['input_sha256'] == fingerprint(), 'Gecko build inputs have changed'
    assert manifest['package'] == package.name
    assert manifest['package_version'] == metadata(package)
    assert manifest['package_sha256'] == sha256(package), 'Gecko package checksum mismatch'
    expected = ''.join(f'{sha256(path)}  {path.name}\n' for path in (manifest_path, package))
    assert (directory / 'SHA256SUMS').read_text() == expected, 'Component checksum mismatch'
    print(f'Verified native Gecko component {manifest["input_sha256"]}: {package.name}')


if __name__ == '__main__':
    command = sys.argv[1]
    if command == 'fingerprint':
        print(fingerprint())
    elif command == 'record':
        record(pathlib.Path(sys.argv[2]))
    elif command == 'verify':
        verify(pathlib.Path(sys.argv[2]))
    else:
        raise SystemExit('Expected fingerprint, record OUTPUT_DIR, or verify COMPONENT_DIR')
