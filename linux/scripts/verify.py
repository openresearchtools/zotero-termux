#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Verify collected DEBs against their requested source, ABI, policies and hashes."""
import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from package import PINS, digest, validate_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--architecture', required=True, choices=['amd64', 'arm64'])
    parser.add_argument('--source-sha', required=True)
    args = parser.parse_args()
    records = list(args.directory.rglob('build-source.json'))
    assert len(records) == 1, 'Expected one build manifest'
    record = json.loads(records[0].read_text())
    assert record['source_sha'] == args.source_sha
    assert record['architecture'] == args.architecture
    assert record['upstream_commit'] == PINS['zotero_commit']
    assert record['version'] == f"{PINS['zotero_version']}-{PINS['package_revision']}"
    package = records[0].parent / record['package']
    assert package.name == f"zotero_{record['version']}_{args.architecture}.deb"
    assert record['sha256'] == digest(package)
    assert len(list(args.directory.rglob('*.deb'))) == 1
    fields = subprocess.check_output(['dpkg-deb', '-f', str(package),
                                     'Package', 'Version', 'Architecture', 'Depends'], text=True)
    control = dict(line.split(': ', 1) for line in fields.splitlines())
    assert control['Package'] == 'zotero'
    assert control['Version'] == record['version']
    assert control['Architecture'] == args.architecture
    with tempfile.TemporaryDirectory(prefix='zotero-verify-') as tmp:
        subprocess.run(['dpkg-deb', '-x', str(package), tmp], check=True)
        depends, report = validate_app(Path(tmp) / 'usr/lib/zotero', args.architecture)
        assert control['Depends'] == ', '.join(depends)
        for key, value in report.items():
            assert record[key] == value
        installed = json.loads((Path(tmp) / 'usr/share/doc/zotero/build-source.json').read_text())
        assert installed == {k: v for k, v in record.items() if k not in ['package', 'sha256']}
    print(f"Verified {package.name}: source, checksum, Linux ABI, dependencies, automation, APT updates and stock LibreOffice paths")


if __name__ == '__main__':
    main()
