"""Checks for the API generator. Run from the repository root:

    python -m support.apigen.test_apigen
"""

import glob
import os
import re

from support.apigen.generate import (
    HEADER, ParseError, clean_doc, mangle_prefixes, parse, parse_section,
    render_module, signature,
)

MODULES = parse()
BY_KEY = {m.key: m for m in MODULES}
PREFIXES = mangle_prefixes(open(HEADER).read())


def test_module_set():
    assert list(BY_KEY) == ["nfft", "nfct", "nfst", "nnfft", "nsfft", "mri",
                            "nfsft", "nfsoft", "fpt", "solver"]
    # The malloc and util APIs mangle with NFFT_MANGLE_*, so they are sections
    # of the nfft page rather than modules.
    assert [s.title for s in BY_KEY["nfft"].sections] == [
        "NFFT", "Memory management", "Utilities"]


def test_prototype_counts():
    """The per-macro counts measured in ledger item 0.4."""
    expected = {"nfft": 23 + 3 + 22, "nfct": 16, "nfst": 16, "nnfft": 13,
                "nsfft": 8, "mri": 8, "nfsft": 11, "nfsoft": 8, "fpt": 7,
                "solver": 10}
    got = {k: sum(len(s.functions) for s in m.sections) for k, m in BY_KEY.items()}
    assert got == expected, got
    assert sum(got.values()) == 145


def test_inherited_members_are_expanded():
    """MACRO_MV_PLAN is a separate macro; without expansion these are missing."""
    plan = next(s for s in BY_KEY["nfft"].main.structs if s.name == "X(plan)")
    names = [m.name for m in plan.members]
    assert names[:6] == ["N_total", "M_total", "f_hat", "f", "mv_trafo", "mv_adjoint"]
    assert names == [
        "N_total", "M_total", "f_hat", "f", "mv_trafo", "mv_adjoint",
        "d", "N", "sigma", "n", "n_total", "m", "b", "K", "flags", "fftw_flags",
        "x", "MEASURE_TIME_t", "my_fftw_plan1", "my_fftw_plan2", "c_phi_inv",
        "psi", "psi_index_g", "psi_index_f", "g", "g_hat", "g1", "g2",
        "spline_coeffs", "index_x"], names
    assert dict((m.name, m.type) for m in plan.members)["mv_trafo"] == "void(*)(void*)"


def test_multi_line_prototype_signature():
    sec = BY_KEY["nfft"].main
    fn = next(f for f in sec.functions if f.name == "init_guru")
    assert signature(fn, sec, "LONG_DOUBLE", PREFIXES) == (
        "void nfftl_init_guru(nfftl_plan *ths, int d, int *N, int M, int *n, "
        "int m, unsigned flags, unsigned fftw_flags);")
    assert signature(fn, sec, "FLOAT", PREFIXES).startswith("void nfftf_init_guru(")


def test_fftw_and_nfft_types_in_one_signature():
    """nnfft binds X, Y and Z at once; Z(plan) must become the nfft plan."""
    sec = BY_KEY["nnfft"].main
    plan = next(s for s in sec.structs if s.name == "X(plan)")
    direct = next(m for m in plan.members if m.name == "direct_plan")
    assert direct.type == "Z(plan) *"
    fn = next(f for f in sec.functions if f.name == "init_1d")
    assert signature(fn, sec, "DOUBLE", PREFIXES) == (
        "void nnfft_init_1d(nnfft_plan *ths_plan, int N, int M_total);")


def test_declaration_shapes():
    """The malloc API mixes prototypes, typedefs and plain variables."""
    sec = next(s for s in BY_KEY["nfft"].sections if s.title == "Memory management")
    assert [f.name for f in sec.functions] == ["malloc", "free", "die"]
    assert [t.name for t in sec.typedefs] == [
        "malloc_type_function", "free_type_function", "die_type_function"]
    assert [v.name for v in sec.variables] == ["malloc_hook", "free_hook", "die_hook"]


def test_odd_member_shapes():
    """A mangled member name, and four declarators sharing one comment."""
    nfst = next(s for s in BY_KEY["nfst"].main.structs if s.name == "X(plan)")
    assert "X(full_psi_eps)" in [m.name for m in nfst.members]
    nsfft = next(s for s in BY_KEY["nsfft"].main.structs if s.name == "X(plan)")
    exchanged = [m for m in nsfft.members if m.name[2:3].isdigit()]
    assert [m.name for m in exchanged] == ["x_102", "x_201", "x_120", "x_021"]
    assert all(m.type == "R *" for m in exchanged)
    assert all("coordinate exchanged nodes" in m.doc for m in exchanged)


def test_opaque_and_two_struct_modules():
    assert [t.name for t in BY_KEY["fpt"].main.typedefs] == ["set"]
    assert [s.name for s in BY_KEY["fpt"].main.structs] == []
    assert [s.name for s in BY_KEY["mri"].main.structs] == [
        "X(inh_2d1d_plan)", "X(inh_3d_plan)"]
    assert [s.name for s in BY_KEY["solver"].main.structs] == [
        "X(plan_complex)", "X(plan_double)"]


def test_doc_text_is_markdown():
    """No continuation backslashes, no comment asterisks, no Doxygen math."""
    plan = next(s for s in BY_KEY["nfft"].main.structs if s.name == "X(plan)")
    n = next(m for m in plan.members if m.name == "n")
    assert n.doc == ("Length of FFTW transforms. This is equal to sigma*N. "
                     "The default\nis to use a power of two that satifies  "
                     "$2\\le\\sigma<4$.")
    psi_index = next(m for m in plan.members if m.name == "psi_index_g")
    assert psi_index.doc == "Indices in source/target vector for PRE_FULL_PSI"
    for mod in MODULES:
        for sec in mod.sections:
            docs = ([s.doc for s in sec.structs] + [f.doc for f in sec.functions]
                    + [m.doc for s in sec.structs for m in s.members])
            for doc in docs:
                for leftover in ("\\f$", "\\f[", "\\f]", "\\ref", "@defgroup"):
                    assert leftover not in doc, (leftover, doc)
                assert "\\\n" not in doc and not doc.rstrip().endswith("\\"), doc
                assert "\n * " not in doc, doc


def test_flags_belong_to_their_module():
    """fpt is declared between nfsft and nfsoft, so file order decides."""
    assert [f.name for f in BY_KEY["nfsft"].flags][0] == "NFSFT_NORMALIZED"
    assert all(f.name.startswith("NFSFT_") for f in BY_KEY["nfsft"].flags)
    assert all(f.name.startswith("FPT_") for f in BY_KEY["fpt"].flags)
    nfft_flags = [f.name for f in BY_KEY["nfft"].flags]
    assert "PRE_PHI_HUT" in nfft_flags and "PRE_ONE_PSI" in nfft_flags
    composite = next(f for f in BY_KEY["nfft"].flags if f.name == "PRE_ONE_PSI")
    assert composite.value == "(PRE_LIN_PSI| PRE_FG_PSI| PRE_PSI| PRE_FULL_PSI)"


def test_helper_macros_are_kept():
    assert [m.name for m in BY_KEY["nfsft"].macros] == [
        "NFSFT_INDEX", "NFSFT_F_HAT_SIZE"]
    assert [m.name for m in BY_KEY["nfsoft"].macros] == [
        "NFSOFT_INDEX", "NFSOFT_F_HAT_SIZE"]


def test_documented_count_is_exact():
    """A misplaced comment silently documents the wrong function, so the count
    is asserted exactly rather than as a lower bound."""
    documented = sum(1 for m in MODULES for s in m.sections
                     for f in s.functions if f.doc)
    assert documented == 145, documented
    assert sum(1 for m in MODULES for s in m.sections
               for f in s.functions) == 145


def test_every_flag_and_macro_is_documented_once():
    """Flag docs live above the #define in the header. support/*.dox must not
    repeat them or Doxygen shows every description twice."""
    for m in MODULES:
        for c in m.flags + m.macros:
            assert c.doc, f"{c.name} has no description"
    for path in glob.glob("support/*.dox"):
        for name in re.findall(r"\\def\s+(\w+)", open(path).read()):
            assert name == "MACRO_MV_PLAN", f"{path} documents {name}"


def test_documented_parameters_match_the_prototype():
    for m in MODULES:
        for sec in m.sections:
            for f in sec.functions:
                args = [a.strip() for a in re.split(r",(?![^()]*\))", f.args)
                        if a.strip() and a.strip() != "void"]
                names = {re.search(r"(\w+)\s*(\[\])?\s*$", a).group(1) for a in args}
                documented = set(re.findall(r"^`([^`]+)`\n:", f.doc, re.M))
                assert documented <= names, (f.name, documented - names)


def test_migrated_docs_and_parameters():
    sec = BY_KEY["nfft"].main
    init = next(f for f in sec.functions if f.name == "init_guru")
    assert init.doc.startswith("Initialisation of a transform plan")
    assert "Parameters:" in init.doc
    assert "`fftw_flags`" in init.doc and "`ths`" in init.doc
    # The parameter list must be a definition list with its own blank lines,
    # or it renders as one run-on paragraph.
    assert "\n\n`ths`\n:   " in init.doc, repr(init.doc)
    fpt = next(f for f in BY_KEY["fpt"].main.functions if f.name == "precompute")
    assert "$" in fpt.doc, fpt.doc


def test_no_doxygen_markup_left_in_the_header():
    src = open(HEADER).read()
    for leftover in ("\\f$", "\\f[", "\\f]", "\\ref ", "\\arg ", "\\author",
                     "\\anchor", "@defgroup"):
        assert leftover not in src, leftover


def test_no_latex_row_break_at_a_line_end():
    """`clean_doc` strips one trailing backslash as a line continuation, so a
    LaTeX `\\\\` row break at a line end would be silently corrupted."""
    bad = [i + 1 for i, ln in enumerate(open(HEADER).read().split("\n"))
           if ln.rstrip().endswith("\\\\")]
    assert not bad, f"lines ending in a double backslash: {bad}"


def test_misplaced_doc_comment_raises():
    """The three ways a doc comment used to vanish or attach to the wrong
    function."""
    from support.apigen.generate import statements
    for body in ("/** orphan */\n",
                 "void X(a)(void);\n/** two */\n/** docs */\nvoid X(b)(void);\n",
                 "void X(a)(void);\n/** dangles at the end */\n"):
        try:
            statements(body)
        except ParseError:
            continue
        raise AssertionError(f"did not raise for {body!r}")


def test_trailing_doc_marker_only_documents_a_member():
    """`/**<` documents the declaration before it. Above a prototype it would
    silently move the text onto the previous function, which no count catches,
    so the only legal use is at the end of a member line."""
    for i, ln in enumerate(open(HEADER).read().split("\n"), 1):
        if "/**<" in ln:
            assert ln.split("/**<")[0].rstrip().endswith(";"), f"{HEADER}:{i}"


def test_unknown_shape_raises():
    """A statement the classifier cannot place must not be dropped silently."""
    src = open(HEADER).read().replace(
        "NFFT_EXTERN void X(trafo)(X(plan) *ths);",
        "NFFT_EXTERN void [[bad]] X(trafo)(X(plan) *ths);")
    try:
        parse_section("NFFT", "NFFT_DEFINE_API", src)
    except ParseError:
        return
    raise AssertionError("a malformed declaration did not raise")


def test_precision_page_matches_nfft3mp():
    """doc/guide/precision.md is hand-written. This is what stops it drifting
    from the header it describes."""
    src = open(os.path.join("include", "nfft3mp.h")).read()
    macros = set(re.findall(r"^#define (\w+)\(name\) NFFT_CONCAT", src, re.M))
    page = open(os.path.join("doc", "guide", "precision.md")).read()
    named = {m for m in macros if f"`{m}(name)`" in page}
    assert named == macros, f"page does not name: {sorted(macros - named)}"
    # And the modules the header deliberately has no macro for.
    for absent in ("NNFFT", "NSFFT", "NFSOFT", "FPT", "MRI"):
        assert f"#define {absent}(name)" not in src, absent
        assert absent in page, absent
    for name in re.findall(r"`(NFFT__\w+__)`", page):
        assert re.search(r"^#\s*define\s+%s\b" % re.escape(name), src, re.M), name


def test_makefile_ships_every_doc_file():
    """Makefile.am lists doc/ file by file, so a new page must be added there or
    it is missing from the release tarball."""
    import subprocess
    tracked = set(subprocess.run(["git", "ls-files", "doc"], check=True,
                                 capture_output=True, text=True).stdout.split())
    src = open("Makefile.am").read()
    listed = set(re.findall(r"^\tdoc/\S+", src, re.M))
    listed = {x.strip() for x in listed}
    assert listed == tracked, (
        f"only in git: {sorted(tracked - listed)}; "
        f"only in Makefile.am: {sorted(listed - tracked)}")


def test_snippet_sources_are_tracked_by_git():
    """A `--8<--` include of an untracked file builds here and fails in CI.
    Four examples/*/simple_test.c are generated by configure and gitignored;
    the docs must include their tracked .c.in templates instead."""
    import subprocess
    tracked = set(subprocess.run(["git", "ls-files"], check=True,
                                 capture_output=True, text=True).stdout.split())
    missing = []
    for page in glob.glob("doc/**/*.md", recursive=True):
        for path in re.findall(r'--8<--\s+"([^":]+)', open(page).read()):
            if path not in tracked:
                missing.append(f"{page} includes untracked {path}")
    assert not missing, missing


def test_render_has_all_three_names():
    page = render_module(BY_KEY["nfft"], PREFIXES)
    for name in ("nfft_trafo", "nfftf_trafo", "nfftl_trafo"):
        assert f"`{name}`" in page, name
    assert "### `trafo`" in page
    assert '=== "long double"' in page
    for leftover in ("\\f$", "\\f[", "\\ref", "@defgroup", "X(plan)"):
        assert leftover not in page, leftover


if __name__ == "__main__":
    tests = [v for k, v in sorted(globals().items()) if k.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} checks passed")
