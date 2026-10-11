#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-only
set -euo pipefail
root=$(cd "$(dirname "$0")/../.." && pwd)
cd "$root"
arch=$1
output=$(realpath -m "$2")
case "$arch" in amd64|arm64) ;; *) exit 1;; esac
test "$(dpkg --print-architecture)" = "$arch"
source_sha=$(git rev-parse HEAD)
source termux/upstream.lock
test "$(cat version)" = "$ZOTERO_VERSION.SOURCE"
git fetch --no-tags --depth 1 https://github.com/zotero/zotero.git "$ZOTERO_COMMIT"
test "$(git rev-parse 'FETCH_HEAD^{commit}')" = "$ZOTERO_COMMIT"
git diff --exit-code "$ZOTERO_COMMIT" HEAD -- . \
  ':(exclude)termux' ':(exclude)linux' ':(exclude)LICENSE' \
  ':(exclude).github/workflows/termux-build.yml' \
  ':(exclude).github/workflows/termux-native.yml' \
  ':(exclude).github/workflows/linux-build.yml' \
  ':(exclude).github/workflows/linux-native.yml'
readarray -t runtime < <(python3 - "$arch" <<'PY'
import json, sys
p=json.load(open('linux/upstream.json'))
r=p['gecko'][sys.argv[1]]
print(p['gecko_version']); print(r['architecture']); print(r['url']); print(r['sha256'])
PY
)
test "${runtime[0]}" = "$GECKO_VERSION"
mkdir -p app/xulrunner
archive="app/xulrunner/firefox-${runtime[0]}-${runtime[1]}.tar.xz"
if [[ ! -f "$archive" ]]; then
  curl --fail --location --retry 3 --output "$archive" "${runtime[2]}"
fi
printf '%s  %s\n' "${runtime[3]}" "$archive" | sha256sum --check -
# Only these shared automation patches are applied on desktop Linux.
# Native paths, launcher and LibreOffice sockets remain upstream Linux code.
patch --batch --fuzz=0 -p1 < termux/packages/zotero/0001-enable-local-api-by-default.patch
patch --batch --fuzz=0 -p1 < termux/packages/zotero/0007-local-api-auto-authorize.patch
export NODE_OPTIONS="${NODE_OPTIONS:-} --openssl-legacy-provider"
npm ci --no-audit --no-fund
app/scripts/fetch_xulrunner -p l -a "${runtime[1]}"
npm run build
prepared=$(mktemp -d)
trap 'rm -rf "$prepared"' EXIT
app/scripts/prepare_build -s build -o "$prepared" -c release
app/build.sh -d "$prepared" -p l -a "${runtime[1]}" -c release -s -q
python3 linux/scripts/package.py "$arch" "app/staging/Zotero_linux-${runtime[1]}" "$output" --source-sha "$source_sha"
