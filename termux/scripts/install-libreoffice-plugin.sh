#!/usr/bin/env bash
# SPDX-License-Identifier: AGPL-3.0-only
set -euo pipefail

# Run as the Termux application user after installing libreoffice, openjdk-21,
# openjdk-21-x, and clang. This registers Zotero's unchanged bundled extension.
if [[ $(id -u) == 0 || -z ${PREFIX:-} ]]; then
    echo 'Run this script inside Termux as its normal application user.' >&2
    exit 1
fi
if pgrep -x soffice.bin >/dev/null; then
    echo 'Save your documents and close LibreOffice before installing its plugin.' >&2
    exit 1
fi
for command in clang unopkg; do
    command -v "$command" >/dev/null || {
        echo "Missing $command; install libreoffice, openjdk-21, openjdk-21-x, and clang." >&2
        exit 1
    }
done
export JAVA_HOME="$PREFIX/lib/jvm/java-21-openjdk"
test -x "$JAVA_HOME/bin/java"
extension="$PREFIX/lib/zotero/integration/libreoffice/Zotero_LibreOffice_Integration.oxt"
test -f "$extension"
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
build_dir=$(mktemp -d "${TMPDIR:-$PREFIX/tmp}/zotero-office-install.XXXXXX")
trap 'rm -rf -- "$build_dir"' EXIT
clang -shared -fPIC -O2 -Wall -Wextra -Werror \
    "-DTERMUX_PREFIX=\"$PREFIX\"" \
    "$script_dir/../helpers/libreoffice-pipe-compat.c" \
    -o "$build_dir/libpipe-compat.so" -lcrypto -ldl

# Scope the compatibility library to unopkg and its registration subprocesses.
# Neither installed application nor extension is modified, and normal launches
# do not need LD_PRELOAD. Preserve any existing Termux execution preload.
LD_PRELOAD="$build_dir/libpipe-compat.so${LD_PRELOAD:+:$LD_PRELOAD}" \
    unopkg add --force "$extension"
echo 'Zotero LibreOffice plugin installed. Start LibreOffice normally.'
