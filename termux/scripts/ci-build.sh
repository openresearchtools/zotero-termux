#!/usr/bin/env bash
set -euo pipefail
# Run inside the official Termux builder, with this script copied to its root.
export GIT_LFS_SKIP_SMUDGE=1
export TERMUX_PKG_MAKE_PROCESSES=2
phase=${1:-all}
# The GHA backend stores compiler outputs as they finish, including when a
# later compiler invocation fails. Keep its server inside the builder container.
if [[ "${1:-all}" != zotero && -n "${ZOTERO_SCCACHE:-}" ]]; then
    test -x "$ZOTERO_SCCACHE"
    "$ZOTERO_SCCACHE" --start-server
    finish_cache() {
        local result=$?
        "$ZOTERO_SCCACHE" --show-stats || true
        "$ZOTERO_SCCACHE" --stop-server || true
        exit "$result"
    }
    trap finish_cache EXIT
fi
case "$phase" in
    gecko|all) ./build-package.sh -I -a aarch64 zotero-gecko ;;
    zotero) ;;
    *) echo "Expected gecko, zotero, or all" >&2; exit 2 ;;
esac
if [[ "$phase" == zotero || "$phase" == all ]]; then
    # Restore a native runtime cached by this workflow's exact recipe key.
    # This is only for the standard CI prefix; custom-prefix builds use the
    # normal source dependency path described in README.md.
    if [[ ! -f /data/data/.built-packages/zotero-gecko ]]; then
        runtime=(output/zotero-gecko_*_aarch64.deb)
        test "${#runtime[@]}" -eq 1
        test "$(dpkg-deb -f "${runtime[0]}" Architecture)" = aarch64
        # Match the framework's dependency extraction: preserve existing /data
        # directory permissions and do not try to change the container root.
        dpkg-deb --fsys-tarfile "${runtime[0]}" | \
            tar x --no-overwrite-dir --transform='s#^.$#data#' -C /
        mkdir -p /data/data/.built-packages
        dpkg-deb -f "${runtime[0]}" Version > /data/data/.built-packages/zotero-gecko
    fi
    ./build-package.sh -I -a aarch64 zotero
fi
