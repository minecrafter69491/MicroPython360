#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdarg.h>
#include "mpconfig.h"
#include "mphal.h"
#include "mpstate.h"
#include "misc.h"
#include "gc.h"
#include "runtime.h"
#include "stackctrl.h"
#include "lexer.h"
#include "reader.h"
#include "shared/runtime/pyexec.h"
#include "mperrno.h"
#include "builtin.h"
#include "parse.h"
#include "compile.h"
#include "objmodule.h"
#include "shared/runtime/gchelper.h"

extern void xbox360_uart_putc(char c);
extern char xbox360_uart_getc(void);
extern unsigned long xbox360_get_tick_ms(void);

mp_uint_t mp_hal_ticks_ms(void) {
    return xbox360_get_tick_ms();
}

mp_uint_t mp_hal_ticks_us(void) {
    return xbox360_get_tick_ms() * 1000;
}

void mp_hal_set_interrupt_char(char c) {
}

int mp_hal_stdin_rx_chr(void) {
    return xbox360_uart_getc();
}

mp_uint_t mp_hal_stdout_tx_strn(const char *str, mp_uint_t len) {
    for (mp_uint_t i = 0; i < len; i++) {
        xbox360_uart_putc(str[i]);
    }
    return len;
}

void mp_hal_stdout_tx_str(const char *str) {
    mp_hal_stdout_tx_strn(str, strlen(str));
}

void mp_hal_stdout_tx_strn_cooked(const char *str, mp_uint_t len) {
    for (mp_uint_t i = 0; i < len; i++) {
        if (str[i] == '\n') {
            xbox360_uart_putc('\r');
        }
        xbox360_uart_putc(str[i]);
    }
}

void gc_collect(void) {
    gc_collect_start();
    gc_helper_collect_regs_and_stack();
    gc_collect_end();
}

mp_lexer_t *mp_lexer_new_from_file(qstr filename) {
    const char *path = qstr_str(filename);
    FILE *f = fopen(path, "rb");
    if (!f) {
        mp_raise_OSError(MP_ENOENT);
    }
    fseek(f, 0, SEEK_END);
    long len = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *data = (char*)malloc(len + 1);
    if (!data) {
        fclose(f);
        mp_raise_OSError(MP_ENOMEM);
    }
    size_t n = fread(data, 1, len, f);
    fclose(f);
    data[n] = '\0';
    mp_lexer_t *lex = mp_lexer_new_from_str_len(filename, data, n, 0);
    free(data);
    return lex;
}

mp_import_stat_t mp_import_stat(const char *path) {
    size_t plen = strlen(path);
    char *fpath = (char*)malloc(plen + 4);
    memcpy(fpath, path, plen);
    fpath[plen] = '.';
    fpath[plen + 1] = 'p';
    fpath[plen + 2] = 'y';
    fpath[plen + 3] = '\0';

    FILE *f = fopen(fpath, "rb");
    free(fpath);
    if (f) {
        fclose(f);
        return MP_IMPORT_STAT_FILE;
    }

    char *dpath = (char*)malloc(plen + 13);
    memcpy(dpath, path, plen);
    memcpy(dpath + plen, "/__init__.py", 13);
    f = fopen(dpath, "rb");
    free(dpath);
    if (f) {
        fclose(f);
        return MP_IMPORT_STAT_DIR;
    }

    return MP_IMPORT_STAT_NO_EXIST;
}



mp_obj_t mp_builtin_open(size_t n_args, const mp_obj_t *args, mp_map_t *kwargs) {
    mp_raise_OSError(MP_ENOENT);
}
MP_DEFINE_CONST_FUN_OBJ_KW(mp_builtin_open_obj, 1, mp_builtin_open);

void nlr_jump_fail(void *val) {
    while (1);
}

void NORETURN __fatal_error(const char *msg) {
    while (1);
}

void __stack_chk_fail(void) {
    static bool failed_once;
    if (failed_once) return;
    failed_once = true;
    __fatal_error("Stack corruption detected");
}

void __assert_fail(const char *assertion, const char *file,
    unsigned int line, const char *function) {
    printf("Assert at %s:%d:%s() \"%s\" failed\n", file, line, function, assertion);
    for (;;);
}

extern const mp_obj_module_t mp_module_pyos;

// Terminal printf helper: writes to screen via xbox360_uart_putc
static void term_printf(const char *fmt, ...) {
    char buf[256];
    va_list args;
    va_start(args, fmt);
    vsnprintf(buf, sizeof(buf), fmt, args);
    va_end(args);
    for (char *p = buf; *p; p++) {
        xbox360_uart_putc(*p);
    }
}

void mp_xbox360_init(void) {
    __declspec(align(16)) static char heap[256 * 1024];

    memset(&mp_state_ctx, 0, sizeof(mp_state_ctx));

    gc_init(heap, heap + sizeof(heap));

    mp_stack_ctrl_init();
    mp_stack_set_limit(48 * 1024);

    mp_init();

    // ABI diagnostics — now visible on screen via terminal
    term_printf("MICROPY_OBJ_REPR=%d\r\n", MICROPY_OBJ_REPR);
    term_printf("sizeof(mp_int_t)=%u\r\n", sizeof(mp_int_t));
    term_printf("sizeof(mp_uint_t)=%u\r\n", sizeof(mp_uint_t));
    term_printf("sizeof(void*)=%u\r\n", sizeof(void*));
    term_printf("sizeof(mp_obj_t)=%u\r\n", sizeof(mp_obj_t));
    term_printf("sizeof(size_t)=%u\r\n", sizeof(size_t));
    term_printf("sizeof(long)=%u\r\n", sizeof(long));
    term_printf("sizeof(long long)=%u\r\n", sizeof(long long));
    term_printf("MICROPY_LONGINT_IMPL=%d\r\n", MICROPY_LONGINT_IMPL);
    term_printf("MICROPY_NLR_SETJMP=%d\r\n", MICROPY_NLR_SETJMP);
    term_printf("MP_ENDIANNESS_LITTLE=%d\r\n", MP_ENDIANNESS_LITTLE);
    term_printf("sizeof(mp_obj_t)=%u, sizeof(void*)=%u\r\n", sizeof(mp_obj_t), sizeof(void*));

    // Object model sanity checks
    mp_obj_t one = mp_obj_new_int(1);
    mp_obj_t two = mp_obj_new_int(2);
    term_printf("small_int(1)=0x%x, small_int(2)=0x%x\r\n", (unsigned)one, (unsigned)two);
    term_printf("mp_type_int.type=0x%x\r\n", (unsigned)(mp_uint_t)(mp_obj_get_type(one)));
    term_printf("mp_type_int ptr=0x%x\r\n", (unsigned)(mp_uint_t)(&mp_type_int));

    // Test int add at C level
    mp_obj_t sum = mp_binary_op(MP_BINARY_OP_ADD, one, two);
    term_printf("1+2 result=0x%x\r\n", (unsigned)sum);
    if (mp_obj_is_small_int(sum)) {
        term_printf("1+2 = %d\r\n", (int)MP_OBJ_SMALL_INT_VALUE(sum));
    } else if (mp_obj_is_exact_type(sum, &mp_type_int)) {
        term_printf("1+2 is mp_int\r\n");
    } else {
        term_printf("1+2 type is not small int or mp_int\r\n");
    }

    // Test print at C level
    term_printf("mp_plat_print test: ");
    mp_print_str(&mp_plat_print, "hello from MicroPython print\n");

    // --- Pipeline test: parse+compile+execute in EVAL mode ---
    {
        term_printf("=== Pipeline test EVAL '1+1' ===\r\n");
        nlr_buf_t nlr;
        if (nlr_push(&nlr) == 0) {
            mp_lexer_t *lex = mp_lexer_new_from_str_len(MP_QSTR__lt_stdin_gt_,
                "1+1", 3, 0);
            mp_obj_t result = mp_parse_compile_execute(lex, MP_PARSE_EVAL_INPUT,
                mp_globals_get(), mp_locals_get());
            term_printf("EVAL result=0x%x\r\n", (unsigned)result);
            if (mp_obj_is_small_int(result)) {
                term_printf("EVAL 1+1 = %d\r\n", (int)MP_OBJ_SMALL_INT_VALUE(result));
            } else {
                term_printf("EVAL result type is not small int\r\n");
            }
            nlr_pop();
        } else {
            mp_obj_t exc = (mp_obj_t)nlr.ret_val;
            term_printf("EVAL exception: ");
            mp_obj_print_exception(&mp_plat_print, exc);
            term_printf("\r\n");
        }
    }

    // --- Pipeline test: SINGLE_INPUT mode ---
    {
        term_printf("=== Pipeline test SINGLE '1+1\\n' ===\r\n");
        nlr_buf_t nlr;
        if (nlr_push(&nlr) == 0) {
            mp_lexer_t *lex = mp_lexer_new_from_str_len(MP_QSTR__lt_stdin_gt_,
                "1+1\n", 4, 0);
            mp_parse_compile_execute(lex, MP_PARSE_SINGLE_INPUT,
                mp_globals_get(), mp_locals_get());
            term_printf("SINGLE completed without exception\r\n");
            nlr_pop();
        } else {
            mp_obj_t exc = (mp_obj_t)nlr.ret_val;
            // Print type name
            const mp_obj_type_t *type = mp_obj_get_type(exc);
            term_printf("SINGLE exception type: ");
            mp_print_str(&mp_plat_print, qstr_str(type->name));
            term_printf("\r\nSINGLE full exception: ");
            mp_obj_print_exception(&mp_plat_print, exc);
            term_printf("\r\n");
        }
    }

    // --- Check what's in globals ---
    {
        mp_obj_dict_t *globals = mp_globals_get();
        term_printf("globals dict ptr=0x%x\r\n", (unsigned)(mp_uint_t)globals);
        term_printf("globals map is_ordered=%d used=%u alloc=%u\r\n",
            globals->map.is_ordered, globals->map.used, globals->map.alloc);
    }

    // --- Try looking up 'print' ---
    {
        qstr print_qstr = MP_QSTR_print;
        mp_obj_t print_obj;
        term_printf("Lookup 'print':\r\n");
        // Try mp_load_name
        nlr_buf_t nlr;
        if (nlr_push(&nlr) == 0) {
            print_obj = mp_load_name(print_qstr);
            term_printf("mp_load_name(print) = 0x%x\r\n", (unsigned)print_obj);
            const mp_obj_type_t *type = mp_obj_get_type(print_obj);
            term_printf("type = 0x%x, name = ", (unsigned)(mp_uint_t)type);
            mp_print_str(&mp_plat_print, qstr_str(type->name));
            term_printf("\r\n");
            nlr_pop();
        } else {
            mp_obj_t exc = (mp_obj_t)nlr.ret_val;
            term_printf("mp_load_name(print) failed: ");
            mp_obj_print_exception(&mp_plat_print, exc);
            term_printf("\r\n");
        }
    }

    // Register pyos module
    mp_obj_dict_store(MP_OBJ_FROM_PTR(&MP_STATE_VM(mp_loaded_modules_dict)), MP_OBJ_NEW_QSTR(MP_QSTR_pyos), MP_OBJ_FROM_PTR(&mp_module_pyos));
}

void mp_xbox360_execute(const char *script) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_lexer_t *lex = mp_lexer_new_from_str_len(MP_QSTR__lt_stdin_gt_,
            script, strlen(script), 0);
        mp_parse_compile_execute(lex, MP_PARSE_SINGLE_INPUT, mp_globals_get(), mp_locals_get());
        nlr_pop();
    } else {
        mp_obj_t exc = (mp_obj_t)nlr.ret_val;
        if (mp_obj_is_subclass_fast(mp_obj_get_type(exc), &mp_type_SystemExit)) {
            return;
        }
        mp_obj_print_exception(&mp_plat_print, exc);
    }
}

void mp_xbox360_execute_evall(const char *script) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_lexer_t *lex = mp_lexer_new_from_str_len(MP_QSTR__lt_stdin_gt_,
            script, strlen(script), 0);
        mp_parse_compile_execute(lex, MP_PARSE_EVAL_INPUT, mp_globals_get(), mp_locals_get());
        nlr_pop();
    } else {
        mp_obj_t exc = (mp_obj_t)nlr.ret_val;
        mp_obj_print_exception(&mp_plat_print, exc);
    }
}

void mp_xbox360_execute_file(const char *script) {
    nlr_buf_t nlr;
    if (nlr_push(&nlr) == 0) {
        mp_lexer_t *lex = mp_lexer_new_from_str_len(MP_QSTR__lt_stdin_gt_,
            script, strlen(script), 0);
        mp_parse_compile_execute(lex, MP_PARSE_FILE_INPUT, mp_globals_get(), mp_locals_get());
        nlr_pop();
    } else {
        mp_obj_t exc = (mp_obj_t)nlr.ret_val;
        mp_obj_print_exception(&mp_plat_print, exc);
    }
}
