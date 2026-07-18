def split(line):
    result = []
    current = ""
    quote = None

    for c in line:
        if quote:
            if c == quote:
                quote = None
            else:
                current += c

        else:
            if c in ("'", '"'):
                quote = c

            elif c == " " or c == "\t":
                if current:
                    result.append(current)
                    current = ""

            else:
                current += c

    if current:
        result.append(current)

    return result