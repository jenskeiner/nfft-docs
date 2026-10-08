---
symbol: nfsoft_SO3_fpt_transposed
kind: function
source: agent
---
!!! warning "Declared, not defined"

    `nfft/include/nfft3.h:704` declares this function, but the library does
    not define it. A program that calls it does not link. Only the static
    function `SO3_fpt_transposed` in `nfft/kernel/nfsoft/nfsoft.c:322`
    exists, and only `nfsoft_adjoint` calls it (`nfsoft.c:607`).

The static `SO3_fpt_transposed` is the transposed step of `nfsoft_SO3_fpt`,
used in `nfsoft_adjoint` for one pair of orders $(k,m)$. It turns Chebyshev
coefficients in $\cos\beta$ into coefficients of the degrees
$\max(|k|,|m|),\dots,B$ with the transposed [FPT](fpt.md).

`coeffs`
:   In: the Chebyshev coefficients of the degrees $0$ to `l`. Out: the
    coefficient of the degree $j$ in `coeffs[j]`, for
    $j=\max(|k|,|m|),\dots,$`l`. The entries below $\max(|k|,|m|)$ have no
    defined value (`nfsoft.c:375-378`). `nfsoft_adjoint` reads only the
    defined entries (`nfsoft.c:614`). The array has at least `l`$+1$ entries.

`set`
:   The FPT set, one entry of `internal_fpt_set` of the plan.

`l`
:   The bandwidth $B$.

`k`
:   The first order. It selects the transform in `set` as in
    `nfsoft_SO3_fpt` (`nfsoft.c:348`).

`m`
:   The second order.

`nfsoft_flags`
:   With `NFSOFT_USE_DPT` the function uses `fpt_transposed_direct`,
    otherwise `fpt_transposed` (`nfsoft.c:365-374`).
