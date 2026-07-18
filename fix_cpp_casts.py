import os, re, sys

BASE = os.path.join(os.path.dirname(__file__) or '.', 'MicroPython360')
PY_DIR = os.path.join(BASE, 'py')
XBOX_DIR = os.path.join(BASE, 'ports', 'xbox360')

C_EXT = ('.c', '.h')

def fix_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    original = content

    lines = content.split('\n')
    new_lines = []
    modified = False

    for lineno, line in enumerate(lines, 1):
        orig_line = line
        stripped = line.lstrip()

        # 1) type *var = MP_OBJ_TO_PTR( -> add (type *) cast
        #    Handles: type *var = MP_OBJ_TO_PTR(...
        #             const type *var = MP_OBJ_TO_PTR(...
        #             type * const var = MP_OBJ_TO_PTR(...  (unusual, skip)
        m = re.match(
            r'^(\s*(?:const\s+)?([a-zA-Z_]\w*)\s+\*\s*(\w+))\s*=\s*MP_OBJ_TO_PTR\(',
            line
        )
        if m:
            prefix = m.group(1)  # e.g. "mp_obj_type_t *type" or "const mp_obj_base_t *o"
            typename = m.group(2)
            full_decl = m.group(0)
            col_offset = m.start()
            cast_type = f"const {typename} *" if stripped.startswith('const ') else f"{typename} *"
            line = line.replace('= MP_OBJ_TO_PTR(', f"= ({cast_type})MP_OBJ_TO_PTR(", 1)
            modified = True
            print(f"  [{filepath}:{lineno}] MP_OBJ_TO_PTR cast: add ({cast_type})")

        # 2) type *var = parser_alloc(...) -> add (type *) cast
        m2 = re.match(
            r'^(\s*(?:(?:const|static)\s+)?([a-zA-Z_]\w*)\s+\*\s*(\w+))\s*=\s*parser_alloc\(',
            line
        )
        if m2 and 'MP_OBJ_TO_PTR' not in line:
            prefix = m2.group(1)
            typename = m2.group(2)
            cast_type = f"{typename} *"
            line = line.replace('= parser_alloc(', f"= ({cast_type})parser_alloc(", 1)
            modified = True
            print(f"  [{filepath}:{lineno}] parser_alloc cast: add ({cast_type})")

        # 3) C2664: explicit casts for enum assignments with arithmetic
        #    mp_binary_op_t var = <arithmetic expression>  ->  (mp_binary_op_t)
        #    mp_unary_op_t  var = <arithmetic expression>  ->  (mp_unary_op_t)
        #    mp_token_kind_t var = <arithmetic expression>  ->  (mp_token_kind_t)
        for enum_type in ('mp_binary_op_t', 'mp_unary_op_t', 'mp_token_kind_t'):
            # Pattern: enum_type var = <expr that's not just a simple enum value>
            # If RHS is a single identifier or simple enum constant, skip it
            enum_re = re.compile(
                r'^(\s*)' + re.escape(enum_type) + r'\s+\w+\s*=\s*(.+)$'
            )
            em = enum_re.match(line)
            if em:
                rhs = em.group(2).rstrip(';').strip()
                # Skip if RHS is a simple identifier, cast expression, or function call
                # Only flag arithmetic or bitwise expressions
                # Replace -> and -- with placeholders to avoid false positives from struct access
                cleaned = rhs.replace('->', '  ').replace('--', '  ')
                if re.search(r'[+\-*/%&|^~]', cleaned) and not re.match(r'\s*\(\s*' + re.escape(enum_type) + r'\s*\)\s*\(', rhs):
                    # Wrap entire RHS in (enum_type)(...)
                    indent = em.group(1)
                    parts = line.split('=', 1)
                    after_eq = parts[1].lstrip()
                    # Remove trailing semicolon for clean wrapping
                    has_semi = after_eq.endswith(';')
                    if has_semi:
                        after_eq = after_eq[:-1]
                    line = parts[0] + '= (' + enum_type + ')(' + after_eq.strip() + ')' + (';' if has_semi else '')
                    modified = True
                    print(f"  [{filepath}:{lineno}] {enum_type} cast on arithmetic RHS")
                break

        new_lines.append(line)

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write('\n'.join(new_lines))
        return True
    return False


def main():
    total = 0
    for root, dirs, files in os.walk(PY_DIR):
        for f in files:
            if f.endswith(C_EXT) and not f.endswith('.bak'):
                fp = os.path.join(root, f)
                if fix_file(fp):
                    total += 1

    if os.path.isdir(XBOX_DIR):
        for root, dirs, files in os.walk(XBOX_DIR):
            for f in files:
                if f.endswith(C_EXT) and not f.endswith('.bak'):
                    fp = os.path.join(root, f)
                    if fix_file(fp):
                        total += 1

    print(f"\nFixed {total} file(s).")


if __name__ == '__main__':
    main()
