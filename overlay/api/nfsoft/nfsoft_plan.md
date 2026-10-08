---
symbol: nfsoft_plan
kind: struct
source: agent
---
Plan of a transform on the rotation group $\mathrm{SO}(3)$. One of the init
functions fills it, `nfsoft_finalize` frees it. See
[Plan and data layout](../transforms/nfsoft.md#plan-and-data-layout).

### N_total

The bandwidth $B$, not the number of coefficients
(`nfft/kernel/nfsoft/nfsoft.c:89`). `NFSOFT_F_HAT_SIZE(N_total)` gives the
number of coefficients.

### M_total

Number of nodes $M$.

### x

Nodes, $3M$ angles in radians: `x[3*j]` $=\alpha_j$, `x[3*j+1]` $=\beta_j$,
`x[3*j+2]` $=\gamma_j$. With `NFSOFT_MALLOC_X` the init function allocates
the array and `nfsoft_finalize` frees it. `nfsoft_precompute` copies the
nodes into `p_nfft.x` in the order $\gamma,\alpha,\beta$ and divides them by
$2\pi$ (`nfsoft.c:393-401`).

### wig_coeffs

Not used. The init function sets it to `NULL` (`nfsoft.c:110`).

### cheby

Not used. The init function sets it to `NULL` (`nfsoft.c:111`).

### aux

Not used. The init function sets it to `NULL` (`nfsoft.c:112`).

### t

Not used. No function in `nfft/kernel/nfsoft/` sets or reads it.

### flags

The NFSOFT flags given to the init function (`nfsoft.c:91`).

### p_nfft

The internal three-dimensional NFFT plan, of bandwidth $2B+2$ in each
dimension (`nfsoft.c:73-82`). Its flags are the `nfft_flags` of
`nfsoft_init_guru`.

### internal_fpt_set

Array of `nthreads` FPT sets, one for each thread (`nfsoft.c:170`,
`nfsoft.c:216-221`). The sets share the precomputed data of the first set.
`nfsoft_finalize` frees them.

### nthreads

The number of threads at the time of the init call, from
`nfft_get_num_threads` (`nfsoft.c:117`).
