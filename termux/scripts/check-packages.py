#!/usr/bin/env python3
"""Reject wrong-ABI packages and verify the packaged application, not its sources."""
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys
import tempfile
import zipfile


def output(*args):
    return subprocess.check_output(args, text=True)


def check_elf(file, name):
    header = output('readelf', '-h', str(file))
    assert re.search(r'Machine:\s+AArch64', header), name
    program = output('readelf', '-l', str(file))
    if 'Requesting program interpreter:' in program:
        assert '/system/bin/linker64' in program, name
    dynamic = output('readelf', '-d', str(file))
    assert not re.search(r'lib(?:c|m|pthread|dl|rt)\.so\.[0-9]|ld-linux', dynamic), name
    assert 'GLIBC_' not in output('readelf', '-V', str(file)), name


def check_archive(data, name):
    # Preserve the portable upstream LibreOffice installer. This JNA jar is an
    # external JVM resource, not part of Zotero's loaded Gecko runtime. Its only
    # native call in the pinned integration is Windows user32 window activation.
    # The exact hash prevents this exception silently accepting changed payloads.
    if name == 'integration/libreoffice/Zotero_LibreOffice_Integration.oxt!/external_jars/jna.jar':
        assert hashlib.sha256(data).hexdigest() == (
            '34ed1e1f27fa896bca50dbc4e99cf3732967cec387a7a0d5e3486c09673fe8c6'
        ), 'Upstream LibreOffice JNA changed: review its native payloads'
        return 0
    count = 0
    with zipfile.ZipFile(io.BytesIO(data)) as jar:
        for member in jar.infolist():
            if member.is_dir():
                continue
            payload = jar.read(member)
            nested_name = name + '!/' + member.filename
            if payload.startswith(b'\x7fELF'):
                with tempfile.NamedTemporaryFile() as tmp:
                    tmp.write(payload)
                    tmp.flush()
                    check_elf(tmp.name, nested_name)
                count += 1
            elif pathlib.PurePosixPath(member.filename).suffix.lower() in ARCHIVE_SUFFIXES:
                count += check_archive(payload, nested_name)
    return count


ARCHIVE_SUFFIXES = {'.ja', '.jar', '.zip', '.xpi', '.oxt'}
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
            installer = jar.read('integration/libreoffice/resource/installer.mjs').decode()
            # Check the shipped, substituted paths, not just the patch sources.
            installed_prefix = '/' + str(prefix.relative_to(root))
            assert f'{installed_prefix}/bin/unopkg' in installer
            assert f'{installed_prefix}/lib/zotero/libreoffice-unopkg' in installer
            wizard = jar.read('integration/libreoffice/chrome/install.js').decode()
            assert 'openjdk-21-x' in wizard and f'{installed_prefix}/bin/apt-get' in wizard
            assert '@TERMUX_PREFIX@' not in installer + wizard
        wrapper = (app / 'libreoffice-unopkg').read_text()
        assert wrapper.startswith(f'#!{installed_prefix}/bin/bash\n')
        assert '@TERMUX_PREFIX@' not in wrapper
        assert (app / 'libreoffice-pipe-compat.so').is_file()
        pi = prefix / 'share/zotero/pi'
        manifest = json.loads((pi / 'package.json').read_text())
        for entry in manifest['pi']['extensions']:
            assert (pi / entry).is_file()
        for entry in manifest['pi']['skills']:
            assert (pi / entry / 'SKILL.md').is_file()
        assert (pi / 'libreoffice.mjs').is_file()
        policy = json.loads((app / 'distribution/policies.json').read_text())
        assert policy['policies']['DisableAppUpdate'] is True
        checked = 0
        for file in app.rglob('*'):
            if not file.is_file() or file.is_symlink():
                continue
            if file.suffix.lower() in ARCHIVE_SUFFIXES:
                checked += check_archive(file.read_bytes(), str(file.relative_to(app)))
                continue
            with file.open('rb') as stream:
                if stream.read(4) != b'\x7fELF':
                    continue
            check_elf(file, file)
            checked += 1
        assert checked >= 2
        print(f'{package.name}: {checked} AArch64 Bionic runtime ELF files; upstream UI, license, API defaults verified')
        print('Archives checked; exact upstream multi-platform LibreOffice JNA installer resource preserved')
