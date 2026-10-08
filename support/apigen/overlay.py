"""Doc text for API symbols that the header lacks, merged over the parse.

One file per symbol under overlay/api/<module>/<key>.md, where key is the
double-precision mangled name (`nfft_trafo`, `nfft_plan`) or the plain name of
a flag or helper macro. Front matter names the symbol, its kind and whether the
text was seeded from a header or written by an agent. A struct file carries the
struct text, then one `### member` section per documented member.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field

from support.apigen.generate import Module, Section, mangled, unwrap

ROOT = os.path.join("overlay", "api")
FRONT = re.compile(r"\A---\n(?P<head>.*?)\n---\n(?P<body>.*)\Z", re.S)
MEMBER = re.compile(r"^### +`?(?P<name>[\w()]+)`?\s*$", re.M)


class OverlayError(Exception):
    pass


@dataclass
class Overlay:
    symbol: str
    kind: str
    source: str
    body: str
    members: dict[str, str] = field(default_factory=dict)


def _parse(path: str) -> Overlay:
    m = FRONT.match(open(path).read())
    if not m:
        raise OverlayError(f"{path}: missing front matter")
    head = dict(ln.split(":", 1) for ln in m.group("head").splitlines() if ":" in ln)
    head = {k.strip(): v.strip() for k, v in head.items()}
    for key in ("symbol", "kind", "source"):
        if not head.get(key):
            raise OverlayError(f"{path}: front matter lacks {key}")
    parts = MEMBER.split(m.group("body"))
    body = parts[0].strip()
    members = {parts[i]: parts[i + 1].strip() for i in range(1, len(parts), 2)}
    return Overlay(head["symbol"], head["kind"], head["source"], body, members)


def load(root: str = ROOT) -> dict[tuple[str, str], Overlay]:
    out = {}
    if not os.path.isdir(root):
        return out
    for module in sorted(os.listdir(root)):
        mdir = os.path.join(root, module)
        for name in sorted(os.listdir(mdir)):
            if name.endswith(".md"):
                ov = _parse(os.path.join(mdir, name))
                if ov.symbol != name[:-3]:
                    raise OverlayError(f"{mdir}/{name}: symbol {ov.symbol!r} differs from the file name")
                out[(module, ov.symbol)] = ov
    return out


def key_of(section: Section, item, prefixes: dict[str, str]) -> str:
    """The overlay key of a parsed item: the double-precision public name."""
    if hasattr(item, "mangle"):
        return mangled(section, item.name, item.mangle, "DOUBLE", prefixes)
    if hasattr(item, "members"):
        if re.fullmatch(r"[A-Z]\(\w+\)", item.name):
            return mangled(section, *unwrap(item.name), "DOUBLE", prefixes)
        return item.name
    return item.name


def apply(modules: list[Module], entries: dict[tuple[str, str], Overlay],
          prefixes: dict[str, str]) -> list[tuple[str, str]]:
    """Replace the doc of every matched symbol. Returns the keys matched nothing."""
    seen = set()
    for mod in modules:
        for sec in mod.sections:
            for item in sec.structs + sec.typedefs + sec.variables + sec.functions:
                key = (mod.key, key_of(sec, item, prefixes))
                ov = entries.get(key)
                if ov is None:
                    continue
                seen.add(key)
                if ov.body:
                    item.doc = ov.body
                for mem in getattr(item, "members", []):
                    if mem.name in ov.members:
                        mem.doc = ov.members[mem.name]
        for item in mod.flags + mod.macros:
            key = (mod.key, item.name)
            if key in entries:
                seen.add(key)
                item.doc = entries[key].body
    return sorted(set(entries) - seen)
