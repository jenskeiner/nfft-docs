"""Check what `zensical build --strict` does not.

--strict validates in-page Markdown links and anchors only. It does not look at
nav targets, extra_css, extra_javascript or theme features, and it cannot see a
malformed formula, because MathJax runs in the browser. Run from the repo root
after a build. Lives in support/checks/ so the deploy script and CI share it.
"""

import glob
import html
import json
import os
import re
import sys
import tomllib

SITE = "site"
fail = []

cfg = tomllib.load(open("zensical.toml", "rb"))["project"]
fail = []


def walk(item, out):
    if isinstance(item, list):
        for i in item:
            walk(i, out)
    elif isinstance(item, dict):
        for title, v in item.items():
            walk(v, out) if not isinstance(v, str) else out.append((title, v))


pages = []
walk(cfg["nav"], pages)

for title, path in pages:
    built = os.path.join(SITE, path[: -len("index.md")] + "index.html"
                         if path.endswith("index.md")
                         else path[:-3] + "/index.html")
    if not os.path.isfile(built):
        fail.append(f"nav entry {title!r} -> {path}: no {built}")
print(f"nav pages: {len(pages)}")

landing = open(os.path.join(SITE, "index.html")).read()
conf = re.search(r'id="__config"[^>]*>(.*?)</script>', landing, re.S)
if not conf:
    fail.append("no __config block in the landing page")
else:
    data = json.loads(conf.group(1))
    got = set(data["features"])
    want = set(cfg["theme"]["features"])
    if got != want:
        fail.append(f"features mismatch: {want ^ got}")
    print(f"features in __config: {len(got)}")

for asset in ["assets/logo.png", "assets/favicon.png",
              "stylesheets/extra.css", "javascripts/mathjax.js"]:
    if not os.path.isfile(os.path.join(SITE, asset)):
        fail.append(f"asset missing in site/: {asset}")

for needle in ["stylesheets/extra.css",
               "javascripts/mathjax.js",
               "cdn.jsdelivr.net/npm/mathjax@3.2.2",
               'href="' + cfg["repo_url"] + "/" + cfg["edit_uri"]]:
    if needle not in open(os.path.join(SITE, "getting-started/index.html")).read():
        fail.append(f"not referenced from a built page: {needle}")

home = open(os.path.join(SITE, "index.html")).read()
if home.count("arithmatex") < 2:
    fail.append("landing page has fewer than two arithmatex blocks")
if 'class="grid cards"' not in home:
    fail.append("landing page card grid did not render")

stub = open(os.path.join(SITE, "guide/windows/index.html")).read()
if 'class="admonition warning"' not in stub:
    fail.append("stub admonition did not render")



payloads = []
for path in glob.glob(f"{SITE}/**/*.html", recursive=True):
    page = open(path).read()
    for m in re.finditer(r'class="arithmatex">(.*?)</(?:span|div)>', page, re.S):
        payloads.append((path, html.unescape(m.group(1))))

print(f"{len(payloads)} math payloads")
if not payloads:
    fail.append("no math found in the built site")

for path, tex in payloads:
    body = tex.strip()
    if body.startswith("\\[") and body.endswith("\\]"):
        body = body[2:-2]
    elif body.startswith("\\(") and body.endswith("\\)"):
        body = body[2:-2]
    else:
        fail.append(f"{path}: math not wrapped in \\( \\) or \\[ \\]: {body[:60]}")
        continue
    depth = 0
    for i, c in enumerate(body):
        if c == "{" and (i == 0 or body[i - 1] != "\\"):
            depth += 1
        elif c == "}" and (i == 0 or body[i - 1] != "\\"):
            depth -= 1
        if depth < 0:
            break
    if depth != 0:
        fail.append(f"{path}: unbalanced braces in {body[:70]!r}")
    if body.count("\\begin{") != body.count("\\end{"):
        fail.append(f"{path}: unpaired begin/end in {body[:70]!r}")
    if "$" in body:
        fail.append(f"{path}: stray $ inside a math payload: {body[:70]!r}")

# Doxygen markup must not survive into any page.
for path in glob.glob(f"{SITE}/**/*.html", recursive=True):
    page = open(path).read()
    for leftover in (r"\f$", r"\f[", r"\f]", r"\ref ", "@defgroup", "\\anchor",
                     "\\subsection", "\\remark", "\\arg ", "@{"):
        if leftover in html.unescape(page):
            fail.append(f"{path}: Doxygen leftover {leftover!r}")

# Every C identifier a page names must exist in the generated API.
api = " ".join(open(p).read() for p in glob.glob("doc/api/*.md"))
known = set(re.findall(r"[a-z]+_[a-z0-9_]+", api)) | set(
    re.findall(r"`([A-Z][A-Z0-9_]+)`", api))
prefixes = ("nfft_", "nfct_", "nfst_", "nnfft_", "nsfft_", "mri_", "nfsft_",
            "nfsoft_", "fpt_", "solver_")
# Names that share a module prefix but are not API functions.
NOT_API = {"nfft_version_major", "nfft_version_minor", "nfft_version_patch",
           "nfft_version_type",
           # Example programs under examples/ and a MATLAB function, not C API.
           "nfft_benchomp", "nfft_benchomp_createdataset",
           "nfft_benchomp_detail_single", "nfft_benchomp_detail_threads",
           "nfsft_benchomp", "nfsft_benchomp_createdataset",
           "nfsft_benchomp_detail_single", "nfsft_benchomp_detail_threads",
           "nfft_times", "nsfft_test", "nfft_solver"}
checked = 0
for path in glob.glob("doc/**/*.md", recursive=True):
    if path.startswith(os.path.join("doc", "api")):
        continue
    for name in set(re.findall(r"`([a-z]+_[a-z0-9_]+)`", open(path).read())):
        if not name.startswith(prefixes) or name in NOT_API:
            continue
        checked += 1
        if name not in known:
            fail.append(f"{path}: names `{name}`, which is not in the API pages")
print(f"{checked} API identifiers checked against doc/api/")

if 'class="mermaid"' not in open(f"{SITE}/guide/index.html").read():
    fail.append("the guide has no rendered mermaid diagram")

for path in glob.glob(f"{SITE}/transforms/*/index.html"):
    if 'class="arithmatex">\\[' not in open(path).read():
        fail.append(f"{path}: no display formula")
    if "/api/" not in open(path).read():
        fail.append(f"{path}: does not link its API page")

# M1 covers the transform pages, getting started and the guide introduction.
# The rest of the guide is items 3.4 to 3.7, which are not in M1.
M1_PAGES = (glob.glob(f"{SITE}/transforms/**/index.html", recursive=True)
            + glob.glob(f"{SITE}/getting-started/**/index.html", recursive=True)
            + [f"{SITE}/guide/index.html"])
for path in M1_PAGES:
    if "This page is a stub" in open(path).read():
        fail.append(f"{path}: still a stub, but in M1 scope")


for f in fail:
    print("FAIL", f)
print("OK" if not fail else f"{len(fail)} failures")
sys.exit(1 if fail else 0)
