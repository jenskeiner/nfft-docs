---
symbol: NFFT_SORT_NODES
kind: flag
source: header
---
If this flag is set, the plan sorts the nodes to improve the use of the cache
in the multiplication with the sparse matrix $\mathbf{B}$. The sorted order
is stored in the member `index_x`. The array `x` stays unchanged. The
precomputation routines do the sorting, so call `nfft_precompute_one_psi`
after setting the nodes.

See also: `nfft_precompute_one_psi`, `NFFT_OMP_BLOCKWISE_ADJOINT`.
