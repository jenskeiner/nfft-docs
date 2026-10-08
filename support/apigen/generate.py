"""Generate the API reference pages from include/nfft3.h.

The public API is declared once per module inside a `*_DEFINE_*API(...)` macro
and expanded three times, once per precision. This reads those macro bodies and
the expansion sites, and writes one Markdown page per module plus an index and a
coverage report.

Anything the classifier does not recognise raises `ParseError` with the line, so
a change to the header cannot silently drop a function.
"""

from __future__ import annotations

import json
import os
import re
from dataclasses import dataclass, field

HEADER = os.path.join("include", "nfft3.h")

PRECISIONS = ("FLOAT", "DOUBLE", "LONG_DOUBLE")

PRECISION_TYPES = {
    "FLOAT": ("float", "fftwf_complex"),
    "DOUBLE": ("double", "fftw_complex"),
    "LONG_DOUBLE": ("long double", "fftwl_complex"),
}

# FFTW's mangling macros live in fftw3.h and expand through FFTW_CONCAT, so they
# cannot be read out of nfft3.h.
FFTW_PREFIXES = {
    "FFTW_MANGLE_FLOAT": "fftwf_",
    "FFTW_MANGLE_DOUBLE": "fftw_",
    "FFTW_MANGLE_LONG_DOUBLE": "fftwl_",
}

# Modules in the order they are presented, with the page title and the macro
# that declares them. The three util and malloc macros mangle with
# NFFT_MANGLE_*, so they belong on the nfft page rather than on pages of their
# own.
MODULES = [
    ("nfft", "NFFT", "NFFT_DEFINE_API"),
    ("nfct", "NFCT", "NFCT_DEFINE_API"),
    ("nfst", "NFST", "NFST_DEFINE_API"),
    ("nnfft", "NNFFT", "NNFFT_DEFINE_API"),
    ("nsfft", "NSFFT", "NSFFT_DEFINE_API"),
    ("mri", "MRI", "MRI_DEFINE_API"),
    ("nfsft", "NFSFT", "NFSFT_DEFINE_API"),
    ("nfsoft", "NFSOFT", "NFSOFT_DEFINE_API"),
    ("fpt", "FPT", "FPT_DEFINE_API"),
    ("solver", "Solver", "SOLVER_DEFINE_API"),
]

EXTRA_SECTIONS = {
    "nfft": [("Memory management", "NFFT_DEFINE_MALLOC_API"),
             ("Utilities", "NFFT_DEFINE_UTIL_API")],
}


class ParseError(Exception):
    pass


# `/** */`, `/*!  */` and `/**< */` are documentation. A plain `/* */` is a
# section marker such as `/* internal use only */` and carries none.
DOC_COMMENT = re.compile(r"^/\*[*!]")


@dataclass
class Member:
    type: str
    name: str
    doc: str = ""


@dataclass
class Struct:
    name: str
    members: list[Member]
    doc: str = ""


@dataclass
class Function:
    name: str
    mangle: str  # the macro parameter that mangles it, X or Y
    ret: str
    args: str
    doc: str = ""


@dataclass
class Variable:
    type: str
    name: str
    mangle: str
    doc: str = ""


@dataclass
class Typedef:
    name: str
    mangle: str
    decl: str
    doc: str = ""


@dataclass
class Macro:
    name: str
    params: str
    body: str
    doc: str = ""


@dataclass
class Flag:
    name: str
    value: str
    doc: str = ""


@dataclass
class Section:
    title: str
    macro: str
    params: list[str]
    bindings: dict[str, dict[str, str]]
    structs: list[Struct] = field(default_factory=list)
    functions: list[Function] = field(default_factory=list)
    variables: list[Variable] = field(default_factory=list)
    typedefs: list[Typedef] = field(default_factory=list)


@dataclass
class Module:
    key: str
    title: str
    sections: list[Section]
    flags: list[Flag] = field(default_factory=list)
    macros: list[Macro] = field(default_factory=list)

    @property
    def main(self) -> Section:
        return self.sections[0]


# --- lexing -----------------------------------------------------------------


def strip_comments(text: str) -> str:
    """Replace every block comment with a space, keeping the line count."""
    out, i, n = [], 0, len(text)
    while i < n:
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            if end < 0:
                raise ParseError("unterminated comment")
            out.append(" " + "\n" * text.count("\n", i, end))
            i = end + 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out)


def macro_body(text: str, start: int) -> str:
    """Body of a macro definition starting at `start`, comment aware.

    A body line may end without a backslash when the newline sits inside a block
    comment: translation phase 3 replaces the comment with a single space before
    the directive is terminated in phase 4. See include/nfft3.h:116.
    """
    out, i, in_comment = [], start, False
    while i < len(text):
        if in_comment:
            if text.startswith("*/", i):
                in_comment, i = False, i + 2
                out.append("*/")
                continue
        elif text.startswith("/*", i):
            in_comment, i = True, i + 2
            out.append("/*")
            continue
        elif text[i] == "\\" and text[i + 1 : i + 2] == "\n":
            out.append("\n")
            i += 2
            continue
        elif text[i] == "\n":
            break
        out.append(text[i])
        i += 1
    return "".join(out)


def clean_doc(raw: str) -> str:
    """Turn a Doxygen comment body into Markdown.

    Relative indentation is preserved, so nested lists and indented blocks
    survive; only the common indent of the comment is removed.
    """
    raw = re.sub(r"^/\*[*!]<?", "", raw.strip())
    raw = re.sub(r"\*/$", "", raw).strip()

    lines = []
    for ln in raw.split("\n"):
        ln = re.sub(r"^[ \t]*\*(?!/)[ \t]?", "", ln).rstrip()
        # Strip exactly one line-continuation backslash. Stripping more would
        # eat a LaTeX `\\` row break; test_apigen rejects those in the header.
        lines.append(ln[:-1].rstrip() if ln.endswith("\\") else ln)

    # Remove the common indent, keep what is nested below it. The first line
    # sits right after the comment opener and has no indent of its own, so it
    # does not take part in the measurement.
    body = [ln for ln in lines[1:] if ln.strip()]
    indent = min((len(ln) - len(ln.lstrip()) for ln in body), default=0)
    text = "\n".join([lines[0]] + [ln[indent:] if ln.strip() else ""
                                   for ln in lines[1:]]).strip()

    text = text.replace("\\f[", "$$").replace("\\f]", "$$").replace("\\f$", "$")
    text = re.sub(r"\\(?:ref|e|b|c|a|p)\s+(?=\w)", "", text)
    text = re.sub(r"\\anchor\s+\w+\s*", "", text)
    # Markdown needs a blank line before a list that follows a paragraph, for
    # every list in the comment, not just the first. A line that is itself a
    # list item or a definition already opened the block, so it is left alone.
    # A `:` definition always follows its own term, so it needs no blank line.
    ITEM = r"[ \t]*(?:[-*+][ \t]|\d+\.[ \t])"
    text = re.sub(r"(?<=\S)\n(?=%s)" % ITEM,
                  lambda m: "\n" if re.match(ITEM, text[:m.start()].rsplit("\n", 1)[-1])
                  else "\n\n", text)
    return re.sub(r"\n{3,}", "\n\n", text)


def statements(body: str) -> list[tuple[str, str]]:
    """Split a macro or struct body into (statement, doc) pairs.

    Comments are scanned first and independently, so a `;` or an unbalanced `)`
    inside one cannot desynchronise the scan (include/nfft3.h:461 and :567).
    A `/**<` comment documents the statement before it, a `/**` comment the
    statement after it; anything else is not documentation.
    """
    items: list[list[str]] = []
    i, n = 0, len(body)
    buf, doc, depth, paren = [], "", 0, 0
    while i < n:
        if body.startswith("/*", i):
            end = body.find("*/", i + 2)
            if end < 0:
                raise ParseError("unterminated comment")
            comment, i = body[i : end + 2], end + 2
            if depth > 0 or "".join(buf).strip():
                buf.append(comment)  # inside a nested body, keep it in place
            elif comment.startswith("/**<"):
                if not items:
                    raise ParseError(f"trailing doc with nothing before it: {comment!r}")
                items[-1][1] = "\n\n".join(
                    x for x in (items[-1][1], clean_doc(comment)) if x)
            elif comment.startswith("/**") or comment.startswith("/*!"):
                if doc:
                    raise ParseError(
                        f"two doc comments before one statement: {comment!r}")
                doc = clean_doc(comment)
            elif DOC_COMMENT.match(comment):
                # A doc comment the placement rules cannot reach would be
                # dropped silently, which is how a whole module shifts by one.
                raise ParseError(f"doc comment in a place that documents "
                                 f"nothing: {comment!r}")
            continue
        c = body[i]
        if c == "{":
            depth += 1
        elif c == "}":
            depth -= 1
        elif c == "(":
            paren += 1
        elif c == ")":
            paren -= 1
        elif c == ";" and depth == 0 and paren == 0:
            text = "".join(buf)
            if text.strip():
                items.append([text, doc])
            buf, doc = [], ""
            i += 1
            continue
        buf.append(c)
        i += 1
    if "".join(buf).strip():
        raise ParseError(f"trailing text in body: {''.join(buf).strip()!r}")
    if doc:
        raise ParseError(f"doc comment after the last statement: {doc[:60]!r}")
    return [(text, doc) for text, doc in items]


def split_doc(text: str) -> tuple[str, str]:
    """Separate a statement's code from the doc comments embedded in it."""
    code, docs, i = [], [], 0
    while i < len(text):
        if text.startswith("/*", i):
            end = text.index("*/", i + 2) + 2
            comment = text[i:end]
            if comment.startswith("/**"):
                docs.append(clean_doc(comment))
            code.append(" ")
            i = end
            continue
        code.append(text[i])
        i += 1
    return "".join(code), "\n\n".join(d for d in docs if d)


def top_level_split(text: str, sep: str) -> list[str]:
    out, buf, depth = [], [], 0
    for c in text:
        if c in "([":
            depth += 1
        elif c in ")]":
            depth -= 1
        if c == sep and depth == 0:
            out.append("".join(buf))
            buf = []
        else:
            buf.append(c)
    out.append("".join(buf))
    return out


def unwrap(name: str) -> tuple[str, str]:
    """`X(trafo)` -> (`trafo`, `X`). A bare name mangles with X by convention."""
    m = re.fullmatch(r"([A-Z])\((\w+)\)", name)
    return (m.group(2), m.group(1)) if m else (name, "X")


DECL = re.compile(r"^(?P<type>.*?)(?P<name>[A-Z]\(\w+\)|[A-Za-z_]\w*)"
                  r"(?P<dims>(?:\s*\[[^\]]*\])*)\s*$")


def parse_declarator(text: str) -> tuple[str, str]:
    """Split `R *sigma`, `R X(full_psi_eps)` or `R t[3]` into (type, name)."""
    text = " ".join(text.split())
    m = DECL.match(text)
    if not m:
        raise ParseError(f"cannot read declarator: {text!r}")
    type_ = (m.group("type").strip() + m.group("dims").replace(" ", "")).strip()
    return type_ or "int", m.group("name")


FUNC_PTR = re.compile(r"^(?P<ret>.+?)\(\s*\*\s*(?P<name>[A-Z]\(\w+\)|[A-Za-z_]\w*)\s*\)"
                      r"\s*\((?P<args>.*)\)$", re.S)
# A prototype's name is followed by its argument list. `X(malloc_type_function)
# X(malloc_hook);` has no such list and is a variable, so the name pattern must
# not fall back to the bare macro parameter letter.
FUNC = re.compile(r"^(?P<ret>.*?)(?P<name>[A-Z]\(\w+\)|\b[a-z_]\w*)\s*"
                  r"\((?P<args>[^()]*(?:\([^()]*\)[^()]*)*)\)$", re.S)


def parse_members(body: str) -> list[Member]:
    members = []
    for text, above in statements(body):
        code, trailing = split_doc(text)
        doc = "\n\n".join(d for d in (above, trailing) if d)
        code = " ".join(code.split())
        if not code:
            continue
        m = FUNC_PTR.match(code)
        if m:
            members.append(Member(f"{m.group('ret').strip()}(*)({m.group('args')})",
                                  m.group("name"), doc))
            continue
        parts = top_level_split(code, ",")
        # `R *x_102,*x_201,...`: the declarators after the first carry only their
        # own pointer stars, so re-attach the base type without them.
        base = parse_declarator(parts[0])[0].rstrip("* ")
        for part in parts:
            part = part.strip()
            if part.startswith("*"):
                part = base + " " + part
            type_, name = parse_declarator(part)
            members.append(Member(type_, name, doc))
    return members


# A type is qualifiers, one name that may be a mangling macro call, and stars.
TYPE = re.compile(r"^(?:(?:const|unsigned|signed|long|short|struct)\s+)*"
                  r"(?:[A-Za-z_]\w*|[A-Z]\(\w+\))[\s*]*$")

STRUCT = re.compile(r"^typedef\s+struct\s*(?:[A-Za-z_]\w*|[A-Z]\(\w+\))?\s*"
                    r"\{(?P<body>.*)\}\s*(?P<name>[A-Z]\(\w+\)|\w+)$", re.S)
OPAQUE = re.compile(r"^typedef\s+struct\s+(?:[A-Za-z_]\w*|[A-Z]\(\w+\))\s*\*\s*"
                    r"(?P<name>[A-Z]\(\w+\)|\w+)$", re.S)


def parse_section(title: str, macro: str, src: str) -> Section:
    m = re.search(r"^#define\s+%s\((?P<params>[^)]*)\)" % re.escape(macro), src, re.M)
    if not m:
        raise ParseError(f"macro {macro} not found")
    params = [p.strip() for p in m.group("params").split(",")]
    body = macro_body(src, src.index("\n", m.end()) + 1)
    body = expand_mv_plan(body)

    bindings = {}
    for site in re.finditer(r"^%s\((?P<args>[^)]*)\)\s*$" % re.escape(macro), src, re.M):
        args = [a.strip() for a in site.group("args").split(",")]
        if len(args) != len(params):
            raise ParseError(f"{macro} expanded with {len(args)} of {len(params)} args")
        env = dict(zip(params, args))
        prec = precision_of(env, params)
        bindings[prec] = env
    if set(bindings) != set(PRECISIONS):
        raise ParseError(f"{macro} expanded for {sorted(bindings)}, expected all three")

    sec = Section(title, macro, params, bindings)
    for text, above in statements(body):
        code, trailing = split_doc(text)
        code = code.strip()
        if not code:
            continue
        s = STRUCT.match(text.strip())
        if s:
            # The comments inside the braces belong to the members, not here.
            sec.structs.append(
                Struct(s.group("name"), parse_members(s.group("body")), above))
            continue
        doc = "\n\n".join(d for d in (above, trailing) if d)
        flat = " ".join(code.split())
        o = OPAQUE.match(flat)
        if o:
            sec.typedefs.append(Typedef(*unwrap(o.group("name")), flat, doc))
            continue
        if flat.startswith("typedef "):
            f = FUNC_PTR.match(flat[len("typedef "):])
            if not f:
                raise ParseError(f"unknown typedef in {macro}: {flat!r}")
            sec.typedefs.append(Typedef(*unwrap(f.group("name")), flat, doc))
            continue
        flat = re.sub(r"^NFFT_EXTERN\s+", "", flat)
        f = FUNC.match(flat)
        if f:
            if not TYPE.match(f.group("ret").strip()):
                raise ParseError(f"unexpected return type in {macro}: {flat!r}")
            name, mangle = unwrap(f.group("name"))
            sec.functions.append(Function(name, mangle, f.group("ret").strip(),
                                          " ".join(f.group("args").split()), doc))
            continue
        type_, name = parse_declarator(flat)
        sec.variables.append(Variable(type_, *unwrap(name), doc))
    return sec


def expand_mv_plan(body: str) -> str:
    """Inline MACRO_MV_PLAN(RC), the only nested macro used inside the bodies."""
    src = open(HEADER).read()
    m = re.search(r"^#define\s+MACRO_MV_PLAN\((\w+)\)", src, re.M)
    if not m:
        raise ParseError("MACRO_MV_PLAN not found")
    param = m.group(1)
    template = macro_body(src, src.index("\n", m.end()) + 1)
    def sub(match):
        return re.sub(r"\b%s\b" % param, match.group(1), template)
    return re.sub(r"MACRO_MV_PLAN\((\w+)\)", sub, body)


def precision_of(env: dict[str, str], params: list[str]) -> str:
    for key in ("X", "Y", "Z"):
        arg = env.get(key, "")
        for prec in ("LONG_DOUBLE", "FLOAT", "DOUBLE"):
            if arg.endswith("_MANGLE_" + prec):
                return prec
    raise ParseError(f"cannot tell the precision of {env}")


MANGLE = re.compile(r"^#define\s+(?P<macro>\w+_MANGLE_\w+)\(name\)\s+"
                    r"NFFT_CONCAT\((?P<prefix>\w+),\s*name\)", re.M)


def mangle_prefixes(src: str) -> dict[str, str]:
    out = dict(FFTW_PREFIXES)
    for m in MANGLE.finditer(src):
        out[m.group("macro")] = m.group("prefix")
    return out


FLAG = re.compile(r"^#define\s+(?P<name>[A-Z][A-Z0-9_]*)\s+(?P<value>\(.*\))\s*$", re.M)
HELPER = re.compile(r"^#define\s+(?P<name>[A-Z][A-Z0-9_]*)\((?P<params>[^)]*)\)\s+"
                    r"(?P<body>.+)$", re.M)


DEFINE_API = re.compile(r"^#define\s+\w+_DEFINE_\w*API\(", re.M)


def parse_module_extras(src: str, macro: str):
    """Flags and helper macros between this module's last expansion and the next.

    The region ends at the next `*_DEFINE_*API` definition in file order, not at
    the next entry of MODULES; the two orders differ (fpt is declared between
    nfsft and nfsoft).
    """
    start = src.rindex(f"\n{macro}(")
    ends = [m.start() for m in DEFINE_API.finditer(src) if m.start() > start]
    region = src[start : ends[0] if ends else len(src)]
    flags = [Flag(m.group("name"), m.group("value"), preceding_doc(region, m.start()))
             for m in FLAG.finditer(region)]
    macros = [Macro(m.group("name"), m.group("params"), m.group("body").strip(),
                    preceding_doc(region, m.start()))
              for m in HELPER.finditer(region)
              if "_MANGLE_" not in m.group("name")]
    return flags, macros


def preceding_doc(text: str, pos: int) -> str:
    """The `/** */` comment that ends right before `pos`, or an empty string."""
    end = text.rfind("*/", 0, pos)
    if end < 0 or text[end + 2 : pos].strip():
        return ""
    comment = text[text.rfind("/*", 0, end) : end + 2]
    return clean_doc(comment) if comment.startswith("/**") else ""


def parse(path: str = HEADER) -> list[Module]:
    src = open(path).read()
    modules = []
    for key, title, macro in MODULES:
        sections = [parse_section(title, macro, src)]
        for extra_title, extra_macro in EXTRA_SECTIONS.get(key, []):
            sections.append(parse_section(extra_title, extra_macro, src))
        flags, macros = parse_module_extras(src, macro)
        modules.append(Module(key, title, sections, flags, macros))
    return modules


# --- rendering --------------------------------------------------------------


def mangled(section: Section, name: str, mangle: str, prec: str,
            prefixes: dict[str, str]) -> str:
    if mangle not in section.bindings[prec]:
        mangle = "Y"  # the util macro takes the nfft mangling macro as Y
    return prefixes[section.bindings[prec][mangle]] + name


def bind(text: str, section: Section, prec: str, prefixes: dict[str, str]) -> str:
    """Substitute the macro parameters of a signature for one precision."""
    env = section.bindings[prec]
    real, complex_ = PRECISION_TYPES[prec]

    def macro_call(m):
        arg = env.get(m.group(1))
        if arg is None:
            return m.group(0)
        return prefixes[arg] + m.group(2)

    text = re.sub(r"\b([XYZ])\((\w+)\)", macro_call, text)
    for param, value in env.items():
        if value in ("float", "double", "long double"):
            text = re.sub(r"\b%s\b" % param, real, text)
        elif value.endswith("_complex"):
            text = re.sub(r"\b%s\b" % param, complex_, text)
    return text


def signature(fn: Function, section: Section, prec: str, prefixes: dict[str, str]) -> str:
    ret = bind(fn.ret, section, prec, prefixes)
    args = bind(fn.args, section, prec, prefixes)
    if not ret.endswith("*"):
        ret += " "
    return f"{ret}{mangled(section, fn.name, fn.mangle, prec, prefixes)}({args});"


def render_members(struct: Struct, out: list[str]) -> None:
    out.append("| Type | Member | Description |")
    out.append("|------|--------|-------------|")
    for mem in struct.members:
        doc = " ".join(mem.doc.split()).replace("|", r"\|") or "&mdash;"
        out.append(f"| `{mem.type}` | `{mem.name}` | {doc} |")
    out.append("")


def render_module(mod: Module, prefixes: dict[str, str]) -> str:
    out = [f"# {mod.title} API", ""]
    names = ", ".join(f"`{mangled(mod.main, '', 'X', p, prefixes)}`" for p in PRECISIONS)
    out += [
        f"Declared in `include/nfft3.h` by the `{mod.main.macro}` macro, expanded "
        f"once per precision with the prefixes {names}.",
        "",
        "In the signatures below, `R` is the real type of the precision and `C` "
        "the matching FFTW complex type. See the [index](index.md) for the "
        "mangling rules.",
        "",
    ]

    for sec in mod.sections:
        if len(mod.sections) > 1:
            out += [f"## {sec.title}", ""]
        depth = "###" if len(mod.sections) > 1 else "##"

        for struct in sec.structs:
            plain = re.sub(r"^[A-Z]\((\w+)\)$", r"\1", struct.name)
            out += [f"{depth} `{plain}`", ""]
            if struct.doc:
                out += [struct.doc, ""]
            if struct.members:
                render_members(struct, out)

        for td in sec.typedefs:
            triple = " / ".join(f"`{mangled(sec, td.name, td.mangle, p, prefixes)}`"
                                for p in PRECISIONS)
            out += [f"{depth} `{td.name}`", "", triple, ""]
            if td.doc:
                out += [td.doc, ""]
            out += ["```c", bind(td.decl, sec, "DOUBLE", prefixes) + ";", "```", ""]

        for var in sec.variables:
            triple = " / ".join(f"`{mangled(sec, var.name, var.mangle, p, prefixes)}`"
                                for p in PRECISIONS)
            out += [f"{depth} `{var.name}`", "", triple, ""]
            if var.doc:
                out += [var.doc, ""]
            decl = bind(var.type, sec, "DOUBLE", prefixes)
            out += ["```c",
                    f"{decl} {mangled(sec, var.name, var.mangle, 'DOUBLE', prefixes)};",
                    "```", ""]

        for fn in sec.functions:
            triple = " / ".join(f"`{mangled(sec, fn.name, fn.mangle, p, prefixes)}`"
                                for p in PRECISIONS)
            out += [f"{depth} `{fn.name}`", "", triple, ""]
            if fn.doc:
                out += [fn.doc, ""]
            for prec, label in zip(PRECISIONS, ("float", "double", "long double")):
                out += [f'=== "{label}"', "",
                        "    ```c",
                        "    " + signature(fn, sec, prec, prefixes),
                        "    ```", ""]

    if mod.flags:
        out += ["## Flags", ""]
        for f in mod.flags:
            out += [f"`{f.name}`", f":   Value `{f.value}`.", ""]
            out += indent_doc(f.doc)
        out.append("")

    if mod.macros:
        out += ["## Macros", ""]
        for m in mod.macros:
            out += [f"`{m.name}({m.params})`", f":   Definition `{m.body}`.", ""]
            out += indent_doc(m.doc)
        out.append("")

    return "\n".join(out) + "\n"


def coverage(modules: list[Module]) -> dict:
    data = {"generated_from": HEADER, "modules": {}}
    totals = {"functions": 0, "documented": 0, "members": 0, "members_documented": 0,
              "flags": 0, "flags_documented": 0}
    for mod in modules:
        fns, undoc, members, mem_undoc = 0, [], 0, 0
        for sec in mod.sections:
            for fn in sec.functions:
                fns += 1
                if not fn.doc:
                    undoc.append(fn.name)
            for struct in sec.structs:
                for mem in struct.members:
                    members += 1
                    mem_undoc += not mem.doc
        consts = mod.flags + mod.macros
        const_undoc = [c.name for c in consts if not c.doc]
        data["modules"][mod.key] = {
            "functions": fns,
            "undocumented_functions": sorted(undoc),
            "members": members,
            "undocumented_members": mem_undoc,
            "flags_and_macros": len(consts),
            "undocumented_flags_and_macros": const_undoc,
        }
        totals["functions"] += fns
        totals["documented"] += fns - len(undoc)
        totals["members"] += members
        totals["members_documented"] += members - mem_undoc
        totals["flags"] += len(consts)
        totals["flags_documented"] += len(consts) - len(const_undoc)
    data["totals"] = totals
    return data


def indent_doc(doc: str) -> list[str]:
    """A description as the continuation of a definition list entry."""
    if not doc:
        return []
    return [("    " + ln if ln.strip() else "") for ln in doc.split("\n")] + [""]


def render_index(modules: list[Module], cov: dict, prefixes: dict[str, str]) -> str:
    out = [
        "# API reference",
        "",
        "The reference covers the two installed headers. `include/nfft3.h` declares",
        "the functions and structures, and the module pages below are generated from",
        "it. `include/nfft3mp.h` provides the precision-agnostic macros, described in",
        "[Precision and name mangling](../guide/precision.md). Nothing else is public:",
        "the application libraries and `kernel/` are not installed.",
        "",
        "Do not edit the generated pages by hand; run",
        "`uv run python -m support.apigen` from the repository root.",
        "",
        "## Name mangling",
        "",
        "The library compiles in three precisions and all three can be linked into",
        "the same program, so every exported name carries a precision prefix.",
        "The same function appears three times. Only NFFT, NFCT, NFST, the solver",
        "and the utilities are built in all three precisions; the other modules",
        "exist in double precision only:",
        "",
        "| Precision | Real type `R` | Complex type `C` | NFFT prefix |",
        "|-----------|---------------|------------------|-------------|",
    ]
    main = modules[0].main
    for prec, label in zip(PRECISIONS, ("float", "double", "long double")):
        real, cplx = PRECISION_TYPES[prec]
        out.append(f"| {label} | `{real}` | `{cplx}` | "
                   f"`{prefixes[main.bindings[prec]['X']]}` |")
    out += [
        "",
        "Include `nfft3mp.h` instead of `nfft3.h` to write precision-agnostic code:",
        "define one of `NFFT_PRECISION_SINGLE`, `NFFT_PRECISION_DOUBLE` or",
        "`NFFT_PRECISION_LONG_DOUBLE` and write `NFFT(trafo)` for the mangled name.",
        "See [Precision and name mangling](../guide/precision.md).",
        "",
        "## Modules",
        "",
        "| Module | Functions | Documented |",
        "|--------|-----------|------------|",
    ]
    for mod in modules:
        c = cov["modules"][mod.key]
        out.append(f"| [{mod.title}]({mod.key}.md) | {c['functions']} | "
                   f"{c['functions'] - len(c['undocumented_functions'])} |")
    t = cov["totals"]
    out += [
        f"| **Total** | **{t['functions']}** | **{t['documented']}** |",
        "",
        "## Documentation coverage",
        "",
        f"{t['documented']} of {t['functions']} functions and "
        f"{t['members_documented']} of {t['members']} structure members carry a",
        f"description, and so do {t['flags_documented']} of {t['flags']} flags and",
        "helper macros. The machine-readable report is",
        "[`coverage.json`](coverage.json).",
        "",
    ]
    missing = [(mod.title, mod.key, cov["modules"][mod.key]["undocumented_functions"])
               for mod in modules]
    missing = [m for m in missing if m[2]]
    if missing:
        out += ["Functions still without a description:", ""]
        for title, key, names in missing:
            out.append(f"- **{title}**: " + ", ".join(f"`{n}`" for n in names))
        out.append("")
    missing = [(mod.title, cov["modules"][mod.key]["undocumented_flags_and_macros"])
               for mod in modules]
    missing = [m for m in missing if m[1]]
    if missing:
        out += ["Flags and macros still without a description:", ""]
        for title, names in missing:
            out.append(f"- **{title}**: " + ", ".join(f"`{n}`" for n in names))
        out.append("")
    return "\n".join(out) + "\n"


def main(out_dir: str = os.path.join("doc", "api")) -> None:
    src = open(HEADER).read()
    prefixes = mangle_prefixes(src)
    modules = parse()
    cov = coverage(modules)

    os.makedirs(out_dir, exist_ok=True)
    for mod in modules:
        with open(os.path.join(out_dir, f"{mod.key}.md"), "w") as fh:
            fh.write(render_module(mod, prefixes))
    with open(os.path.join(out_dir, "index.md"), "w") as fh:
        fh.write(render_index(modules, cov, prefixes))
    with open(os.path.join(out_dir, "coverage.json"), "w") as fh:
        json.dump(cov, fh, indent=2, sort_keys=True)
        fh.write("\n")

    t = cov["totals"]
    print(f"{len(modules)} modules, {t['functions']} functions "
          f"({t['documented']} documented), {t['members']} members "
          f"({t['members_documented']} documented) -> {out_dir}")
