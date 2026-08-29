"""Code 39 barcode, encoded by hand into SVG rectangles.

No barcode library, no web service. Nine elements per character
(bar space bar space bar space bar space bar), three of them wide,
one narrow space between characters, start and stop character '*'.
"""

PATTERNS = {
    "0": "nnnwwnwnn", "1": "wnnwnnnnw", "2": "nnwwnnnnw", "3": "wnwwnnnnn",
    "4": "nnnwwnnnw", "5": "wnnwwnnnn", "6": "nnwwwnnnn", "7": "nnnwnnwnw",
    "8": "wnnwnnwnn", "9": "nnwwnnwnn",
    "A": "wnnnnwnnw", "B": "nnwnnwnnw", "C": "wnwnnwnnn", "D": "nnnnwwnnw",
    "E": "wnnnwwnnn", "F": "nnwnwwnnn", "G": "nnnnnwwnw", "H": "wnnnnwwnn",
    "I": "nnwnnwwnn", "J": "nnnnwwwnn", "K": "wnnnnnnww", "L": "nnwnnnnww",
    "M": "wnwnnnnwn", "N": "nnnnwnnww", "O": "wnnnwnnwn", "P": "nnwnwnnwn",
    "Q": "nnnnnnwww", "R": "wnnnnnwwn", "S": "nnwnnnwwn", "T": "nnnnwnwwn",
    "U": "wwnnnnnnw", "V": "nwwnnnnnw", "W": "wwwnnnnnn", "X": "nwnnwnnnw",
    "Y": "wwnnwnnnn", "Z": "nwwnwnnnn",
    "-": "nwnnnnwnw", ".": "wwnnnnwnn", " ": "nwwnnnwnn", "$": "nwnwnwnnn",
    "/": "nwnwnnnwn", "+": "nwnnnwnwn", "%": "nnnwnwnwn", "*": "nwnnwnwnn",
}


def elements(text):
    """Return [(is_bar, is_wide), ...] for '*text*'."""
    out = []
    for i, ch in enumerate("*" + text.upper() + "*"):
        if ch not in PATTERNS:
            raise ValueError("Code 39 cannot encode %r" % ch)
        for j, e in enumerate(PATTERNS[ch]):
            out.append((j % 2 == 0, e == "w"))
        out.append((False, False))  # inter-character narrow space
    out.pop()  # no trailing gap after the stop character
    return out


def width(text, narrow=2, wide=5):
    return sum(wide if w else narrow for _, w in elements(text))


def svg_bars(text, x, y, height, narrow=2, wide=5, fill="#000"):
    """Bars as one path string, drawn left to right from x."""
    parts, cx = [], float(x)
    for is_bar, is_wide in elements(text):
        w = wide if is_wide else narrow
        if is_bar:
            parts.append("M%.1f %.1fh%.1fv%.1fh-%.1fz" % (cx, y, w, height, w))
        cx += w
    return '<path d="%s" fill="%s"/>' % ("".join(parts), fill)


# ---------------------------------------------------------------- self-check
def decode(widths):
    """Independent decoder: list of (is_bar, run_length) -> text."""
    runs = [w for _, w in widths]
    thresh = (min(runs) + max(runs)) / 2.0
    bits = "".join("w" if w > thresh else "n" for w in runs)
    rev = {v: k for k, v in PATTERNS.items()}
    out, i = [], 0
    while i + 9 <= len(bits):
        ch = rev.get(bits[i:i + 9])
        if ch is None:
            return None
        out.append(ch)
        i += 10  # 9 elements + 1 gap
    s = "".join(out)
    if not (s.startswith("*") and s.endswith("*")):
        return None
    return s[1:-1]
