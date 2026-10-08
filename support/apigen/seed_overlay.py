"""Seed overlay/api/ from a header that carries more doc text than the submodule.

    python -m support.apigen.seed_overlay path/to/nfft3.h

Writes one file per symbol whose text differs from the submodule header, with
`source: header`. Existing overlay files are overwritten. One-off tool.
"""

import os
import sys

from support.apigen import overlay
from support.apigen.generate import mangle_prefixes, parse


def items_of(modules, prefixes):
    for mod in modules:
        for sec in mod.sections:
            for item in sec.structs + sec.typedefs + sec.variables + sec.functions:
                yield mod.key, overlay.key_of(sec, item, prefixes), item
        for item in mod.flags + mod.macros:
            yield mod.key, item.name, item


def kind_of(item):
    if hasattr(item, "members"):
        return "struct"
    if hasattr(item, "args"):
        return "function"
    if hasattr(item, "decl"):
        return "typedef"
    if hasattr(item, "params"):
        return "macro"
    if hasattr(item, "value"):
        return "flag"
    return "variable"


def main(src_header: str, out_root: str = overlay.ROOT) -> int:
    prefixes = mangle_prefixes(open(src_header).read())
    base = {(m, k): it for m, k, it in items_of(parse(), prefixes)}
    written = 0
    for mod, key, item in items_of(parse(src_header), prefixes):
        have = base.get((mod, key))
        body = item.doc if (have is None or item.doc != have.doc) else ""
        members = {}
        for mem in getattr(item, "members", []):
            old = next((o for o in getattr(have, "members", []) if o.name == mem.name), None)
            if mem.doc and (old is None or old.doc != mem.doc):
                members[mem.name] = mem.doc
        if not body and not members:
            continue
        os.makedirs(os.path.join(out_root, mod), exist_ok=True)
        with open(os.path.join(out_root, mod, key + ".md"), "w") as fh:
            fh.write(f"---\nsymbol: {key}\nkind: {kind_of(item)}\nsource: header\n---\n")
            if body:
                fh.write(body + "\n")
            for name, doc in members.items():
                fh.write(f"\n### {name}\n\n{doc}\n")
        written += 1
    print(f"{written} overlay files written to {out_root}")
    return 0


if __name__ == "__main__":
    sys.exit(main(*sys.argv[1:]))
