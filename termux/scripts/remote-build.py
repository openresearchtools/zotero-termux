#!/usr/bin/env python3
"""Dispatch the isolated x86_64 builder and collect its verified native packages."""
import json
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
REPOSITORY = 'openresearchtools/zotero-termux-build-x86_64'


def api(endpoint, body=None):
    command = ['gh', 'api', endpoint]
    if body is not None:
        command += ['--method', 'POST', '--input', '-']
    result = subprocess.run(command, input=json.dumps(body) if body is not None else None,
                            text=True, capture_output=True, check=True)
    return json.loads(result.stdout) if result.stdout.strip() else None


def main():
    directory = Path(sys.argv[1])
    source = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip()
    request = f'{os.environ["GITHUB_RUN_ID"]}-{os.environ.get("GITHUB_RUN_ATTEMPT", "1")}-x86_64'
    title = f'Zotero {source} / {request}'
    endpoint = f'repos/{REPOSITORY}/actions/workflows/build.yml'
    artifact_name = f'zotero-termux-x86_64-{source}'

    def find_run():
        return next((run for run in api(endpoint + '/runs?event=workflow_dispatch&per_page=100')['workflow_runs']
                     if run['display_title'] == title), None)

    run = find_run()
    if run is None:
        api(endpoint + '/dispatches', {'ref': 'main', 'inputs': {'source_sha': source, 'request_id': request}})
    linked = False
    while True:
        run = run or find_run()
        if run is not None:
            if not linked:
                print(run['html_url'], flush=True)
                with Path(os.environ['GITHUB_STEP_SUMMARY']).open('a') as summary:
                    summary.write(f'- [x86_64 build and downloadable artifacts]({run["html_url"]})\n')
                linked = True
            artifacts = api(f'repos/{REPOSITORY}/actions/runs/{run["id"]}/artifacts?per_page=100')['artifacts']
            if any(item['name'] == artifact_name and not item['expired'] for item in artifacts):
                subprocess.run(['gh', 'run', 'download', str(run['id']), '--repo', REPOSITORY,
                                '--name', artifact_name, '--dir', str(directory)], check=True)
                metadata = json.loads(next(directory.rglob('build-source.json')).read_text())
                if metadata != {'source_sha': source, 'architecture': 'x86_64'}:
                    raise RuntimeError('Builder artifact does not match the requested source and architecture')
                package_dir = next(directory.rglob('zotero_*_x86_64.deb')).parent
                subprocess.run([sys.executable, str(ROOT / 'termux/scripts/check-packages.py'), str(package_dir)],
                               env={**os.environ, 'TERMUX_ARCH': 'x86_64'}, check=True)
                (directory / 'builder.json').write_text(json.dumps({
                    'repository': REPOSITORY, 'run': run['id'], 'source_sha': source,
                    'url': run['html_url'],
                }, indent=2) + '\n')
                return
            run = api(f'repos/{REPOSITORY}/actions/runs/{run["id"]}')
            if run['status'] == 'completed':
                raise RuntimeError(f'Builder finished with {run["conclusion"]} without required package: {run["html_url"]}')
        time.sleep(30)


if __name__ == '__main__':
    main()
