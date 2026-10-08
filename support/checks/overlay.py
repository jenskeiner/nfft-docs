"""Every overlay file must parse and name a symbol in the submodule header.

    python support/checks/overlay.py
"""

import sys

from support.apigen import overlay
from support.apigen.generate import HEADER, mangle_prefixes, parse

try:
    entries = overlay.load()
except overlay.OverlayError as e:
    sys.exit(str(e))
unmatched = overlay.apply(parse(), entries, mangle_prefixes(open(HEADER).read()))
for mod, key in unmatched:
    print(f"overlay/api/{mod}/{key}.md matches no symbol in {HEADER}")
print(f"{len(entries)} overlay files, {len(unmatched)} unmatched")
sys.exit(1 if unmatched else 0)
