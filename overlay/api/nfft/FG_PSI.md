---
symbol: FG_PSI
kind: flag
source: header
---
If this flag is set, the convolution step (the multiplication with the
sparse matrix $\mathbf{B}$) uses particular properties of the Gaussian
window function to trade multiplications for direct calls to the exponential
function. The flag has an effect only if the library was built with the
Gaussian window.

See also: `nfft_init`, `nfft_init_guru`.
