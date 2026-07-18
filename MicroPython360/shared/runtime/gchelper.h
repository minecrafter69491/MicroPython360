#ifndef MICROPY_INCLUDED_SHARED_RUNTIME_GCHELPER_H
#define MICROPY_INCLUDED_SHARED_RUNTIME_GCHELPER_H

#include <setjmp.h>

typedef jmp_buf gc_helper_regs_t;

void gc_helper_collect_regs_and_stack(void);

#endif
