#include <stdint.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <errno.h>
#include <time.h>

// PowerPC (Xbox 360) is big-endian; define this early so
// py/mpconfig.h skips the endian.h include that doesn't exist
// on the Xbox 360 SDK.
#define MP_ENDIANNESS_LITTLE        (0)

// Override NORETURN for MSVC — py/mpconfig.h unconditionally defines
// it as __attribute__((noreturn)) which the Xbox 360 compiler doesn't support.
#define NORETURN __declspec(noreturn)

#define MICROPY_FLOAT_USE_NATIVE_FLT16 (0)

// MSVC in Xbox 360 SDK has no __attribute__ support at all; neuter it.
#define __attribute__(x)

// MSVC doesn't support C99 restrict keyword.
#define restrict

// MSVC uses __declspec(noinline) instead of __attribute__((noinline)).
// Must be defined BEFORE py/mpconfig.h processes MP_NOINLINE at line 2079.
#ifndef MP_NOINLINE
#define MP_NOINLINE __declspec(noinline)
#endif

#define inline __inline

// MSVC doesn't have __builtin_expect; just evaluate the expression.
#ifndef MP_LIKELY
#define MP_LIKELY(x)   (x)
#endif
#ifndef MP_UNLIKELY
#define MP_UNLIKELY(x) (x)
#endif

// Old MSVC (2005/2008) doesn't have C11/C++11 alignof.
// Use MSVC's __alignof intrinsic instead.
#ifndef alignof
#define alignof __alignof
#endif

// Some MicroPython source files use __builtin_expect directly.
// Provide a fallback for MSVC which doesn't have GCC builtins.
#ifndef __builtin_expect
#define __builtin_expect(x, val) (x)
#endif

// Xbox 360 (PowerPC) has no architecture-specific gc helper,
// so use the portable setjmp-based implementation.
#ifndef MICROPY_GCREGS_SETJMP
#define MICROPY_GCREGS_SETJMP (1)
#endif

#ifndef __cplusplus
typedef unsigned char bool;
#define true 1
#define false 0
#endif

// Enable full Unicode; uses uint32_t for unichar (stdint.h is available)
// instead of the fallback 'typedef uint unichar' which fails on MSVC.
#define MICROPY_PY_BUILTINS_STR_UNICODE (1)

#define MICROPY_ENABLE_COMPILER     (1)
#define MICROPY_QSTR_EXTRA_POOL     mp_qstr_const_pool
#define MICROPY_ALLOC_PATH_MAX      (256)
#define MICROPY_EMIT_X64            (0)
#define MICROPY_EMIT_THUMB          (0)
#define MICROPY_EMIT_INLINE_THUMB   (0)
#define MICROPY_EMIT_ARM            (0)
#define MICROPY_EMIT_XTENSA         (0)
#define MICROPY_EMIT_INLINE_XTENSA  (0)
#define MICROPY_COMP_MODULE_CONST   (0)
#define MICROPY_COMP_CONST          (0)
#define MICROPY_COMP_DOUBLE_TUPLE_ASSIGN (0)
#define MICROPY_COMP_TRIPLE_TUPLE_ASSIGN (0)
#define MICROPY_MEM_STATS           (0)
#define MICROPY_DEBUG_PRINTERS      (1)
#define MICROPY_ENABLE_GC           (1)
#define MICROPY_STACK_CHECK         (1)
#define MICROPY_GC_ALLOC_THRESHOLD  (0)
#define MICROPY_REPL_EVENT_DRIVEN   (0)
#define MICROPY_HELPER_REPL         (1)
#define MICROPY_HELPER_LEXER_UNIX   (0)
#define MICROPY_ENABLE_SOURCE_LINE  (1)
#define MICROPY_ENABLE_DOC_STRING   (0)
#define MICROPY_ERROR_REPORTING     (MICROPY_ERROR_REPORTING_TERSE)
#define MICROPY_BUILTIN_METHOD_CHECK_SELF_ARG (0)
#define MICROPY_PY_ASYNC_AWAIT      (0)
#define MICROPY_MODULE_BUILTIN_INIT         (1)
#define MICROPY_PY_BUILTINS_BYTEARRAY (1)
#define MICROPY_PY_BUILTINS_DICT_FROMKEYS (1)
#define MICROPY_PY_BUILTINS_MEMORYVIEW (1)
#define MICROPY_PY_BUILTINS_ENUMERATE (1)
#define MICROPY_PY_BUILTINS_FILTER  (1)
#define MICROPY_PY_BUILTINS_FROZENSET (1)
#define MICROPY_PY_BUILTINS_REVERSED (1)
#define MICROPY_PY_BUILTINS_SET     (1)
#define MICROPY_PY_BUILTINS_SLICE   (1)
#define MICROPY_PY_BUILTINS_PROPERTY (1)
#define MICROPY_PY_BUILTINS_MIN_MAX (1)
#define MICROPY_PY_BUILTINS_STR_COUNT (1)
#define MICROPY_PY_BUILTINS_STR_OP_MODULO (1)
#define MICROPY_PY_BUILTINS_HELP    (1)
#define MICROPY_PY_BUILTINS_HELP_MODULES (1)
#define MICROPY_PY___FILE__         (0)
#define MICROPY_PY_GC               (1)
#define MICROPY_PY_ARRAY            (1)
#define MICROPY_PY_COLLECTIONS      (1)
#define MICROPY_PY_MATH             (0)
#define MICROPY_PY_CMATH            (0)
#define MICROPY_PY_IO               (1)
#define MICROPY_PY_STRUCT           (1)
#define MICROPY_PY_SYS              (1)
#define MICROPY_MODULE_FROZEN_MPY   (0)
#define MICROPY_CPYTHON_COMPAT      (0)
#define MICROPY_LONGINT_IMPL        (MICROPY_LONGINT_IMPL_MPZ)
#define MICROPY_FLOAT_IMPL          (MICROPY_FLOAT_IMPL_NONE)
#define MICROPY_ENABLE_PYSTACK      (1)
#define MICROPY_USE_INTERNAL_PRINTF (1)
#ifndef MICROPY_NLR_SETJMP
#define MICROPY_NLR_SETJMP          (1)
#endif
#define MICROPY_PY_USOCKET          (1)
#define MICROPY_PY_NETWORK          (1)

#define MICROPY_VFS                 (0)
#define MICROPY_PY_JSON             (1)
#define MICROPY_PY_SYS_PLATFORM     "xbox360"

#define MICROPY_MODULE_FROZEN       (0)
#define MICROPY_MODULE_FROZEN_STR   (0)

#define MICROPY_GIT_TAG "v1.24.0"
#define MICROPY_GIT_HASH "0000000"
#define MICROPY_BUILD_DATE "2026-07-16"

#define MICROPY_HW_BOARD_NAME "Xbox 360 PyOS"
#define MICROPY_HW_MCU_NAME "Xenon PowerPC"

#define UINT_FMT "%u"
#define INT_FMT "%d"
typedef int mp_int_t;
typedef unsigned int mp_uint_t;
typedef int mp_off_t;

#define MICROPY_PORT_BUILTINS \
    { MP_ROM_QSTR(MP_QSTR_open), MP_ROM_PTR(&mp_builtin_open_obj) },

#define MP_STATE_PORT MP_STATE_VM

#define MICROPY_MAKE_POINTER_CALLABLE(p) ((void *)((mp_uint_t)(p) | 1))

