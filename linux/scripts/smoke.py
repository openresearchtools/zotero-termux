#!/usr/bin/env python3
# SPDX-License-Identifier: AGPL-3.0-only
"""Run installed native Zotero/API and Java/OXT checks with disposable profiles."""
import configparser
import json
import os
from pathlib import Path
import signal
import re
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.request


def request(base, path, payload=None, headers=None):
    req = urllib.request.Request(base + path,
        data=None if payload is None else json.dumps(payload).encode(),
        headers={'Zotero-API-Version': '3', 'Content-Type': 'application/json', **(headers or {})})
    try:
        response = urllib.request.urlopen(req, timeout=5)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


def main():
    app = Path(sys.argv[1] if len(sys.argv) > 1 else '/usr/lib/zotero')
    ini = configparser.ConfigParser()
    ini.read(app / 'app/application.ini')
    # Hosted runners also have manually selected Java alternatives. Resolve the
    # actual default-jre dependency so preinstalled Temurin cannot hide a gap.
    dependencies = subprocess.check_output(
        ['dpkg-query', '-W', '-f=${Depends}', 'default-jre-headless'], text=True)
    package = re.search(r'openjdk-[0-9]+-jre-headless', dependencies).group()
    files = subprocess.check_output(['dpkg-query', '-L', package], text=True).splitlines()
    java = next(Path(name) for name in files if name.endswith('/bin/java'))
    java_home = java.parent.parent
    subprocess.run([str(java), '-version'], check=True)
    java_environment = {**os.environ, 'JAVA_HOME': str(java_home),
                        'UNO_JAVA_JFW_JREHOME': java_home.as_uri()}
    with tempfile.TemporaryDirectory(prefix='zotero-linux-smoke-') as tmp:
        directory = Path(tmp)
        profile = directory / 'zotero'
        profile.mkdir()
        data = directory / 'library'
        data.mkdir()
        # A private test port avoids contact with any personal Zotero instance.
        import socket
        with socket.socket() as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        (profile / 'user.js').write_text(
            f'user_pref("extensions.zotero.httpServer.port", {port});\n'
            f'user_pref("extensions.zotero.dataDir", {json.dumps(str(data))});\n'
            'user_pref("extensions.zotero.useDataDir", true);\n'
            'user_pref("extensions.zotero.firstRun2", false);\n'
            'user_pref("extensions.zotero.automaticScraperUpdates", false);\n')
        with (directory / 'zotero.log').open('w+') as log:
            child = subprocess.Popen([str(app / 'zotero'), '-no-remote', '-profile', str(profile)],
                                     stdout=log, stderr=log, start_new_session=True)
            try:
                base = f'http://127.0.0.1:{port}'
                deadline = time.monotonic() + 120
                while time.monotonic() < deadline:
                    assert child.poll() is None, f'Zotero exited: {child.returncode}'
                    try:
                        status, headers, body = request(base, '/api/users/0/items?limit=1')
                        if status == 200:
                            break
                    except (OSError, urllib.error.URLError):
                        pass
                    time.sleep(1)
                else:
                    raise RuntimeError('Installed Zotero local API did not become ready')
                assert isinstance(json.loads(body), list)
                identity = {'Zotero-Server-ID': headers['Zotero-Server-ID']}
                status, _, _ = request(base, '/api/users/0/items', [], identity)
                assert status == 401
                status, _, body = request(base, '/api/local/authorize', {'appName': 'Linux package smoke test'}, identity)
                assert status == 200
                key = json.loads(body)
                assert key['remember'] is True and key['key']
                identity['Zotero-API-Key'] = key['key']
                for _ in range(2):
                    status, _, body = request(base, '/api/users/0/items', [], identity)
                    assert status == 400 and body == b'No items provided'
                print(f"Installed Zotero {ini['App']['Version']}: reads, unattended authorization, remembered keys and rejection of unauthenticated writes passed")
            except Exception:
                log.seek(0)
                print(log.read()[-12000:], file=sys.stderr)
                raise
            finally:
                if child.poll() is None:
                    os.killpg(child.pid, signal.SIGTERM)
                    try:
                        child.wait(timeout=15)
                    except subprocess.TimeoutExpired:
                        os.killpg(child.pid, signal.SIGKILL)
                        child.wait()
        # Normal desktop unopkg and Java; no Termux wrapper or socket preload.
        user_install = '-env:UserInstallation=' + (directory / 'libreoffice').as_uri()
        oxt = app / 'integration/libreoffice/Zotero_LibreOffice_Integration.oxt'
        subprocess.run(['unopkg', user_install, 'add', '--force', str(oxt)],
                       env=java_environment, check=True, timeout=90)
        listing = subprocess.check_output(['unopkg', user_install, 'list', 'org.Zotero.integration.openoffice'],
                                          env=java_environment, text=True, timeout=45)
        summary = listing.split('bundled Packages:')[0]
        assert 'is registered: yes' in summary
        print('Bundled LibreOffice OXT registered with the system Java runtime and standard Linux sockets; live Writer citation UI still requires separate acceptance')


if __name__ == '__main__':
    main()
