#!/usr/bin/env python3
"""Check a running Zotero's real API and retained write authorization boundary."""
import argparse
import json
import urllib.error
import urllib.request

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--base', default='http://127.0.0.1:23119')
parser.add_argument('--expect-disabled', action='store_true')
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
