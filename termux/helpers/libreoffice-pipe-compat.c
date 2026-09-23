// SPDX-License-Identifier: AGPL-3.0-only
#define _GNU_SOURCE
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <pthread.h>
#include <sys/un.h>
#include <openssl/sha.h>

#ifndef TERMUX_PREFIX
#error Build with the installed LibreOffice package's TERMUX_PREFIX
#endif

/* LibreOffice's extension registrar generates up to 64 hexadecimal characters
 * for a UNO pipe ID. Termux's longer temporary-directory prefix can push its
 * pathname past sockaddr_un.sun_path. Interpose only during registration;
 * shorten overflowing ASCII IDs to a deterministic 128-bit digest so both
 * ends agree. Permissions, owner, and transport remain LibreOffice's choices.
 *
 * rtl_uString's published C ABI begins with two sal_Int32 members, followed by
 * its UTF-16 buffer. Resolve SAL lazily after the original library is loaded.
 */
typedef struct { int32_t refs, length; uint16_t buffer[]; } UString;
static void *(*original)(UString *, int, void *);
static void (*from_ascii)(UString **, const char *);
static void (*release_string)(UString *);
static pthread_once_t init_once = PTHREAD_ONCE_INIT;

/* Budget ten digits for a uid, its separator, and the terminating NUL. */
enum { PIPE_OVERHEAD = sizeof(TERMUX_PREFIX "/tmp/OSL_PIPE_") + 11 };
_Static_assert(PIPE_OVERHEAD + 35 <= sizeof(((struct sockaddr_un *)0)->sun_path),
               "Termux prefix is too long for this compatibility helper");

static void init_symbols(void) {
    original = dlsym(RTLD_NEXT, "osl_createPipe");
    from_ascii = dlsym(RTLD_NEXT, "rtl_uString_newFromAscii");
    release_string = dlsym(RTLD_NEXT, "rtl_uString_release");
    if (!original || !from_ascii || !release_string) {
        fputs("LibreOffice pipe compatibility: missing SAL symbols\n", stderr);
        abort();
    }
}

void *osl_createPipe(UString *name, int options, void *security) {
    pthread_once(&init_once, init_symbols);
    if (!name || name->length < 0 ||
        (size_t)name->length + PIPE_OVERHEAD <= sizeof(((struct sockaddr_un *)0)->sun_path))
        return original(name, options, security);
    /* The affected generated IDs are ASCII. Leave other pipe APIs untouched. */
    for (int32_t i = 0; i < name->length; ++i)
        if (name->buffer[i] > 127) return original(name, options, security);
    unsigned char digest[SHA256_DIGEST_LENGTH];
    SHA256((const unsigned char *)name->buffer, (size_t)name->length * 2, digest);
    char shortened[36] = "lo_";
    for (size_t i = 0; i < 16; ++i)
        snprintf(shortened + 3 + 2*i, 3, "%02x", digest[i]);
    UString *mapped = NULL;
    from_ascii(&mapped, shortened);
    void *result = original(mapped, options, security);
    release_string(mapped);
    return result;
}
