---
symbol: nfsoft_SO3_fpt
kind: function
source: agent
---
!!! warning "Declared, not defined"

    `nfft/include/nfft3.h:703` declares this function, but the library does
    not define it. A program that calls it does not link. Only the static
    function `SO3_fpt` in `nfft/kernel/nfsoft/nfsoft.c:257` exists, and only
    `nfsoft_trafo` calls it (`nfsoft.c:483`).

The static `SO3_fpt` does step 2 of `nfsoft_trafo` for one pair of orders
$(k,m)$. It turns the coefficients of the degrees $l=\max(|k|,|m|),\dots,B$
into Chebyshev coefficients in $\cos\beta$ with the [FPT](fpt.md). See
[How the fast algorithm works](../transforms/nfsoft.md#how-the-fast-algorithm-works).

`coeffs`
:   In: the coefficients of the degrees $\max(|k|,|m|)$ to `l`, from
    `coeffs[0]` on (`nfsoft.c:291-294`). Out: the
    Chebyshev coefficients of the degrees $0$ to `l`. The array has at least
    `l`$+1$ entries.

`set`
:   The FPT set, one entry of `internal_fpt_set` of the plan.

`l`
:   The bandwidth $B$.

`k`
:   The first order. The transform number in `set` is
    $(L+k)(2L+1)+(L+m)$, with $L$ the transform length below
    (`nfsoft.c:282`).

`m`
:   The second order.

`nfsoft_flags`
:   With `NFSOFT_USE_DPT` the function uses `fpt_trafo_direct` and $L=\max(l,2)$.
    Otherwise it uses `fpt_trafo` and $L$ is the next power of two of `l`,
    at least 2 (`nfsoft.c:265-277`, `nfsoft.c:300-310`).
