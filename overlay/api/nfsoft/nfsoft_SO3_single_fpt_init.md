---
symbol: nfsoft_SO3_single_fpt_init
kind: function
source: agent
---
!!! warning "Declared, not defined"

    `nfft/include/nfft3.h:702` declares this function, but the library does
    not define it. A program that calls it does not link. No function in
    `nfft/` has this name or this signature.

The plan builds its FPT sets with the static function `SO3_fpt_init`
(`nfft/kernel/nfsoft/nfsoft.c:168`), which `nfsoft_init_guru_advanced` calls
(`nfsoft.c:119`). It has the parameters `l`, `flags`, `kappa` and a thread
count, but no orders `k` and `m`. It returns one set for each thread, stored
in `internal_fpt_set`. Each set holds one transform for every pair of orders,
$(2L+1)^2$ transforms with $L$ the transform length of `nfsoft_SO3_fpt`
(`nfsoft.c:216`). The precomputation of each transform uses `kappa` as the
FPT threshold (`nfsoft.c:249`).

`l`
:   The bandwidth $B$ in `SO3_fpt_init`.

`flags`
:   The NFSOFT flags in `SO3_fpt_init`. `NFSOFT_USE_DPT` selects
    `FPT_NO_FAST_ALGORITHM`, `NFSOFT_NO_STABILIZATION` selects
    `FPT_NO_STABILIZATION` (`nfsoft.c:195-197`).

`kappa`
:   The FPT threshold in `SO3_fpt_init`. The init functions pass `fpt_kappa`.
