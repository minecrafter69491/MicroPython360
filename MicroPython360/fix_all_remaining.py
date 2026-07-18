"""
Comprehensive fix script for all remaining C++98 compilation errors.
Applies fixes based on the error log pattern analysis.
"""
import re
import os

PYROOT = r'C:\Users\Public\project\project\RealPyOS\MicroPython360\MicroPython360'

def fix_nargs_macros():
    """Fix C2078: remove 1 extra zero from NARGS_1 through NARGS_10 macros."""
    path = os.path.join(PYROOT, 'py', 'obj.h')
    with open(path, 'r') as f:
        data = f.read()
    # Count and fix: NARGS_N should have (12-N) zeros before '{ v'
    # Current has too many. Remove the last ', 0' before '{ v' for NARGS_1..10
    lines = data.split('\n')
    fixed = 0
    for i, line in enumerate(lines):
        m = re.search(r'MP_DEFINE_CONST_OBJ_TYPE_NARGS_(\d+)', line)
        if m:
            n = int(m.group(1))
            if 1 <= n <= 10:
                # Find last ', 0' before '{ v'
                brace_pos = line.find('{ v')
                if brace_pos == -1:
                    continue
                # Find the last ', 0' that appears before the brace
                before_brace = line[:brace_pos]
                last_zero = before_brace.rfind(', 0')
                if last_zero != -1:
                    # Verify it's a standalone ', 0' not part of a larger number
                    lines[i] = line[:last_zero] + line[last_zero + 3:]
                    fixed += 1
                    print(f'  Fixed NARGS_{n} at line {i+1}')
    if fixed:
        with open(path, 'w') as f:
            f.write('\n'.join(lines))
    print(f'obj.h: fixed {fixed} NARGS macros')

def fix_c2440_returns():
    """Fix C2440 'return': add explicit cast when returning MP_OBJ_TO_PTR."""
    # Pattern: return MP_OBJ_TO_PTR(expr); where function returns typed pointer
    files_to_check = {
        r'py\objexcept.c': {
            123: ('mp_obj_exception_t *', 'return MP_OBJ_TO_PTR(self_in)'),
            125: ('mp_obj_exception_t *', 'return MP_OBJ_TO_PTR(((mp_obj_instance_t *)MP_OBJ_TO_PTR(self_in))->subobj[0])'),
        },
    }
    for relpath, fixes in files_to_check.items():
        path = os.path.join(PYROOT, relpath)
        with open(path, 'r') as f:
            lines = f.readlines()
        for lineno, (cast_type, old_pattern) in fixes.items():
            idx = lineno - 1
            old = lines[idx].rstrip('\n')
            new = old.replace(old_pattern, f'return ({cast_type}){old_pattern[6:]}', 1)
            if new != old:
                lines[idx] = new + '\n'
                print(f'  {relpath}:{lineno} - added cast')
        with open(path, 'w') as f:
            f.writelines(lines)

def fix_c2440_initializing_type_mismatches():
    """Fix C2440 'initializing' from int/enum arithmetic mismatches."""
    # objexcept.c:165: mp_print_kind_t k = kind & ~PRINT_EXC_SUBCLASS
    path = os.path.join(PYROOT, r'py\objexcept.c')
    with open(path, 'r') as f:
        data = f.read()
    
    # Fix line 165: mp_print_kind_t k = kind & ~PRINT_EXC_SUBCLASS;
    old = 'mp_print_kind_t k = kind & ~PRINT_EXC_SUBCLASS;'
    new = 'mp_print_kind_t k = (mp_print_kind_t)(kind & ~PRINT_EXC_SUBCLASS);'
    if old in data:
        data = data.replace(old, new)
        print('  objexcept.c:165 - enum cast added')
    
    # Fix line 443: struct _exc_printer_t *pr = data; (void* to typed)
    old2 = 'struct _exc_printer_t *pr = data;'
    new2 = 'struct _exc_printer_t *pr = (struct _exc_printer_t *)data;'
    if old2 in data:
        data = data.replace(old2, new2)
        print('  objexcept.c:443 - pointer cast added')
    
    with open(path, 'w') as f:
        f.write(data)

def fix_c2676_enum_arith():
    """Fix C2676: mp_binary_op_t += """ 
    path = os.path.join(PYROOT, r'py\runtime.c')
    with open(path, 'r') as f:
        data = f.read()
    old = 'op += MP_BINARY_OP_OR - MP_BINARY_OP_INPLACE_OR;'
    new = 'op = (mp_binary_op_t)(op + (MP_BINARY_OP_OR - MP_BINARY_OP_INPLACE_OR));'
    if old in data:
        data = data.replace(old, new)
        print('  runtime.c:643 - enum += fixed')
    with open(path, 'w') as f:
        f.write(data)

def fix_c2466_zero_size_arrays():
    """Fix C2466: zero-size arrays when NO_QSTR defined."""
    path = os.path.join(PYROOT, r'py\qstr.c')
    with open(path, 'r') as f:
        data = f.read()
    
    # Lines 138, 149, 169: const foo_t bar[] = { #ifndef NO_QSTR ... #endif };
    # When NO_QSTR is defined, this becomes foo_t bar[0] = { };
    # Fix: add [0] or [1] to the array declaration... actually better to just
    # ensure there's always at least one element.
    
    # Fix 1: line ~131-139
    old1 = '''const qstr_hash_t mp_qstr_const_hashes[] = {
    #ifndef NO_QSTR
#define QDEF0(id, hash, len, str)
#define QDEF1(id, hash, len, str) hash,
    #include "genhdr/qstrdefs.generated.h"
#undef QDEF0
#undef QDEF1
    #endif
};'''
    new1 = '''#ifndef NO_QSTR
const qstr_hash_t mp_qstr_const_hashes[] = {
#define QDEF0(id, hash, len, str)
#define QDEF1(id, hash, len, str) hash,
    #include "genhdr/qstrdefs.generated.h"
#undef QDEF0
#undef QDEF1
};
#else
const qstr_hash_t mp_qstr_const_hashes[1] = {0};
#endif'''
    
    if old1 in data and False:  # disable - this changes structure too much
        pass
    
    # Simpler fix: use [1] instead of [] for all three arrays
    data = data.replace(
        'const qstr_hash_t mp_qstr_const_hashes[] = {',
        'const qstr_hash_t mp_qstr_const_hashes[1] = {'
    )
    data = data.replace(
        'const qstr_len_t mp_qstr_const_lengths[] = {',
        'const qstr_len_t mp_qstr_const_lengths[1] = {'
    )
    # For the pool array at line ~169, it's inside a struct member:
    # Actually let me check if the size matters here - the struct has MP_QSTRnumber_of elements
    # which could be 0 when NO_QSTR is defined.
    
    with open(path, 'w') as f:
        f.write(data)
    print('  qstr.c: arrays given size [1]')

def fix_c2664_param_casts():
    """Fix C2664: add explicit casts for function parameters."""
    fixes = {
        r'py\objstringio.c': [
            (197, 'vstr_init_fixed_buf(o->vstr, bufinfo.len, bufinfo.buf)',
                  'vstr_init_fixed_buf(o->vstr, bufinfo.len, (char *)bufinfo.buf)'),
        ],
        r'py\objarray.c': [
            (78, 'mp_str_print_quoted(print, bufinfo.buf, bufinfo.len)',
                 'mp_str_print_quoted(print, (const byte *)bufinfo.buf, bufinfo.len)'),
            (339, 'find_subbytes(needle_bufinfo.buf, haystack_bufinfo.buf, ...)'),  # too complex
            (373, 'mp_seq_cmp_bytes(...)'),  # too complex
        ],
        r'py\objint.c': [
            (58, 'mp_parse_num_integer(bufinfo.buf, ...)'),  # too complex
        ],
        r'py\emitglue.c': [
            (220, 'mp_obj_new_fun_bc(...)'),  # complex
        ],
        r'shared\runtime\pyexec.c': [
            (99, 'qstr_from_str(source)'),  # might be fine
        ],
    }
    # Most C2664 fixes require context, let me handle the simpler ones
    path = os.path.join(PYROOT, r'py\objstringio.c')
    with open(path, 'r') as f:
        data = f.read()
    old = 'vstr_init_fixed_buf(o->vstr, bufinfo.len, bufinfo.buf);'
    new = 'vstr_init_fixed_buf(o->vstr, bufinfo.len, (char *)bufinfo.buf);'
    if old in data:
        data = data.replace(old, new)
        print('  objstringio.c:197 - void* to char* cast')
    with open(path, 'w') as f:
        f.write(data)
    
    # objset.c:410,420: set_update_int(self, ...) 
    path = os.path.join(PYROOT, r'py\objset.c')
    with open(path, 'r') as f:
        data = f.read()
    data = data.replace(
        'set_update_int(self_in, set_update_int, args[1]);',
        'set_update_int((mp_obj_set_t *)self_in, set_update_int, args[1]);'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  objset.c - cast self_in')

def fix_c2664_enum_params():
    """Fix C2664: enum parameter mismatches in function calls."""
    # vm.c:1293: mp_unary_op(ip[-1] - MP_BC_UNARY_OP_MULTI, TOP())
    path = os.path.join(PYROOT, r'py\vm.c')
    with open(path, 'r') as f:
        data = f.read()
    
    # Line 1293
    old = 'SET_TOP(mp_unary_op(ip[-1] - MP_BC_UNARY_OP_MULTI, TOP()));'
    new = 'SET_TOP(mp_unary_op((mp_unary_op_t)(ip[-1] - MP_BC_UNARY_OP_MULTI), TOP()));'
    if old in data:
        data = data.replace(old, new)
        print('  vm.c:1293 - mp_unary_op_t cast')
    
    # Line 1298: mp_binary_op(...)
    old2 = 'SET_TOP(mp_binary_op(ip[-1] - MP_BC_BINARY_OP_MULTI, lhs, rhs));'
    new2 = 'SET_TOP(mp_binary_op((mp_binary_op_t)(ip[-1] - MP_BC_BINARY_OP_MULTI), lhs, rhs));'
    if old2 in data:
        data = data.replace(old2, new2)
        print('  vm.c:1298 - mp_binary_op_t cast')
    
    with open(path, 'w') as f:
        f.write(data)
    
    # modbuiltins.c:261,281: mp_binary_op((mp_uint_t)op, ...)
    path = os.path.join(PYROOT, r'py\modbuiltins.c')
    with open(path, 'r') as f:
        data = f.read()
    data = data.replace(
        'ret = mp_binary_op((mp_uint_t)op, lhs, rhs);',
        'ret = mp_binary_op((mp_binary_op_t)(mp_uint_t)op, lhs, rhs);'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  modbuiltins.c:261,281 - mp_binary_op_t cast')

def fix_c2440_assignments():
    """Fix C2440 '=' and 'initializing' with explicit casts at key sites."""
    # These are individual patterns that need explicit casts.
    # Rather than doing each one manually, let's handle the systematic ones.
    
    # nlrsetjmp.c:32, pystack.c:34-36 - m_malloc results
    for relpath, lines_to_fix in [
        (r'py\nlrsetjmp.c', {32: 'nLR_buf_t'}),
        (r'py\pystack.c', {34: 'uint8_t', 35: 'uint8_t', 36: 'uint8_t'}),
    ]:
        path = os.path.join(PYROOT, relpath)
        with open(path, 'r') as f:
            content = f.read()
        print(f'  {relpath} - needs manual cast review')

def fix_c2065_undef():
    """Fix C2065: add missing defines."""
    # MICROPY_REGISTERED_MODULES and MICROPY_REGISTERED_EXTENSIBLE_MODULES
    # These should be defined in the generated code or config
    path = os.path.join(PYROOT, r'py\objmodule.c')
    with open(path, 'r') as f:
        data = f.read()
    
    # Add defines before their first use if not present
    if 'MICROPY_REGISTERED_MODULES' in data and not re.search(r'#define MICROPY_REGISTERED_MODULES', data):
        # Add just before the first use
        data = data.replace(
            '#if MICROPY_MODULE_BUILTIN_INIT',
            '#ifndef MICROPY_REGISTERED_MODULES\n#define MICROPY_REGISTERED_MODULES\n#endif\n#ifndef MICROPY_REGISTERED_EXTENSIBLE_MODULES\n#define MICROPY_REGISTERED_EXTENSIBLE_MODULES\n#endif\n\n#if MICROPY_MODULE_BUILTIN_INIT'
        )
        print('  objmodule.c: added missing #defines')
    with open(path, 'w') as f:
        f.write(data)
    
    # CHAR_CTRL_* - need to add defines in pyexec.c or a header
    path = os.path.join(PYROOT, r'shared\runtime\pyexec.c')
    with open(path, 'r') as f:
        data = f.read()
    if 'CHAR_CTRL_C' in data and not re.search(r'#define CHAR_CTRL_', data):
        # Add defines after existing includes
        data = data.replace(
            '#include <string.h>',
            '#include <string.h>\n\n// C++98 port: CHAR_CTRL defines\n#ifndef CHAR_CTRL_A\n#define CHAR_CTRL_A (1)\n#define CHAR_CTRL_B (2)\n#define CHAR_CTRL_C (3)\n#define CHAR_CTRL_D (4)\n#define CHAR_CTRL_E (5)\n#endif\n'
        )
        print('  pyexec.c: added CHAR_CTRL_* defines')
    with open(path, 'w') as f:
        f.write(data)

def fix_c2086_redefinition():
    """Fix C2086: remove duplicate type definitions in objdict.c."""
    path = os.path.join(PYROOT, r'py\objdict.c')
    with open(path, 'r') as f:
        data = f.read()
    
    # Check if there are duplicate definitions of mp_type_dict_view_it and mp_type_dict_view
    # Lines 477 and 540
    # This suggests the types are defined twice. Let me check.
    count_it = data.count('mp_type_dict_view_it')
    count_view = data.count('mp_type_dict_view')
    if count_it > 1:
        print(f'  objdict.c: mp_type_dict_view_it appears {count_it} times - check for duplicate')
    if count_view > 1:
        print(f'  objdict.c: mp_type_dict_view appears {count_view} times - check for duplicate')

def fix_c2143_compound_literals():
    """Fix C2143/C2059: syntax errors in objtype.c (compound literals)."""
    path = os.path.join(PYROOT, r'py\objtype.c')
    with open(path, 'r') as f:
        lines = f.readlines()
    
    # Lines 1291 and 1481 have syntax errors with { } 
    # Likely compound literal {0} used to zero-initialize a struct
    # In C++98, replace {0} with an actual value or memset
    
    for lineno in [1291, 1481]:
        idx = lineno - 1
        if idx < len(lines):
            old = lines[idx]
            print(f'  objtype.c:{lineno}: {old.rstrip()}')
    
    # Look for the specific pattern at these lines
    # This likely involves a struct initialization with {0}
    # Check if there's a compound literal pattern
    
    data = ''.join(lines)
    # Common pattern in MicroPython: mp_obj_type_t type = {0};
    # In C++98 this needs to be: mp_obj_type_t type = {{0}}; or use memset
    # Actually compound literal (type){0} is C99; in C++98 use explicit init
    
    # Let me look at the specific lines
    for i, line in enumerate(lines):
        if i >= 1285 and i <= 1295:
            print(f'  Line {i+1}: {line.rstrip()}')
        if i >= 1475 and i <= 1485:
            print(f'  Line {i+1}: {line.rstrip()}')


def fix_mp_tagptr():
    """Fix MP_TAGPTR_PTR returning void* needing explicit cast."""
    for relpath in [r'py\vm.c']:
        path = os.path.join(PYROOT, relpath)
        with open(path, 'r') as f:
            data = f.read()
        
        # vm.c:1109: mp_obj_t *finally_sp = MP_TAGPTR_PTR(exc_sp->val_sp);
        data = data.replace(
            'mp_obj_t *finally_sp = MP_TAGPTR_PTR(exc_sp->val_sp);',
            'mp_obj_t *finally_sp = (mp_obj_t *)MP_TAGPTR_PTR(exc_sp->val_sp);'
        )
        # vm.c:1453: mp_obj_t *sp = MP_TAGPTR_PTR(exc_sp->val_sp);
        data = data.replace(
            'mp_obj_t *sp = MP_TAGPTR_PTR(exc_sp->val_sp);',
            'mp_obj_t *sp = (mp_obj_t *)MP_TAGPTR_PTR(exc_sp->val_sp);'
        )
        with open(path, 'w') as f:
            f.write(data)
        print(f'  {relpath}: MP_TAGPTR_PTR casts added')

def fix_runtime_casts():
    """Fix C2440 initializing in runtime.c for nlr_jump_callback_node types."""
    path = os.path.join(PYROOT, r'py\runtime.c')
    with open(path, 'r') as f:
        data = f.read()
    
    # Line 200: nlr_jump_callback_node_globals_locals_t *ctx = ctx_in;
    data = data.replace(
        'nlr_jump_callback_node_globals_locals_t *ctx = ctx_in;',
        'nlr_jump_callback_node_globals_locals_t *ctx = (nlr_jump_callback_node_globals_locals_t *)ctx_in;'
    )
    # Line 206: nlr_jump_callback_node_call_function_1_t *ctx = ctx_in;
    data = data.replace(
        'nlr_jump_callback_node_call_function_1_t *ctx = ctx_in;',
        'nlr_jump_callback_node_call_function_1_t *ctx = (nlr_jump_callback_node_call_function_1_t *)ctx_in;'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  runtime.c:200,206 - void* casts')

def fix_builtinimport_casts():
    """Fix builtinimport.c void* casts."""
    path = os.path.join(PYROOT, r'py\builtinimport.c')
    with open(path, 'r') as f:
        data = f.read()
    
    data = data.replace(
        'nlr_jump_callback_node_unregister_module_t *ctx = ctx_in;',
        'nlr_jump_callback_node_unregister_module_t *ctx = (nlr_jump_callback_node_unregister_module_t *)ctx_in;'
    )
    data = data.replace(
        'do_load_from_lexer(lex, ...)',
        'do_load_from_lexer((mp_lexer_t *)lex, ...)'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  builtinimport.c: void* casts')

def fix_emitbc_casts():
    """Fix emitbc.c void* initializing emit_t*."""
    path = os.path.join(PYROOT, r'py\emitbc.c')
    with open(path, 'r') as f:
        data = f.read()
    data = data.replace(
        'emit_t *emit = m_new0(emit_t, 1);',
        'emit_t *emit = (emit_t *)m_new0(emit_t, 1);'
    )
    data = data.replace(
        'emit_t *emit = m_new(emit_t, 1);',
        'emit_t *emit = (emit_t *)m_new(emit_t, 1);'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  emitbc.c: void* casts')

def fix_vm_additional_casts():
    """Fix vm.c additional C2440 errors."""
    path = os.path.join(PYROOT, r'py\vm.c')
    with open(path, 'r') as f:
        data = f.read()
    
    # exc_sp->prev_exc = nlr.ret_val;  (nlr.ret_val is void*)
    data = data.replace(
        'exc_sp->prev_exc = nlr.ret_val;',
        'exc_sp->prev_exc = (mp_obj_t)nlr.ret_val;'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  vm.c:1455 void* to mp_obj_t cast')

def fix_objstr_casts():
    """Fix objstr.c C2440 and C2664 errors."""
    path = os.path.join(PYROOT, r'py\objstr.c')
    with open(path, 'r') as f:
        data = f.read()
    
    # Line 271: mp_obj_new_bytes(bufinfo.buf, bufinfo.len)
    data = data.replace(
        'mp_obj_new_bytes(bufinfo.buf, bufinfo.len)',
        'mp_obj_new_bytes((const byte *)bufinfo.buf, bufinfo.len)'
    )
    # Line 210: mp_obj_new_str(bufinfo.buf, bufinfo.len)
    data = data.replace(
        'mp_obj_new_str(bufinfo.buf, bufinfo.len, false)',
        'mp_obj_new_str((const char *)bufinfo.buf, bufinfo.len, false)'
    )
    # Line 401: self->data = bufinfo.buf;
    data = data.replace(
        'self->data = bufinfo.buf;',
        'self->data = (const byte *)bufinfo.buf;'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  objstr.c: void* casts')

def fix_misc_additional():
    """Fix other misc errors."""
    # emitglue.c:195 - mp_proto_fun_t to const mp_raw_code_t*
    path = os.path.join(PYROOT, r'py\emitglue.c')
    with open(path, 'r') as f:
        data = f.read()
    data = data.replace(
        'const mp_raw_code_t *rc = proto_fun;',
        'const mp_raw_code_t *rc = (const mp_raw_code_t *)proto_fun;'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  emitglue.c:195 - proto_fun cast')
    
    # objint.c:412 - mp_obj_int_from_bytes_impl needs byte* cast
    path = os.path.join(PYROOT, r'py\objint.c')
    with open(path, 'r') as f:
        data = f.read()
    data = data.replace(
        'mp_obj_int_from_bytes_impl(false, bufinfo.len, bufinfo.buf)',
        'mp_obj_int_from_bytes_impl(false, bufinfo.len, (const byte *)bufinfo.buf)'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  objint.c:412 - byte* cast')
    
    # shared/runtime/sys_stdio_mphal.c - void* to sys_stdio_obj_t*
    path = os.path.join(PYROOT, r'shared\runtime\sys_stdio_mphal.c')
    with open(path, 'r') as f:
        data = f.read()
    data = data.replace(
        'sys_stdio_obj_t *self = MP_OBJ_TO_PTR(self_in);',
        'sys_stdio_obj_t *self = (sys_stdio_obj_t *)MP_OBJ_TO_PTR(self_in);'
    )
    with open(path, 'w') as f:
        f.write(data)
    print('  sys_stdio_mphal.c - self cast')


def fix_compile_parse_enum_casts():
    """Fix C2440 for uintptr_t/int → mp_token_kind_t in compile.c and parse.c."""
    for relpath in [r'py\compile.c', r'py\parse.c']:
        path = os.path.join(PYROOT, relpath)
        with open(path, 'r') as f:
            data = f.read()
        
        # Replace 'uintptr_t' initializing mp_token_kind_t
        # Pattern: mp_token_kind_t tok = MP_TOKEN_KINDA(rule_id);
        # or: mp_token_kind_t tok = rule_id;
        # These need explicit casts
        
        # Generic approach: find lines that assign to mp_token_kind_t from non-enum types
        # But this is risky; let me handle specific known patterns
        
        # compile.c:2042,2215,2274,2282,2288
        # parse.c:758,784,790
        
        # Specific pattern in compile.c: 
        # mp_token_kind_t tok = arg; where arg is uintptr_t
        
        # This is too broad. Instead, let me search for known patterns
        old = 'mp_token_kind_t tok = '
        new = 'mp_token_kind_t tok = (mp_token_kind_t)'
        
        # Only fix specific lines. Too risky to do bulk. 
        print(f'  {relpath} - enum casts need manual review')


print('=== Fixing all remaining C++98 compatibility issues ===')
fix_nargs_macros()
fix_c2440_returns()
fix_c2440_initializing_type_mismatches()
fix_c2676_enum_arith()
fix_c2664_enum_params()
fix_mp_tagptr()
fix_runtime_casts()
fix_builtinimport_casts()
fix_emitbc_casts()
fix_vm_additional_casts()
fix_objstr_casts()
fix_misc_additional()
fix_c2664_param_casts()
fix_c2065_undef()
print('\n=== Done. Some errors may still need manual fixes. ===')
