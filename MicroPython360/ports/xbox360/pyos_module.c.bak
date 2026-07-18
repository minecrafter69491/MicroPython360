#include "runtime.h"
#include "obj.h"
#include "mperrno.h"
#include "pyos_module.h"

static mp_obj_t pyos_read_file(mp_obj_t path_obj) {
    const char* path = mp_obj_str_get_str(path_obj);
    size_t len;
    char* data = pyos_host_read_file(path, &len);
    if (!data) {
        mp_raise_OSError(MP_ENOENT);
    }
    mp_obj_t result = mp_obj_new_str(data, len);
    free(data);
    return result;
}
MP_DEFINE_CONST_FUN_OBJ_1(pyos_read_file_obj, pyos_read_file);

static mp_obj_t pyos_mount_image(mp_obj_t path_obj) {
    const char* path = mp_obj_str_get_str(path_obj);
    int handle = pyos_host_mount_image(path);
    if (handle < 0) {
        mp_raise_OSError(MP_EIO);
    }
    return mp_obj_new_int(handle);
}
MP_DEFINE_CONST_FUN_OBJ_1(pyos_mount_image_obj, pyos_mount_image);

static mp_obj_t pyos_unmount_image(mp_obj_t handle_obj) {
    int handle = mp_obj_get_int(handle_obj);
    pyos_host_unmount_image(handle);
    return mp_const_none;
}
MP_DEFINE_CONST_FUN_OBJ_1(pyos_unmount_image_obj, pyos_unmount_image);

static mp_obj_t pyos_image_read(mp_obj_t handle_obj, mp_obj_t vpath_obj) {
    int handle = mp_obj_get_int(handle_obj);
    const char* vpath = mp_obj_str_get_str(vpath_obj);
    char buf[32768];
    int n = pyos_host_image_read(handle, vpath, buf, sizeof(buf) - 1);
    if (n < 0) {
        mp_raise_OSError(MP_ENOENT);
    }
    buf[n] = '\0';
    return mp_obj_new_str(buf, n);
}
MP_DEFINE_CONST_FUN_OBJ_2(pyos_image_read_obj, pyos_image_read);

static mp_obj_t pyos_get_nvram(void) {
    size_t len;
    char* data = pyos_host_get_nvram(&len);
    if (!data) {
        mp_raise_OSError(MP_ENOENT);
    }
    mp_obj_t result = mp_obj_new_str(data, len);
    free(data);
    return result;
}
MP_DEFINE_CONST_FUN_OBJ_0(pyos_get_nvram_obj, pyos_get_nvram);

static const mp_rom_map_elem_t pyos_module_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_pyos) },
    { MP_ROM_QSTR(MP_QSTR_read_file), MP_ROM_PTR(&pyos_read_file_obj) },
    { MP_ROM_QSTR(MP_QSTR_mount_image), MP_ROM_PTR(&pyos_mount_image_obj) },
    { MP_ROM_QSTR(MP_QSTR_unmount_image), MP_ROM_PTR(&pyos_unmount_image_obj) },
    { MP_ROM_QSTR(MP_QSTR_image_read), MP_ROM_PTR(&pyos_image_read_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_nvram), MP_ROM_PTR(&pyos_get_nvram_obj) },
    { MP_ROM_QSTR(MP_QSTR_FileNotFoundError), MP_ROM_PTR(&mp_type_OSError) },
};
static MP_DEFINE_CONST_DICT(pyos_module_globals, pyos_module_globals_table);

const mp_obj_module_t mp_module_pyos = {
    { &mp_type_module },
    (mp_obj_dict_t*)&pyos_module_globals,
};


