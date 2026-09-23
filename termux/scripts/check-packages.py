#!/usr/bin/env python3
"""Reject wrong-ABI packages and verify the packaged application, not its sources."""
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import zipfile


def output(*args):
    return subprocess.check_output(args, text=True)


directory = pathlib.Path(sys.argv[1])
packages = sorted(directory.glob('zotero_*.deb'))
assert len(packages) == 1, f'Expected one Zotero package, found {packages}'
for package in packages:
    assert output('dpkg-deb', '-f', str(package), 'Architecture').strip() == 'aarch64'
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['dpkg-deb', '-x', str(package), tmp], check=True)
        root = pathlib.Path(tmp)
        apps = list(root.glob('**/lib/zotero/app/application.ini'))
        assert len(apps) == 1, apps
        app = apps[0].parent.parent
        prefix = app.parent.parent
        assert 'Name=Zotero' in apps[0].read_text()
        assert 'Version=10.0.3' in apps[0].read_text()
        assert (prefix / 'share/doc/zotero/COPYING').is_file()
        assert 'GNU AFFERO GENERAL PUBLIC LICENSE' in (prefix / 'share/doc/zotero/COPYING').read_text()
        with zipfile.ZipFile(app / 'app/omni.ja') as jar:
            prefs = jar.read('defaults/preferences/zotero.js').decode()
            assert 'pref("extensions.zotero.httpServer.localAPI.enabled", true);' in prefs
            assert 'pref("extensions.zotero.httpServer.localAPI.autoAuthorize", true);' in prefs
            assert 'pref("extensions.zotero.httpServer.enabled", true);' in prefs
            local_api = jar.read('chrome/content/zotero/xpcom/server/server_localAPI.js').decode()
            assert "if (Zotero.Prefs.get('httpServer.localAPI.autoAuthorize'))" in local_api
            assert 'return { allow: true, remember: true };' in local_api
            assert any('zoteroPane.xhtml' in x for x in jar.namelist())
        policy = json.loads((app / 'distribution/policies.json').read_text())
        assert policy['policies']['DisableAppUpdate'] is True
        checked = 0
        for file in app.rglob('*'):
            if not file.is_file() or file.is_symlink():
                continue
            with file.open('rb') as stream:
                if stream.read(4) != b'\x7fELF':
                    continue
            header = output('readelf', '-h', str(file))
            assert re.search(r'Machine:\s+AArch64', header), file
            program = output('readelf', '-l', str(file))
            if 'Requesting program interpreter:' in program:
                assert '/system/bin/linker64' in program, file
            dynamic = output('readelf', '-d', str(file))
            assert not re.search(r'lib(?:c|m|pthread|dl|rt)\.so\.[0-9]|ld-linux', dynamic), file
            checked += 1
        assert checked >= 2
        print(f'{package.name}: {checked} AArch64 Bionic ELF files; upstream UI, license, API defaults verified')
