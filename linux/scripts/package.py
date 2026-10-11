#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Package a source-built Linux Zotero and reject uncovered native dependencies."""
import argparse
import configparser
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[2]
PINS = json.loads((ROOT / 'linux/upstream.json').read_text())
DEPS = json.loads((ROOT / 'linux/dependencies.json').read_text())


def digest(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file, 'sha256').hexdigest()


def native_dependencies(app, arch):
    bundled = {p.name for p in app.rglob('*') if p.is_file()}
    needed = set()
    count = 0
    for path in app.rglob('*'):
        if not path.is_file():
            continue
        with path.open('rb') as file:
            header = file.read(20)
        if header[:4] != b'\x7fELF':
            continue
        count += 1
        assert header[4:6] == b'\x02\x01', f'Not little-endian ELF64: {path}'
        assert int.from_bytes(header[18:20], 'little') == {'amd64': 62, 'arm64': 183}[arch], path
        dynamic = subprocess.check_output(['readelf', '-d', str(path)], text=True)
        needed.update(re.findall(r'\(NEEDED\).*?\[(.*?)\]', dynamic))
    assert count, 'No native runtime in package'
    external = needed - bundled
    unknown = external - DEPS['sonames'].keys()
    assert not unknown, f'Unmapped required libraries: {sorted(unknown)}'
    depends = sorted(set(DEPS['required']) | {DEPS['sonames'][n] for n in external})
    return depends, {'external_sonames': sorted(external), 'elf_files': count}


def validate_app(app, arch):
    ini = configparser.ConfigParser()
    ini.read(app / 'app/application.ini')
    assert ini['App']['Version'] == PINS['zotero_version']
    platform = configparser.ConfigParser()
    platform.read(app / 'platform.ini')
    assert platform['Build']['Milestone'] == PINS['gecko_version'].removesuffix('esr')
    with zipfile.ZipFile(app / 'app/omni.ja') as archive:
        prefs = archive.read('defaults/preferences/zotero.js').decode()
        for name in ['enabled', 'autoAuthorize']:
            assert f'pref("extensions.zotero.httpServer.localAPI.{name}", true);' in prefs
        api = archive.read('chrome/content/zotero/xpcom/server/server_localAPI.js').decode()
        assert "Zotero.Prefs.get('httpServer.localAPI.autoAuthorize')" in api
        assert 'return { allow: true, remember: true };' in api
        installer = archive.read('integration/libreoffice/resource/installer.mjs').decode()
        assert '/usr/bin/unopkg' in installer and '@TERMUX_PREFIX@' not in installer
        assert 'libreoffice-unopkg' not in installer
        assert 'chrome/browser/content/browser/license.html' in archive.namelist()
    assert (app / 'integration/libreoffice/Zotero_LibreOffice_Integration.oxt').is_file()
    assert not (app / 'libreoffice-pipe-compat.so').exists()
    assert not (app / 'updater').exists(), 'Self-updater must not ship in APT package'
    policy = json.loads((app / 'distribution/policies.json').read_text())
    assert policy == {'policies': {'DisableAppUpdate': True}}
    return native_dependencies(app, arch)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('architecture', choices=['amd64', 'arm64'])
    parser.add_argument('application', type=Path)
    parser.add_argument('output', type=Path)
    parser.add_argument('--source-sha', required=True)
    args = parser.parse_args()
    assert re.fullmatch(r'[a-f0-9]{40}', args.source_sha)
    arch = args.architecture
    version = f"{PINS['zotero_version']}-{PINS['package_revision']}"
    args.output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='zotero-deb-') as tmp:
        stage = Path(tmp)
        app = stage / 'usr/lib/zotero'
        shutil.copytree(args.application, app, symlinks=True)
        (app / 'updater').unlink()
        (app / 'distribution').mkdir(exist_ok=True)
        (app / 'distribution/policies.json').write_text('{"policies":{"DisableAppUpdate":true}}\n')
        depends, report = validate_app(app, arch)
        bin_dir = stage / 'usr/bin'
        bin_dir.mkdir(parents=True)
        (bin_dir / 'zotero').symlink_to('../lib/zotero/zotero')
        desktop = (ROOT / 'app/linux/zotero.desktop').read_text()
        desktop = re.sub(r'^Exec=.*$', 'Exec=/usr/bin/zotero -url %U', desktop, flags=re.M)
        desktop = re.sub(r'^Icon=.*$', 'Icon=zotero', desktop, flags=re.M)
        launcher = stage / 'usr/share/applications/zotero.desktop'
        launcher.parent.mkdir(parents=True)
        launcher.write_text(desktop)
        for size in [32, 64, 128]:
            icon = stage / f'usr/share/icons/hicolor/{size}x{size}/apps/zotero.png'
            icon.parent.mkdir(parents=True)
            shutil.copyfile(ROOT / f'app/linux/icons/icon{size}.png', icon)
        icon = stage / 'usr/share/icons/hicolor/symbolic/apps/zotero-symbolic.svg'
        icon.parent.mkdir(parents=True)
        shutil.copyfile(ROOT / 'app/linux/icons/symbolic.svg', icon)
        shutil.copytree(ROOT / 'termux/pi', stage / 'usr/share/zotero/pi')
        doc = stage / 'usr/share/doc/zotero'
        doc.mkdir(parents=True)
        for name, source in [('copyright', 'COPYING'), ('AGPL-3.0', 'LICENSE'),
                             ('README.md', 'linux/README.md'), ('upstream.json', 'linux/upstream.json')]:
            shutil.copyfile(ROOT / source, doc / name)
        (doc / 'upstream-submodules').write_text(subprocess.check_output(
            ['git', 'submodule', 'status', '--recursive'], cwd=ROOT, text=True))
        metadata = {'source_sha': args.source_sha, 'architecture': arch,
                    'upstream_commit': PINS['zotero_commit'], 'version': version,
                    'gecko_version': PINS['gecko_version'], **report}
        (doc / 'build-source.json').write_text(json.dumps(metadata, indent=2) + '\n')
        installed_size = sum(p.stat().st_size for p in stage.rglob('*') if p.is_file()) // 1024
        control = stage / 'DEBIAN/control'
        control.parent.mkdir()
        control.write_text(f'''Package: zotero
Version: {version}
Architecture: {arch}
Maintainer: Open Research Tools <229047507+openresearchtools@users.noreply.github.com>
Section: text
Priority: optional
Installed-Size: {installed_size}
Depends: {', '.join(depends)}
Recommends: {', '.join(DEPS['recommends'])}
Homepage: https://github.com/openresearchtools/zotero-termux
Description: Zotero reference manager with local automation enabled
 Source-built Zotero with native Linux Gecko and LibreOffice citation support.
 Local API access and unattended key authorization are enabled by default.
 Updates are managed by APT. Unofficial Open Research Tools package.
''')
        package = args.output / f'zotero_{version}_{arch}.deb'
        subprocess.run(['dpkg-deb', '--root-owner-group', '-Zxz', '--build', str(stage), str(package)], check=True)
        metadata['package'] = package.name
        metadata['sha256'] = digest(package)
        (args.output / 'build-source.json').write_text(json.dumps(metadata, indent=2) + '\n')
        (args.output / 'SHA256SUMS').write_text(f"{metadata['sha256']}  {package.name}\n")
        print(json.dumps(metadata, indent=2))


if __name__ == '__main__':
    main()
