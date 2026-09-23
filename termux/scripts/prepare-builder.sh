#!/usr/bin/env bash
set -euo pipefail
root=$(cd "$(dirname "$0")/.." && pwd)
source "$root/upstream.lock"
builder=${1:-"$root/termux-packages"}
if [[ ! -d "$builder/.git" ]]; then
    git init "$builder"
    git -C "$builder" remote add origin https://github.com/termux/termux-packages.git
    git -C "$builder" fetch --depth 1 origin "$TERMUX_PACKAGES_COMMIT"
    git -C "$builder" checkout --detach FETCH_HEAD
fi
test "$(git -C "$builder" rev-parse HEAD)" = "$TERMUX_PACKAGES_COMMIT"
for package in zotero zotero-gecko; do
    mkdir -p "$builder/x11-packages/$package"
    cp -a "$root/packages/$package/." "$builder/x11-packages/$package/"
done
printf 'Recipes installed in %s/x11-packages\n' "$builder"
