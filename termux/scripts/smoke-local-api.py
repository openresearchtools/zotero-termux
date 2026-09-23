#!/usr/bin/env python3
"""Check a running Zotero's API, optionally including unattended authorization."""
import argparse
import json
import urllib.error
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', default='http://127.0.0.1:23119')
mode = parser.add_mutually_exclusive_group()
mode.add_argument('--expect-disabled', action='store_true')
mode.add_argument('--expect-auto-authorize', action='store_true',
                  help='Request one remembered API key and test two empty writes')
args = parser.parse_args()


def request(path, data=None, headers=None):
    req = urllib.request.Request(args.base + path, data=data, headers={
        'Zotero-API-Version': '3', **(headers or {})
    })
    try:
        response = urllib.request.urlopen(req, timeout=15)
    except urllib.error.HTTPError as error:
        response = error
    with response:
        return response.status, response.headers, response.read()


status, headers, body = request('/api/users/0/items?limit=1')
if args.expect_disabled:
    assert status == 403, (status, body)
    print('User-disabled local API correctly returns 403')
else:
    assert status == 200, (status, body)
    assert isinstance(json.loads(body), list)
    server_id = headers['Zotero-Server-ID']
    assert server_id
    assert headers['Zotero-API-Version'] == '3'
    status, _, body = request('/api/itemTypes')
    assert status == 200, (status, body)
    assert any(entry['itemType'] == 'journalArticle' for entry in json.loads(body))
    # An empty write without a key must be rejected, preserving stock behavior.
    # No actual item is created or modified by this test.
    status, _, body = request('/api/users/0/items', b'[]', {
        'Content-Type': 'application/json', 'Zotero-Server-ID': server_id
    })
    assert status == 401, (status, body)
    print('Local API v3: reads work; unauthenticated writes correctly return 401')
    if args.expect_auto_authorize:
        status, _, body = request('/api/local/authorize',
            json.dumps({'appName': 'Termux API smoke test'}).encode(), {
                'Content-Type': 'application/json', 'Zotero-Server-ID': server_id
            })
        assert status == 200, (status, body)
        permission = json.loads(body)
        assert permission['remember'] is True
        assert permission['key']
        for _ in range(2):
            status, _, body = request('/api/users/0/items', b'[]', {
                'Content-Type': 'application/json', 'Zotero-Server-ID': server_id,
                'Zotero-API-Key': permission['key']
            })
            assert status == 200, (status, body)
            assert not json.loads(body)['failed']
        print('Automatic authorization and reusable key work without a dialog; no items changed')
