"""Checks for the API overlay. Run from the repository root:

    python -m support.apigen.test_overlay
"""

import os
import tempfile

from support.apigen import overlay
from support.apigen.generate import HEADER, mangle_prefixes, parse

PREFIXES = mangle_prefixes(open(HEADER).read())


def write(d, module, name, text):
    os.makedirs(os.path.join(d, module), exist_ok=True)
    with open(os.path.join(d, module, name + ".md"), "w") as fh:
        fh.write(text)


def test_function_doc_replaced():
    with tempfile.TemporaryDirectory() as d:
        write(d, "nfft", "nfft_trafo",
              "---\nsymbol: nfft_trafo\nkind: function\nsource: agent\n---\nNew text.\n")
        mods = parse()
        unmatched = overlay.apply(mods, overlay.load(d), PREFIXES)
        fn = next(f for f in mods[0].main.functions if f.name == "trafo")
        assert fn.doc == "New text.", fn.doc
        assert unmatched == []


def test_struct_and_member_docs_replaced():
    with tempfile.TemporaryDirectory() as d:
        write(d, "nfft", "nfft_plan",
              "---\nsymbol: nfft_plan\nkind: struct\nsource: agent\n---\n"
              "Plan text.\n\n### N_total\n\nMember text.\n")
        mods = parse()
        assert overlay.apply(mods, overlay.load(d), PREFIXES) == []
        st = next(s for s in mods[0].main.structs if s.name == "X(plan)")
        assert st.doc == "Plan text."
        mem = next(m for m in st.members if m.name == "N_total")
        assert mem.doc == "Member text."


def test_flag_doc_replaced():
    with tempfile.TemporaryDirectory() as d:
        write(d, "nfft", "PRE_PHI_HUT",
              "---\nsymbol: PRE_PHI_HUT\nkind: flag\nsource: agent\n---\nFlag text.\n")
        mods = parse()
        assert overlay.apply(mods, overlay.load(d), PREFIXES) == []
        flag = next(f for f in mods[0].flags if f.name == "PRE_PHI_HUT")
        assert flag.doc == "Flag text."


def test_unmatched_symbol_reported():
    with tempfile.TemporaryDirectory() as d:
        write(d, "nfft", "nfft_nope",
              "---\nsymbol: nfft_nope\nkind: function\nsource: agent\n---\nx\n")
        mods = parse()
        assert overlay.apply(mods, overlay.load(d), PREFIXES) == [("nfft", "nfft_nope")]


def test_missing_front_matter_rejected():
    with tempfile.TemporaryDirectory() as d:
        write(d, "nfft", "nfft_trafo", "No front matter.\n")
        try:
            overlay.load(d)
        except overlay.OverlayError:
            return
        raise AssertionError("expected OverlayError")


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
