---
symbol: nfsoft_posN
kind: function
source: agent
---
!!! warning "Declared, not defined"

    `nfft/include/nfft3.h:712` declares this function, but the library does
    not define it. A program that calls it does not link. Only the static
    function `posN` in `nfft/kernel/nfsoft/nfsoft.c:676` exists.

The static `posN` returns

$$
\mathrm{posN}(n,m,B) = \sum_{n'=-B}^{n-1} \bigl(B+1-\max(|m|,|n'|)\bigr),
$$

the number of coefficients that come before the order $n$ in the block of
the order $m$ of `f_hat`. Here $m$ is the order of the block, the slower
index, and $n$ the order inside the block. For $n=-B$ the value is $0$. The
code computes the sum by recursion in $n$ (`nfsoft.c:676-686`). The
internal macro `NFSOFT_INDEX_TWO` uses it to find the start of a block in
`f_hat` (`nfsoft.c:40`). See
[Layout of `f_hat`](../transforms/nfsoft.md#layout-of-f_hat).

`n`
:   The order inside the block, $-B \le n \le B$.

`m`
:   The order of the block, $-B \le m \le B$.

`B`
:   The bandwidth.
