"""
Pass 2: Comprehensive fix for remaining C2440, C2664, C2466, C2143, C2086, C2065 errors.
Handles void*→typed* casts, int→enum casts, function parameter casts, and misc issues.
"""
import re, os

PYROOT = r'C:\Users\Public\project\project\RealPyOS\MicroPython360\MicroPython360'

def fix_file(relpath, line_fixes):
    """Apply dict of {lineno: (old_substring, new_substring)} to a file."""
    path = os.path.join(PYROOT, relpath)
    with open(path, 'r') as f:
        data = f.read()
    for lineno, (old, new) in sorted(line_fixes.items(), reverse=True):
        if old in data:
            data = data.replace(old, new, 1)
            print(f'  {relpath}:{lineno} fixed')
        else:
            # Try line-specific approach
            lines = data.split('\n')
            idx = lineno - 1
            if idx < len(lines) and old in lines[idx]:
                lines[idx] = lines[idx].replace(old, new, 1)
                data = '\n'.join(lines)
                print(f'  {relpath}:{lineno} fixed (line match)')
            else:
                print(f'  {relpath}:{lineno} COULD NOT FIND: {old[:60]}')
    with open(path, 'w') as f:
        f.write(data)

def fix_all():
    # ---- C2664 function parameter conversions ----
    
    # objset.c:410,420 - set_update_int(self_in, ...)
    fix_file(r'py\objset.c', {
        410: ('set_update_int(self_in,', 'set_update_int((mp_obj_set_t *)self_in,'),
        420: ('set_update_int(self_in,', 'set_update_int((mp_obj_set_t *)self_in,'),
    })
    
    # pyexec.c:109 - qstr_from_str(source) where source is void*
    fix_file(r'shared\runtime\pyexec.c', {
        109: ('qstr_from_str(source)', 'qstr_from_str((const char *)source)'),
    })
    
    # objarray.c:78 - mp_str_print_quoted(print, bufinfo.buf, bufinfo.len)
    fix_file(r'py\objarray.c', {
        78: ('mp_str_print_quoted(print, bufinfo.buf, bufinfo.len)',
             'mp_str_print_quoted(print, (const byte *)bufinfo.buf, bufinfo.len)'),
        339: ('find_subbytes(needle_bufinfo.buf,', 'find_subbytes((const byte *)needle_bufinfo.buf,'),
        373: ('mp_seq_cmp_bytes(needle_bufinfo.buf,', 'mp_seq_cmp_bytes((const byte *)needle_bufinfo.buf,'),
    })
    
    # objint.c:58 - mp_parse_num_integer(bufinfo.buf, ...)
    fix_file(r'py\objint.c', {
        58: ('mp_parse_num_integer(bufinfo.buf,', 'mp_parse_num_integer((const char *)bufinfo.buf,'),
        412: ('mp_obj_int_from_bytes_impl(false, bufinfo.len, bufinfo.buf') ,  # already fixed
    })
    
    # objtype.c:270 - mp_obj_print_helper(print, o, kind)
    fix_file(r'py\objtype.c', {
        270: ('mp_obj_print_helper(print, o, kind)', 
              'mp_obj_print_helper(print, o, (mp_print_kind_t)kind)'),
    })
    
    # objstr.c:210 - mp_obj_new_str(bufinfo.buf, bufinfo.len, false)
    fix_file(r'py\objstr.c', {
        210: ('mp_obj_new_str(bufinfo.buf, bufinfo.len, false)',
              'mp_obj_new_str((const char *)bufinfo.buf, bufinfo.len, false)'),
    })
    
    # emitglue.c:220 - mp_obj_new_fun_bc(.., proto_fun, ..)
    fix_file(r'py\emitglue.c', {
        220: ('mp_obj_new_fun_bc(scope, proto_fun, def_args, def_kw_args)',
              'mp_obj_new_fun_bc(scope, (const byte *)proto_fun, def_args, def_kw_args)'),
    })
    
    # runtime.c:147 - mp_obj_list_init(o, ...)
    fix_file(r'py\runtime.c', {
        147: ('mp_obj_list_init(o,', 'mp_obj_list_init((mp_obj_list_t *)o,'),
    })
    
    # modbuiltins.c:55 - mp_locals_set(...)
    fix_file(r'py\modbuiltins.c', {
        55: ('mp_locals_set(dict)', 'mp_locals_set((mp_obj_dict_t *)dict)'),
    })
    
    # builtinevex.c:158 - mp_lexer_new_from_str_len(...)
    fix_file(r'py\builtinevex.c', {
        158: ('mp_lexer_new_from_str_len(mp_lexer_new_from_str_len('),
    })  # complex, needs manual check
    
    # sys_stdio_mphal.c:80 - mp_hal_stdout_tx_strn_cooked(stream->str, ...)
    fix_file(r'shared\runtime\sys_stdio_mphal.c', {
        80: ('mp_hal_stdout_tx_strn_cooked(stream->str,',
             'mp_hal_stdout_tx_strn_cooked((const char *)stream->str,'),
    })
    
    # compile.c:2820 - mp_emit_bc_load_const_tok(emit, tok)
    fix_file(r'py\compile.c', {
        2820: ('mp_emit_bc_load_const_tok(emit, tok)',
               'mp_emit_bc_load_const_tok(emit, (mp_token_kind_t)tok)'),
    })
    
    # modbuiltins.c:261,281 - mp_binary_op((mp_uint_t)op, ...)
    # Already fixed in pass 1
    
    # sequence.c:164 - mp_binary_op(op, ...) where op is mp_uint_t
    fix_file(r'py\sequence.c', {
        164: ('mp_binary_op(op,', 'mp_binary_op((mp_binary_op_t)op,'),
    })
    
    # builtinimport.c:217 - do_load_from_lexer(lex, ...)
    fix_file(r'py\builtinimport.c', {
        217: ('do_load_from_lexer(lex,', 'do_load_from_lexer((mp_lexer_t *)lex,'),
        504: ('do_load(lex,', 'do_load((mp_module_context_t *)lex,'),
        513: ('do_load(lex,', 'do_load((mp_module_context_t *)lex,'),
    })
    
    # objdict.c:453 - dict_iter_next(self, ...)
    fix_file(r'py\objdict.c', {
        453: ('dict_iter_next(self,', 'dict_iter_next((mp_obj_dict_t *)self,'),
    })
    
    # ---- C2466 zero-size arrays ----
    # qstr.c:138,149,169 - arrays with NO_QSTR producing [0] size
    # Replace [] with [1] for these 3 arrays
    fix_file(r'py\qstr.c', {
        138: ('const qstr_hash_t mp_qstr_const_hashes[]',
              'const qstr_hash_t mp_qstr_const_hashes[1]'),
        149: ('const qstr_len_t mp_qstr_const_lengths[]',
              'const qstr_len_t mp_qstr_const_lengths[1]'),
        169: ('// corresponds to number of strings in array just below\n    ],',
              '// corresponds to number of strings in array just below\n    [1],'),
    })
    
    # ---- C2440 initializing void*→typed* ----
    # objtype.c:1309 - mp_obj_instance_t *self = MP_OBJ_TO_PTR(self_in);
    fix_file(r'py\objtype.c', {
        1309: ('mp_obj_instance_t *self = MP_OBJ_TO_PTR(self_in);',
               'mp_obj_instance_t *self = (mp_obj_instance_t *)MP_OBJ_TO_PTR(self_in);'),
    })
    
    # emitbc.c:96,147 - emit_t *emit = m_new0(emit_t, 1);
    # m_new0 already casts - let me check what's actually there
    # These might be from m_new_obj_var or similar
    
    # modstruct.c:135 - byte *buf = (byte *)...  (already has cast?)
    # stream.c:47 - byte *buf = (some void*)
    fix_file(r'py\stream.c', {
        47: ('const mp_stream_p_t *stream_p = MP_OBJ_TO_PTR(obj);', ''),
    })
    
    # compile.c:2042,2215,2274,2282 - mp_token_kind_t tok = rule_id;
    fix_file(r'py\compile.c', {
        2042: ('mp_token_kind_t tok = ', 'mp_token_kind_t tok = (mp_token_kind_t)'),
        2215: ('mp_token_kind_t tok = ', 'mp_token_kind_t tok = (mp_token_kind_t)'),
        2274: ('mp_token_kind_t tok = ', 'mp_token_kind_t tok = (mp_token_kind_t)'),
        2282: ('mp_token_kind_t tok = ', 'mp_token_kind_t tok = (mp_token_kind_t)'),
    })
    
    # parse.c:758,784 - mp_token_kind_t tok = rule_id;
    fix_file(r'py\parse.c', {
        758: ('mp_token_kind_t tok = ', 'mp_token_kind_t tok = (mp_token_kind_t)'),
        784: ('mp_token_kind_t tok = ', 'mp_token_kind_t tok = (mp_token_kind_t)'),
    })
    
    # builtinimport.c:292 - int n = mp_map_elem_t* → ??? needs context
    # showbc.c:87,88 - const byte * = const void *const
    fix_file(r'py\showbc.c', {
        87: ('const byte *ip = ', 'const byte *ip = (const byte *)'),
        88: ('const byte *ip_end = ', 'const byte *ip_end = (const byte *)'),
    })
    
    # pyexec.c:104 - const vstr_t * = const void*
    fix_file(r'shared\runtime\pyexec.c', {
        104: ('const vstr_t *vstr = ', 'const vstr_t *vstr = (const vstr_t *)'),
        143: ('const mp_reader_t *reader = ', 'const mp_reader_t *reader = (const mp_reader_t *)'),
    })
    
    # stream.c:100 - const mp_stream_p_t * = const void*
    fix_file(r'py\stream.c', {
        100: ('const mp_stream_p_t *stream_p = MP_OBJ_TO_PTR(obj);',
              'const mp_stream_p_t *stream_p = (const mp_stream_p_t *)MP_OBJ_TO_PTR(obj);'),
    })
    
    # objtype.c:69,215,1325,1402 - const mp_obj_tuple_t * = const void*
    fix_file(r'py\objtype.c', {
        69: ('const mp_obj_tuple_t *items = ', 'const mp_obj_tuple_t *items = (const mp_obj_tuple_t *)'),
        215: ('const mp_obj_tuple_t *items = ', 'const mp_obj_tuple_t *items = (const mp_obj_tuple_t *)'),
        1325: ('const mp_obj_tuple_t *items = ', 'const mp_obj_tuple_t *items = (const mp_obj_tuple_t *)'),
        1402: ('const mp_obj_tuple_t *items = ', 'const mp_obj_tuple_t *items = (const mp_obj_tuple_t *)'),
    })
    
    # ---- C2440 = void*→typed* ----
    # nlrsetjmp.c:32 - top = (uint8_t *)MP_STATE_THREAD(nlr_top); or similar with void*
    fix_file(r'py\nlrsetjmp.c', {
        32: ('top = ', 'top = (uint8_t *)'),
    })
    
    # pystack.c:34,35,36 - void* = uint8_t*
    for ln in [34, 35, 36]:
        fix_file(r'py\pystack.c', {
            ln: (' = ', ' = (uint8_t *)'),
        })
    
    # pairheap.c:53,60,107 - void*→_mp_pairheap_t* / mp_pairheap_t*
    fix_file(r'py\pairheap.c', {
        53: (' = ', ' = (_mp_pairheap_t *)'),
        60: (' = ', ' = (_mp_pairheap_t *)'),
        107: (' = ', ' = (mp_pairheap_t *)'),
    })
    
    # objfun.c:374 - tuple = ...void*...
    fix_file(r'py\objfun.c', {
        374: (' = MP_OBJ_TO_PTR(', ' = (mp_obj_tuple_t *)MP_OBJ_TO_PTR('),
    })
    
    # objtuple.c:296 - void*→mp_obj_tuple_t*
    fix_file(r'py\objtuple.c', {
        296: (' = ', ' = (mp_obj_tuple_t *)'),
    })
    
    # runtime.c:843,864,905 - void*→mp_obj_t*
    # These are m_malloc or similar - need context
    # vm.c:606,714 - void*→mp_obj_t*
    for ln in [843, 864, 905]:
        fix_file(r'py\runtime.c', {
            ln: (' = ', ' = (mp_obj_t *)'),
        })
    
    # objset.c:292,294,301,303 - void*→mp_obj_set_t*
    for ln in [292, 294, 301, 303]:
        fix_file(r'py\objset.c', {
            ln: (' = MP_OBJ_TO_PTR(', ' = (mp_obj_set_t *)MP_OBJ_TO_PTR('),
        })
    
    # objtype.c:336 - void*→mp_obj_instance_t*
    fix_file(r'py\objtype.c', {
        336: (' = MP_OBJ_TO_PTR(', ' = (mp_obj_instance_t *)MP_OBJ_TO_PTR('),
    })
    
    # builtinevex.c:133 - void*→mp_obj_dict_t*
    fix_file(r'py\builtinevex.c', {
        133: (' = ', ' = (mp_obj_dict_t *)'),
    })
    
    # objmodule.c:134 - void*→mp_obj_dict_t*
    fix_file(r'py\objmodule.c', {
        134: (' = MP_OBJ_TO_PTR(', ' = (mp_obj_dict_t *)MP_OBJ_TO_PTR('),
    })
    
    # builtinhelp.c:157 - void*→const mp_obj_type_t*
    fix_file(r'py\builtinhelp.c', {
        157: (' = MP_OBJ_TO_PTR(', ' = (const mp_obj_type_t *)MP_OBJ_TO_PTR('),
    })
    
    # runtime.c:1158 - void*→const mp_obj_type_t*
    fix_file(r'py\runtime.c', {
        1158: (' = MP_OBJ_TO_PTR(', ' = (const mp_obj_type_t *)MP_OBJ_TO_PTR('),
    })
    
    # stackctrl.c:48 - void*→char*
    fix_file(r'py\stackctrl.c', {
        48: (' = ', ' = (char *)'),
    })
    
    # gc.c:152 - void*→byte*
    fix_file(r'py\gc.c', {
        152: (' = end', ' = (byte *)end'),
    })
    
    # lexer.c:724 - size_t→mp_token_kind_t
    fix_file(r'py\lexer.c', {
        724: (' = ', ' = (mp_token_kind_t)'),
        834: (' = ', ' = (mp_token_kind_t)'),
    })
    
    # compile.c:2288 - int→mp_unary_op_t
    fix_file(r'py\compile.c', {
        2288: (' = ', ' = (mp_unary_op_t)'),
    })
    
    # parse.c:790 - int→mp_unary_op_t
    fix_file(r'py\parse.c', {
        790: (' = ', ' = (mp_unary_op_t)'),
    })
    
    # objtype.c:81,236 - const void*→const mp_obj_type_t*
    fix_file(r'py\objtype.c', {
        81: (' = ', ' = (const mp_obj_type_t *)'),
        236: (' = ', ' = (const mp_obj_type_t *)'),
    })
    
    # vm.c:1455 changed from 'nlr.ret_val' to 'mp_obj_t' - need different fix
    # The error became: mp_obj_t → mp_obj_base_t*
    # This was the previous fix changing nlr.ret_val to (mp_obj_t)nlr.ret_val
    # Let me check what the line looks like now
    
    # ---- C2143/C2059 syntax errors in objtype.c ----
    # These are likely from compound literal {0} in C++98
    # Need to read the file to see what's there
    
    # ---- C2086 redefinition ----
    # objdict.c:477,540 - duplicate type definitions
    # Need to read the file to see the duplicates
    
    # ---- C2065 MICROPY_REGISTERED_MODULES ----
    # The previous fix didn't work, need a different approach
    # These should be defined in mpconfigport.h or similar

print('=== Pass 2: Comprehensive remaining fixes ===')
fix_all()
print('\n=== Pass 2 complete ===')
print('Some complex errors still need manual review:')
print('- objtype.c:1291,1481 (C2143/C2059 - compound literals)')
print('- objdict.c:477,540 (C2086 - redefinition)')
print('- builtinimport.c:292 (C2440 - mp_map_elem_t* to int)')
print('- objtype.c:1343 (C2664 - mp_obj_class_lookup)')
print('- builtinevex.c:158 (C2664 - mp_lexer_new_from_str_len)')
print('- objint.c:412 (C2664 - already fixed?)')
print('- emitbc.c:96,147 (C2440 - m_new0 casts if still present)')
print('- vm.c:1455 (C2440 - mp_obj_t to mp_obj_base_t* new error)')
print('- modstruct.c:135 (C2440 - byte* cast)')
print('- C2065 MICROPY_REGISTERED_MODULES (if still present)')
