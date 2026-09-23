TERMUX_PKG_HOMEPAGE=https://www.zotero.org/
TERMUX_PKG_DESCRIPTION="Zotero reference manager for native Bionic Termux (unofficial build)"
TERMUX_PKG_LICENSE="AGPL-3.0, MPL-2.0"
TERMUX_PKG_LICENSE_FILE="COPYING"
TERMUX_PKG_MAINTAINER="@openresearchtools"
TERMUX_PKG_VERSION=10.0.3
TERMUX_PKG_SRCURL=git+https://github.com/openresearchtools/zotero-termux.git
TERMUX_PKG_GIT_BRANCH="$TERMUX_PKG_VERSION"
TERMUX_PKG_EXCLUDED_ARCHES="arm, i686, x86_64"
TERMUX_PKG_BUILD_IN_SRC=true
TERMUX_PKG_AUTO_UPDATE=false
TERMUX_PKG_DEPENDS="bash, coreutils, ffmpeg, fontconfig, freetype, gdk-pixbuf, glib, gtk3, libandroid-shmem, libandroid-spawn, libc++, libcairo, libevent, libffi, libice, libjpeg-turbo, libnspr, libnss, libpixman, libsm, libvpx, libwebp, libx11, libxcb, libxcomposite, libxdamage, libxext, libxfixes, libxrandr, libxtst, pango, pulseaudio, zlib"
TERMUX_PKG_BUILD_DEPENDS="zotero-gecko"
TERMUX_PKG_RECOMMENDS="ttf-dejavu, termux-x11-nightly"

termux_step_post_get_source() {
	# The tag is convenient for Termux's git downloader, but a moved tag must fail.
	test "$(git rev-parse HEAD)" = 80bc5565e000c3f24c37e0020713a41ec9f42e09
}

termux_step_pre_configure() {
	termux_setup_nodejs
	# node-gyp dependencies, if any, are host build tools.
	unset npm_config_arch npm_config_platform
	export NODE_OPTIONS="${NODE_OPTIONS:-} --openssl-legacy-provider"
	npm ci
}

termux_step_configure() {
	local runtime="$TERMUX_PREFIX/lib/zotero-gecko/firefox"
	test -f "$runtime/libxul.so"
	grep -Fx 'Milestone=140.15.0' "$runtime/platform.ini"
	"$READELF" -l "$runtime/firefox-bin" | grep -F '/system/bin/linker64'
	mkdir -p app/xulrunner
	# Supply the native runtime to upstream fetch_xulrunner. It still performs
	# Zotero's complete modify_omni procedure on this exact ESR version.
	tar -cJf "$TERMUX_PKG_TMPDIR/firefox-termux.tar.xz" -C "$(dirname "$runtime")" firefox
	export ZOTERO_TERMUX_RUNTIME_ARCHIVE="$TERMUX_PKG_TMPDIR/firefox-termux.tar.xz"
	app/scripts/fetch_xulrunner -p l -a arm64
}

termux_step_make() {
	npm run build
	mkdir -p "$TERMUX_PKG_TMPDIR/prepared"
	app/scripts/prepare_build -s "$TERMUX_PKG_SRCDIR/build" \
		-o "$TERMUX_PKG_TMPDIR/prepared" -c release
	app/build.sh -d "$TERMUX_PKG_TMPDIR/prepared" -p l -a arm64 -c release -s -q
}

termux_step_make_install() {
	local dest="$TERMUX_PREFIX/lib/zotero"
	mkdir -p "$dest"
	cp -a app/staging/Zotero_linux-arm64/. "$dest/"
	# Package management owns updates. Desktop updates contain glibc binaries.
	mkdir -p "$dest/distribution"
	printf '%s\n' '{"policies":{"DisableAppUpdate":true}}' > "$dest/distribution/policies.json"
	ln -sfr "$dest/zotero" "$TERMUX_PREFIX/bin/zotero"
	sed "s|@TERMUX_PREFIX@|$TERMUX_PREFIX|g" "$TERMUX_PKG_BUILDER_DIR/zotero.desktop" \
		> "$TERMUX_PKG_TMPDIR/zotero.desktop"
	install -Dm644 "$TERMUX_PKG_TMPDIR/zotero.desktop" "$TERMUX_PREFIX/share/applications/zotero.desktop"
	for size in 32 64 128; do
		install -Dm644 "app/linux/icons/icon$size.png" \
			"$TERMUX_PREFIX/share/icons/hicolor/${size}x${size}/apps/zotero.png"
	done
	install -Dm644 app/linux/icons/symbolic.svg "$TERMUX_PREFIX/share/icons/hicolor/symbolic/apps/zotero-symbolic.svg"
	mkdir -p "$TERMUX_PREFIX/share/doc/zotero"
	install -m644 "$TERMUX_PREFIX/share/doc/zotero-gecko/LICENSE" \
		"$TERMUX_PREFIX/share/doc/zotero/Gecko-LICENSE"
	git rev-parse HEAD > "$TERMUX_PREFIX/share/doc/zotero/upstream-commit"
	git submodule status --recursive > "$TERMUX_PREFIX/share/doc/zotero/upstream-submodules"
}
