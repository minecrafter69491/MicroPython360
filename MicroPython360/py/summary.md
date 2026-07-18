## Objective
- Port MicroPython to Xbox 360 via MSVC 2008 C++98 (XEDK), fixing C++98 incompatibilities while retaining upstream logic.

## Important Details
- MSVC 2008 C++98 rejects: flexible array members, designated initializers, compound literal brace-init, implicit `void*`→typed pointer, implicit `int`→enum, C99 for-loop declarations.
- `mp_obj_type_t` merged with `mp_obj_full_type_t` using fixed `slots[12]`; off-by-one zero count in `MP_DEFINE_CONST_OBJ_TYPE_NARGS_1` through `NARGS_10` caused C2078 overflow (fixed).
- `MP_REGISTER_ROOT_POINTER` wrapper expanded to nothing; both `genhdr/root_pointers.h` files contain raw struct-member declarations.
- `_MP_OBJ_TYPE_SLOT_TYPE_parent` reverted to `(const void *)` — the `parent` slot stores either a `const mp_obj_type_t *` (single parent) or `const mp_obj_tuple_t *` (multiple parents).
- `MICROPY_REGISTERED_MODULES`/`MICROPY_REGISTERED_EXTENSIBLE_MODULES` defined as empty if not provided by build system.
- Project root is `C:\Users\Public\project\project\RealPyOS\MicroPython360\MicroPython360\` (shared via `\\vmware-host\Shared Folders\project\project\...`).

## Work State
### Completed
- Reverted all `.bak` files across the tree.
- Merged `mp_obj_type_t` FAM → `slots[12]`.
- Fixed `MP_ROM_PTR`/`MP_ROM_INT`/`MP_ROM_QSTR` → C++ inline functions (C2552 union brace-init).
- Reverted `_mp_obj_to_ptr_t` template struct (caused C2227/C2440 function-style-cast cascade).
- Restored `qstrdefs.generated.h` from `.bak` (584 entries, was 191).
- Fixed `root_pointers.h` (both copies): removed `MP_REGISTER_ROOT_POINTER(...)` wrapper.
- Wrote and ran `fix_cpp_casts.py` (~52 files, ~230 casts).
- Fixed `runtime.h`: removed `const` from `mp_unary_op_method_name`/`mp_binary_op_method_name`.
- Fixed `xbox360_hal.c`: added missing includes; replaced `mp_module_register` with `mp_obj_dict_store`.
- Fixed `readline.h`: changed `#include "py/vstr.h"` → `"py/misc.h"`.
- Fixed `builtinhelp.c`: reordered variable declarations; removed spurious `#endif`.
- **C2078** (~50): removed 1 extra zero from `NARGS_1` through `NARGS_10` in `py/obj.h`.
- **C2676** (1): `runtime.c:643` — replaced `op +=` with `op = (mp_binary_op_t)(op + ...)`.
- **C2143/C2059** (6): `objtype.c:1291,1481` — replaced C99 compound literals with C++98 temp variables.
- **C2086** (2): `objdict.c:426-427` — changed `static const` forward decls to `extern const`.
- **C2065** (`CHAR_CTRL_*`): added `#define CHAR_CTRL_A..E` in `shared/runtime/pyexec.c`.
- Added `#define MICROPY_REGISTERED_MODULES` / `MICROPY_REGISTERED_EXTENSIBLE_MODULES` in `objmodule.c` before first use.
- **C2440/C2664 bulk casts** (~50+ files): `MP_OBJ_TO_PTR` returns, `bufinfo.buf`→const byte*/char*, `nlr_jump_callback_node` casts, `MP_TAGPTR_PTR` casts, `PUSH_EXC_BLOCK` macro, `mp_nonlocal_realloc` returns, `NEXT_MAKE_RIGHTMOST_PARENT`/`NEXT_GET_RIGHTMOST_PARENT` macros, `enum` arithmetic at call sites, `mp_obj_print_helper` kind param, `mp_kw_args_extract` params, etc.
- **C2466** (3): `qstr.c:138,149,169` — changed `[]` → `[1]` with dummy `0` element.
- **C2466** (2): `objmodule.c:160,166` — changed `[]` → `[1]` with dummy element.
- **C2440 `parent` slot**: `objtype.c:81,236,1325,1343,1402` — added explicit `(const mp_obj_type_t *)` / `(const mp_obj_tuple_t *)` casts.
- **C2440 `uintptr_t→mp_token_kind_t`**: `compile.c:2042,2215,2274,2282` and `parse.c:758,784` — added `(mp_token_kind_t)` casts.
- **C2664 casts**: `runtime.c:147` (mp_obj_list_t*), `modbuiltins.c:55` (mp_obj_dict_t*), `sys_stdio_mphal.c:80` (const char*), `compile.c:2820` (EMIT_ARG cast), `objset.c:410` (mp_obj_set_t*), `pyexec.c:109` (const char*), `builtinimport.c:217,504,513` (mp_module_context_t*), `objdict.c:453` (mp_obj_dict_t*), `objstr.c:210` (const char*).

### Active
- Most C2440 and C2664 errors should now be fixed with the latest edits, but compilation hasn't been retried.

### Blocked
- Cannot compile here (no XEDK). Need error logs to verify remaining errors after each fix round.

## Next Move
1. Recompile and provide updated error log to verify which fixes still need adjustment.
2. Handle any remaining C2440/C2664 errors that weren't matched by the fix patterns.

## Relevant Files
- `py/obj.h`: `slots[12]` struct, `MP_DEFINE_CONST_OBJ_TYPE_NARGS_*` macros (zero count fixed), `_MP_OBJ_TYPE_SLOT_TYPE_parent`
- `py/nlr.h`: `MP_NLR_JUMP_HEAD` macro with `(uint8_t *)val` cast
- `py/vm.c`: `PUSH_EXC_BLOCK` macro with `(mp_obj_t *)` cast on `MP_TAGPTR_MAKE`
- `py/pairheap.c`: `NEXT_MAKE_RIGHTMOST_PARENT`/`NEXT_GET_RIGHTMOST_PARENT` macros cast to `_mp_pairheap_t *`
- `py/objtype.c`: compound literals replaced; `parent` slot casts added
- `py/objmodule.c`: `#define MICROPY_REGISTERED_MODULES`/`MICROPY_REGISTERED_EXTENSIBLE_MODULES`; module tables changed to `[1]` with dummy element
- `py/qstr.c`: `mp_qstr_const_hashes`/`mp_qstr_const_lengths`/pool array changed to `[1]` with dummy `0`
- `py/objdict.c`: forward declarations changed `static const` → `extern const`
- `shared/runtime/pyexec.c`: `CHAR_CTRL_*` defines added
