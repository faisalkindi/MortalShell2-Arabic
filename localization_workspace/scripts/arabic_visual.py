"""Logical Arabic -> visual-order presentation forms, for text drawn by Unreal's CANVAS subtitle renderer.

Why: SoundWave subtitles (cutscene VO) are drawn by the engine's canvas text path, which lays text out
left-to-right with no bidi reordering, so logical Arabic comes out mirrored. Feeding it text that is already
shaped (Arabic Presentation Forms-B, which HarfBuzz leaves alone) and already in visual order makes the
LTR drawing read correctly. Only for short pure-Arabic lines; no Latin/digits/brackets are handled.
Needs: pip install arabic-reshaper
"""
import unicodedata
from arabic_reshaper import ArabicReshaper

_R = ArabicReshaper(configuration={"delete_harakat": False, "support_ligatures": True})
ALLOWED = lambda c: c == " " or c in ".،؟!:؛…-" or "\uFB50" <= c <= "\uFDFF" or "\uFE70" <= c <= "\uFEFC" or unicodedata.category(c) == "Mn"

def to_visual(s):
    shaped = _R.reshape(s)
    clusters = []
    for ch in shaped:
        if unicodedata.category(ch) == "Mn" and clusters:     # marks stay after their base in LTR drawing
            clusters[-1] += ch
        else:
            clusters.append(ch)
    out = "".join(reversed(clusters))
    bad = [c for c in out if not ALLOWED(c)]
    if bad:
        raise ValueError(f"unsupported characters {bad!r} in {s!r}")
    return out
