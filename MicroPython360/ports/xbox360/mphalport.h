// Tell py/mphal.h that we provide our own implementation of
// mp_hal_stdout_tx_strn (with a different return type) so mphal.h
// won't emit its conflicting default declaration.
#define mp_hal_stdout_tx_strn   mp_hal_stdout_tx_strn

// Prevent py/mphal.h from including extmod/virtpin.h (not available on
// Xbox 360) and from defining the generic virtual-pin fallback macros.
#define mp_hal_pin_obj_t int

extern mp_uint_t mp_hal_ticks_ms(void);
extern mp_uint_t mp_hal_ticks_us(void);
extern void mp_hal_set_interrupt_char(char c);
extern int mp_hal_stdin_rx_chr(void);
extern mp_uint_t mp_hal_stdout_tx_strn(const char *str, mp_uint_t len);
