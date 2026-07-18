try:
    FileNotFoundError
except NameError:
    class FileNotFoundError(Exception):
        pass

try:
    PermissionError
except NameError:
    class PermissionError(Exception):
        pass

try:
    NotADirectoryError
except NameError:
    class NotADirectoryError(Exception):
        pass


import json
import os
import random
import time

# ============================
# Helpers
# ============================
def exists(path):
    try:
        os.stat(path)
        return True
    except OSError:
        return False


def isdir(path):
    try:
        st = os.stat(path)

        # MicroPython stat tuple:
        # index 0 = mode
        # directory bit = 0x4000
        return bool(st[0] & 0x4000)

    except OSError:
        return False
def normpath(path):
    if not path:
        return "/"

    parts = []

    for p in path.split("/"):
        if p == "" or p == ".":
            continue

        if p == "..":
            if parts:
                parts.pop()
        else:
            parts.append(p)

    return "/" + "/".join(parts)


def dirname(path):
    path = normpath(path)

    if path == "/":
        return "/"

    return "/" + "/".join(path.strip("/").split("/")[:-1])


def basename(path):
    path = normpath(path)

    if path == "/":
        return "/"

    return path.strip("/").split("/")[-1]


def join(a, b):
    return normpath(a.rstrip("/") + "/" + b.lstrip("/"))
def make_stat(is_dir, size=0, mode=0o755, owner=0, group=0):
    return {
        "is_dir": is_dir,
        "size": size,
        "mode": mode,
        "owner": owner,
        "group": group,
    }

# ============================
# Image block device
# ============================

class ImageBlockDevice:
    def __init__(self, img_path):
        self.file = open(img_path, "r+b")
        self.pos = 0

    def read(self, size=-1):
        self.file.seek(self.pos)
        data = self.file.read(size)
        self.pos += len(data)
        return data

    def write(self, data):
        self.file.seek(self.pos)
        self.file.write(data)
        self.pos += len(data)
        return len(data)

    def seek(self, pos):
        self.pos = pos

    def close(self):
        self.file.flush()

# ============================
# Overlay filesystem
# ============================

class OverlayFS:
    writable = True

    def __init__(self):
        self.files = {}     # path -> bytes
        self.dirs = {"/"}
        self.meta = {}

    def _norm(self, path):
        if not path.startswith("/"):
            path = "/" + path
        return path.rstrip("/") if path != "/" else "/"

    def exists(self, path):
        path = self._norm(path)
        return path in self.files or path in self.dirs

    def mkdir(self, path):
        path = self._norm(path)
        parent = dirname(path) or "/"
        if parent not in self.dirs:
            raise FileNotFoundError(parent)
        self.dirs.add(path)
        self.meta[path] = make_stat(True)

    def listdir(self, path):
        path = self._norm(path)
        if path not in self.dirs:
            raise NotADirectoryError(path)

        out = set()
        for d in self.dirs:
            if d != path and dirname(d) == path:
                out.add(basename(d))
        for f in self.files:
            if dirname(f) == path:
                out.add(basename(f))
        return sorted(out)

    def open(self, path, mode="rb"):
        path = self._norm(path)

        if "w" in mode:
            parent = dirname(path) or "/"
            if parent not in self.dirs:
                raise FileNotFoundError(parent)
            self.files.setdefault(path, b"")
            self.meta.setdefault(path, make_stat(False))
            return OverlayFile(self, path)

        if path not in self.files:
            raise FileNotFoundError(path)
        return OverlayFile(self, path, readonly=True)

    def unlink(self, path):
        path = self._norm(path)
        if path in self.files:
            del self.files[path]
            del self.meta[path]
            return
        raise FileNotFoundError(path)

    def stat(self, path):
        path = self._norm(path)
        if path in self.dirs:
            return make_stat(True)
        if path in self.files:
            return make_stat(False, size=len(self.files[path]))
        raise FileNotFoundError(path)

class OverlayFile:
    def __init__(self, fs, path, readonly=False):
        self.fs = fs
        self.path = path
        self.pos = 0
        self.readonly = readonly

    def read(self, size=-1):
        data = self.fs.files[self.path]
        if size < 0:
            size = len(data) - self.pos
        out = data[self.pos:self.pos + size]
        self.pos += len(out)
        return out

    def write(self, data):
        if self.readonly:
            raise PermissionError("read-only")
        if isinstance(data, str):
            data = data.encode()
        buf = self.fs.files[self.path]
        self.fs.files[self.path] = buf[:self.pos] + data + buf[self.pos + len(data):]
        self.pos += len(data)

    def seek(self, pos):
        self.pos = pos

    def close(self):
        pass

# ============================
# Image-backed filesystem
# ============================

class JsonNVRAM:
    writable = True

    def __init__(self, path):
        self.path = path

        try:
            with open(path, "r") as f:
                self.data = json.load(f)
        except:
            self.data = {}

    def save(self):
        with open(self.path, "w") as f:
            json.dump(self.data, f)


    def exists(self, path):
        path = path.strip("/")

        if path == "":
            return True

        return path in self.data


    def listdir(self, path):
        path = path.strip("/")

        if path == "":
            return list(self.data.keys())

        return []


    def stat(self, path):
        path = path.strip("/")

        if path == "":
            return make_stat(True)

        if path in self.data:
            value = str(self.data[path])

            return make_stat(
                False,
                len(value)
            )

        raise FileNotFoundError(path)


    def open(self, path, mode="rb"):
        path = path.strip("/")

        if path not in self.data:
            raise FileNotFoundError(path)

        return NVRAMFile(self, path)


class NVRAMFile:
    def __init__(self, nvram, key):
        self.nvram = nvram
        self.key = key

    def read(self, size=-1):
        data = str(
            self.nvram.data[self.key]
        ).encode()

        if size >= 0:
            return data[:size]

        return data


    def write(self, data):
        if isinstance(data, bytes):
            data = data.decode()

        self.nvram.data[self.key] = data
        self.nvram.save()


    def close(self):
        pass

class ImageFS:
    writable = False

    def __init__(self, img_path):
        self.file = open(img_path, "rb")
        self.table = self._load_table()

    def _load_table(self):
        self.file.seek(0)
        size = int.from_bytes(self.file.read(4), "little")
        return json.loads(self.file.read(size))

    def exists(self, path):
        return path in self.table or any(p.startswith(path.rstrip("/") + "/") for p in self.table)

    def listdir(self, path):
        path = path.rstrip("/") + "/"
        out = set()
        for p in self.table:
            if p.startswith(path):
                rest = p[len(path):]
                out.add(rest.split("/", 1)[0])
        return sorted(out)

    def stat(self, path):
        if path == "/":
            return make_stat(True)
        if path in self.table:
            return make_stat(False, self.table[path]["size"])
        if any(p.startswith(path.rstrip("/") + "/") for p in self.table):
            return make_stat(True)
        raise FileNotFoundError(path)

    def open(self, path, mode="rb"):
        if not path.startswith("/"):
            path = "/" + path

        if path not in self.table:
            raise FileNotFoundError(path)
        return ImageFile(self, self.table[path])
class TempImageFS:
    writable = False

    def __init__(self, file):
        self.file = file
        self.table = self._load_table()

    def _load_table(self):
        self.file.seek(0)
        size = int.from_bytes(self.file.read(4), "little")
        return json.loads(self.file.read(size))

    def exists(self, path):
        return path in self.table or any(p.startswith(path.rstrip("/") + "/") for p in self.table)

    def listdir(self, path):
        path = path.rstrip("/") + "/"
        out = set()
        for p in self.table:
            if p.startswith(path):
                rest = p[len(path):]
                out.add(rest.split("/", 1)[0])
        return sorted(out)

    def stat(self, path):
        if path == "/":
            return make_stat(True)
        if path in self.table:
            return make_stat(False, self.table[path]["size"])
        if any(p.startswith(path.rstrip("/") + "/") for p in self.table):
            return make_stat(True)
        raise FileNotFoundError(path)

    def open(self, path, mode="rb"):
        if not path.startswith("/"):
            path = "/" + path

        if path not in self.table:
            raise FileNotFoundError(path)
        return ImageFile(self, self.table[path])
    
class PropFS:
    writable = True

    def __init__(self, init):
        self.init = init

    def exists(self, path):
        path = path.strip("/")
        return path in self.init.properties

    def listdir(self, path):
        path = path.strip("/")

        if path == "":
            return list(self.init.properties.keys())

        return []

    def open(self, path, mode="rb"):
        path = path.strip("/")

        if "w" in mode:
            return PropFile(self.init, path)

        if path not in self.init.properties:
            raise FileNotFoundError(path)

        return PropFile(self.init, path, readonly=True)

    def stat(self, path):
        path = path.strip("/")

        if path in self.init.properties:
            return {
                "is_dir": False,
                "size": len(self.init.properties[path]),
                "mode": 0o644,
                "owner": 0,
                "group": 0
            }

        raise FileNotFoundError(path)


class PropFile:
    def __init__(self, init, name, readonly=False):
        self.init = init
        self.name = name
        self.readonly = readonly
        self.pos = 0

    def read(self, size=-1):
        value = str(self.init.properties.get(self.name, ""))

        data = value.encode()

        if size < 0:
            return data

        return data[:size]

    def write(self, data):
        if self.readonly:
            raise PermissionError()

        if isinstance(data, bytes):
            data = data.decode()

        self.init.properties[self.name] = data.strip()

    def close(self):
        pass

'''class ImageFile:
    def __init__(self, fs, entry):
        self.fs = fs
        self.entry = entry
        self.pos = 0

    def read(self, size=-1):
        if size < 0:
            size = self.entry["size"] - self.pos
        self.fs.file.seek(self.entry["offset"] + self.pos)
        data = self.fs.file.read(size)
        self.pos += len(data)
        return data

    def close(self):
        pass
'''
'''class ImageFile:
    def __init__(self, fs, entry):
        self.fs = fs
        self.entry = entry
        self.pos = 0

    def read(self, size=-1):
        if size < 0:
            size = self.entry["size"] - self.pos

        self.fs.file.seek(self.entry["offset"] + self.pos)
        data = self.fs.file.read(size)
        self.pos += len(data)

        return data

    def readline(self):
        line = bytearray()

        while self.pos < self.entry["size"]:
            char = self.read(1)

            if char == b"\n":
                break

            line.extend(char)

        return bytes(line)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()

        if not line:
            raise StopIteration

        return line

    def close(self):
        pass'''
class ImageFile:
    def __init__(self, fs, entry):
        self.fs = fs
        self.entry = entry
        self.pos = 0

    def read(self, size=-1):
        if size < 0:
            size = self.entry["size"] - self.pos

        self.fs.file.seek(self.entry["offset"] + self.pos)
        data = self.fs.file.read(size)
        self.pos += len(data)
        return data

    def readline(self):
        if self.pos >= self.entry["size"]:
            return None   # EOF marker

        data = bytearray()

        while self.pos < self.entry["size"]:
            c = self.read(1)
            data.extend(c)

            if c == b"\n":
                break

        return bytes(data)

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()

        if line is None:
            raise StopIteration

        return line

    def close(self):
        pass

class HostFS:
    writable = True

    def __init__(self, root):
        self.root = root

    def _path(self, path):
        if path == "/":
            return self.root

        return join(
            self.root,
            path.lstrip("/")
        )

    def exists(self, path):
        return exists(self._path(path))

    def listdir(self, path):
        real = self._path(path)

        if not isdir(real):
            raise NotADirectoryError(path)

        return os.listdir(real)

    def open(self, path, mode="rb"):
        return open(
            self._path(path),
            mode
        )

    def stat(self, path):
        real = self._path(path)

        if not exists(real):
            raise FileNotFoundError(path)

        info = os.stat(real)

        return {
            "is_dir": isdir(real),
            "size": info.st_size if not isdir(real) else 0,
            "mode": 0o755,
            "owner": 0,
            "group": 0
        }

    def mkdir(self, path):
        os.mkdir(self._path(path))

    def unlink(self, path):
        os.remove(self._path(path))


# ============================
# /dev filesystem
# ============================

class DevNull:
    def read(self, size=-1):
        return b""

    def write(self, data):
        return len(data)

    def close(self):
        pass


class DevRandom:
    def read(self, size=-1):
        if size < 0:
            size = 1

        return os.urandom(size)

    def close(self):
        pass


class DevFS:
    writable = True

    def __init__(self, vfs=None):
        self.devices = {
            "/null": DevNull(),
            "/random": DevRandom(),
        }

    def exists(self, path):
        path = self._norm(path)
        return path in self.devices or path == "/"

    def _norm(self, path):
        if not path.startswith("/"):
            path = "/" + path

        return path.rstrip("/") if path != "/" else "/"

    def listdir(self, path):
        path = self._norm(path)

        if path != "/":
            raise FileNotFoundError(path)

        return [
            name[1:]
            for name in self.devices
        ]

    def open(self, path, mode="rb"):
        path = self._norm(path)

        if path not in self.devices:
            raise FileNotFoundError(path)

        return self.devices[path]

    def stat(self, path):
        path = self._norm(path)

        if path == "/":
            return make_stat(True)

        if path in self.devices:
            return make_stat(False)

        raise FileNotFoundError(path)
# ============================
# Virtual filesystem
# ============================

class VFS:
    def __init__(self):
        self.mounts = {}

    def mount(self, path, fs):
        self.mounts.setdefault(path, []).append(fs)

    '''def listdir(self, path):
        out = set()
        for mount, fss in self.mounts.items():
            if path == mount or path.startswith(mount.rstrip("/") + "/"):
                rel = path[len(mount):] or "/"
                for fs in fss:
                    try:
                        out.update(fs.listdir(rel))
                    except Exception:
                        pass
        for m in self.mounts:
            parent = dirname(m.rstrip("/")) or "/"
            if parent == path:
                out.add(m.rstrip("/").split("/")[-1])
        return sorted(out)'''
    def listdir(self, path):
        'path = normpath(path)'

        out = set()

        for mount, fss in self.mounts.items():

            if mount == "/":
                rel = path

            elif path == mount:
                rel = "/"

            elif path.startswith(mount.rstrip("/") + "/"):
                rel = path[len(mount):]

            else:
                continue

            for fs in reversed(fss):
                try:
                    out.update(fs.listdir(rel))
                except Exception:
                    pass


        # Add mounted directories
        for m in self.mounts:
            if m == "/":
                continue

            parent = dirname(m.rstrip("/")) or "/"

            if parent == path:
                out.add(m.rstrip("/").split("/")[-1])

        return sorted(out)

    def open(self, path, mode="rb"):
        for mount, fss in self.mounts.items():
            if path == mount or path.startswith(mount.rstrip("/") + "/"):
                rel = path[len(mount):] or "/"
                for fs in reversed(fss):
                    try:
                        return fs.open(rel, mode)
                    except FileNotFoundError:
                        pass
        raise FileNotFoundError(path)

    '''def stat(self, path):
        for mount, fss in self.mounts.items():
            if path.startswith(mount):
                rel = path[len(mount):] or "/"
                for fs in fss:
                    try:
                        return fs.stat(rel)
                    except FileNotFoundError:
                        pass
        raise FileNotFoundError(path)'''
    def stat(self, path):
        path = normpath(path)

        # If exactly a mount point
        if path in self.mounts:
            return make_stat(True)

        for mount, fss in self.mounts.items():

            # root mount
            if mount == "/":
                rel = path

            # inside mount
            elif path.startswith(mount.rstrip("/") + "/"):
                rel = path[len(mount):]

            else:
                continue

            if rel == "":
                rel = "/"

            for fs in reversed(fss):
                try:
                    return fs.stat(rel)
                except OSError:
                    continue

        # A directory can exist just because something is mounted below it
        for mount in self.mounts:
            if dirname(mount) == path:
                return make_stat(True)

        raise FileNotFoundError(path)

# ============================
# Bootloader
# ============================

def panic(msg):
    print("[panic]", msg)
    exit(1)

