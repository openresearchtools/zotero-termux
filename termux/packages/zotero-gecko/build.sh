TERMUX_PKG_HOMEPAGE=https://www.mozilla.org/firefox
TERMUX_PKG_DESCRIPTION="Firefox ESR runtime built for native Bionic Zotero (build dependency)"
TERMUX_PKG_LICENSE="MPL-2.0"
TERMUX_PKG_MAINTAINER="@openresearchtools"
TERMUX_PKG_VERSION="140.15.0"
TERMUX_PKG_REVISION=1
TERMUX_PKG_EXCLUDED_ARCHES="arm, i686, x86_64"
TERMUX_RUST_VERSION=1.86.0
TERMUX_PKG_SRCURL=https://archive.mozilla.org/pub/firefox/releases/${TERMUX_PKG_VERSION}esr/source/firefox-${TERMUX_PKG_VERSION}esr.source.tar.xz
TERMUX_PKG_SHA256=358bb03c550f95172f1e31694e4287da3411560df91e931cb25210efdf90e524
# ffmpeg and pulseaudio are dependencies through dlopen(3):
TERMUX_PKG_DEPENDS="ffmpeg, fontconfig, freetype, gdk-pixbuf, glib, gtk3, libandroid-shmem, libandroid-spawn, libc++, libcairo, libevent, libffi, libice, libjpeg-turbo, libnspr, libnss, libpixman, libsm, libvpx, libwebp, libx11, libxcb, libxcomposite, libxdamage, libxext, libxfixes, libxrandr, libxtst, pango, pulseaudio, zlib"
TERMUX_PKG_BUILD_DEPENDS="libcpufeatures, libice, libsm"
TERMUX_PKG_BUILD_IN_SRC=true
TERMUX_PKG_AUTO_UPDATE=false

termux_step_post_get_source() {
	local f="media/ffvpx/config_unix_aarch64.h"
	echo "Applying sed substitution to ${f}"
	sed -E '/^#define (CONFIG_LINUX_PERF|HAVE_SYSCTL) /s/1$/0/' -i ${f}
}

termux_step_pre_configure() {
	# Patch 0029 changes a vendored crate file. Keep Cargo's integrity checking
	# enabled and update only that file's checksum to the reviewed patched hash.
	python3 - <<'PY'
import hashlib
import json
from pathlib import Path
crate = Path('third_party/rust/glslopt')
name = 'glsl-optimizer/include/c11/threads_posix.h'
original = 'f8ad2b69fa472e332b50572c1b2dcc1c8a0fa783a1199aad245398d3df421b4b'
patched = '5fa592653213459e2cce70b430715246d53fd1a10c1866acf427874530a69f92'
assert hashlib.sha256((crate / name).read_bytes()).hexdigest() == patched
path = crate / '.cargo-checksum.json'
checksums = json.loads(path.read_text())
assert checksums['files'][name] in (original, patched)
checksums['files'][name] = patched
path.write_text(json.dumps(checksums))
PY
	# ESR 140's mach is incompatible with Python 3.14 on newer build hosts.
	# Build its host interpreter in a clean environment, never with target flags.
	local host_python="$TERMUX_COMMON_CACHEDIR/zotero-python-3.12.12"
	if [ ! -f "$host_python/.complete" ]; then
		termux_download https://www.python.org/ftp/python/3.12.12/Python-3.12.12.tar.xz \
			"$TERMUX_PKG_CACHEDIR/python-3.12.12.tar.xz" \
			fb85a13414b028c49ba18bbd523c2d055a30b56b18b92ce454ea2c51edc656c4
		mkdir -p "$TERMUX_PKG_TMPDIR/host-python"
		tar -xf "$TERMUX_PKG_CACHEDIR/python-3.12.12.tar.xz" \
			-C "$TERMUX_PKG_TMPDIR/host-python" --strip-components=1
		(
			cd "$TERMUX_PKG_TMPDIR/host-python"
			env -i PATH=/usr/bin:/bin HOME="$HOME" CC=/usr/bin/cc \
				./configure --prefix="$host_python" --with-ensurepip=install
			env -i PATH=/usr/bin:/bin HOME="$HOME" make -j "$TERMUX_PKG_MAKE_PROCESSES"
			env -i PATH=/usr/bin:/bin HOME="$HOME" make install
		)
		"$host_python/bin/python3" -c 'import ssl, sqlite3, zlib; assert __import__("sys").version_info[:2] == (3, 12)'
		touch "$host_python/.complete"
	fi
	export PATH="$host_python/bin:$PATH"
	termux_setup_nodejs
	termux_setup_rust

	# https://github.com/rust-lang/rust/issues/49853
	# https://github.com/rust-lang/rust/issues/45854
	# Out of memory when building gkrust
	# CI shows (signal: 9, SIGKILL: kill)
	if [ "$TERMUX_DEBUG_BUILD" = false ]; then
		local env_host=$(printf $CARGO_TARGET_NAME | tr a-z A-Z | sed s/-/_/g)
		export CARGO_TARGET_${env_host}_RUSTFLAGS+=" -C debuginfo=1"
	fi

	cargo install cbindgen --version 0.28.0 --locked

	export HOST_CC=$(command -v clang)
	export HOST_CXX=$(command -v clang++)

	export BINDGEN_CFLAGS="--target=$CCTERMUX_HOST_PLATFORM --sysroot=$TERMUX_STANDALONE_TOOLCHAIN/sysroot"
	local env_name=BINDGEN_EXTRA_CLANG_ARGS_${CARGO_TARGET_NAME@U}
	env_name=${env_name//-/_}
	export $env_name="$BINDGEN_CFLAGS"

	# https://reviews.llvm.org/D141184
	CXXFLAGS+=" -U__ANDROID__ -D_LIBCPP_HAS_NO_C11_ALIGNED_ALLOC"
	LDFLAGS+=" -landroid-shmem -landroid-spawn -llog"

	if [ "$TERMUX_ARCH" = "arm" ]; then
		# For symbol android_getCpuFeatures
		LDFLAGS+=" -l:libndk_compat.a"
	fi
}

termux_step_configure() {
	if [ "$TERMUX_CONTINUE_BUILD" == "true" ]; then
		termux_step_pre_configure
		cd $TERMUX_PKG_SRCDIR
	fi

	sed \
		-e "s|@TERMUX_HOST_PLATFORM@|${TERMUX_HOST_PLATFORM}|" \
		-e "s|@TERMUX_PREFIX@|${TERMUX_PREFIX}|" \
		-e "s|@CARGO_TARGET_NAME@|${CARGO_TARGET_NAME}|" \
		$TERMUX_PKG_BUILDER_DIR/mozconfig.cfg > .mozconfig

	if [ -n "${ZOTERO_SCCACHE:-}" ]; then
		test -x "$ZOTERO_SCCACHE"
		# Mozilla uses --with-ccache=sccache for both C/C++ and Rust.
		printf 'ac_add_options --with-ccache=%s\n' "$ZOTERO_SCCACHE" >> .mozconfig
	fi

	if [ "$TERMUX_DEBUG_BUILD" = true ]; then
		cat >>.mozconfig - <<END
ac_add_options --enable-debug-symbols
ac_add_options --disable-install-strip
END
	fi

	./mach configure
}

termux_step_make() {
	./mach build -j "$TERMUX_PKG_MAKE_PROCESSES"
	./mach build -j "$TERMUX_PKG_MAKE_PROCESSES" package
}

termux_step_make_install() {
	# Keep the exact ESR runtime separate from the user's Firefox installation.
	local archive
	archive=$(find obj-termux/dist -maxdepth 1 -name 'firefox-*.tar.xz' -print -quit)
	test -n "$archive"
	mkdir -p "$TERMUX_PREFIX/lib/zotero-gecko"
	tar -xf "$archive" -C "$TERMUX_PREFIX/lib/zotero-gecko"
	install -Dm644 LICENSE "$TERMUX_PREFIX/share/doc/zotero-gecko/LICENSE"
}

termux_step_post_make_install() {
	local elf="$TERMUX_PREFIX/lib/zotero-gecko/firefox/firefox-bin"
	"$READELF" -l "$elf" | grep -F '/system/bin/linker64'
	if "$READELF" -d "$elf" | grep -q '(RELR)'; then
		termux_error_exit "DT_RELR is unsupported on older Android releases"
	fi
}
