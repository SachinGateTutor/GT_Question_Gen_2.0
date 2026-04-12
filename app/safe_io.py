"""Stdout/stderr helpers for Windows consoles that use legacy encodings (e.g. cp1252).

LLM and API text may contain any Unicode; writing via TextIOWrapper can raise
UnicodeEncodeError. Writing UTF-8 bytes to the underlying buffer avoids that.
"""
import sys


def safe_print(*args, sep: str = " ", end: str = "\n", file=None) -> None:
    """Print arbitrary Unicode without raising UnicodeEncodeError on narrow consoles."""
    file = file or sys.stdout
    line = sep.join(str(a) for a in args) + end
    buf = getattr(file, "buffer", None)
    if buf is not None:
        buf.write(line.encode("utf-8", errors="replace"))
        buf.flush()
        return
    try:
        file.write(line)
    except UnicodeEncodeError:
        file.write(line.encode("ascii", errors="replace").decode("ascii"))
