# Glossary

This page defines the terms that the guide and the transform pages use. Each
entry gives the symbol, a short definition and a link to the page that
describes the term in depth. The line references point into the `nfft/` source
tree.

Adjoint
:   The transform with the conjugate transposed matrix. It maps the samples
    $f_j$ to the sums $\hat h_{\mathbf k}$ with the sign $+2\pi\mathrm{i}$ in
    the exponent. It is not the inverse. See
    [NFFT](../transforms/nfft.md#definition) and
    [nfft_adjoint](../api/nfft.md#adjoint). For the inverse, see the
    [solver](../transforms/solver.md).

Bandwidth
:   The number $N_t$ of frequencies in dimension $t$. The vector
    $\mathbf N = (N_t)_{t=0,\dots,d-1}$ is the multibandlimit. Each $N_t$ must
    be even. The plan member is `N` (`include/nfft3.h:114`). See
    [What the NFFT computes](index.md#notation).

Cut-off parameter
:   The integer $m$. The window is truncated to $2m+2$ grid points per
    dimension. A larger $m$ gives a smaller error and more work. The plan
    member is `m` (`include/nfft3.h:119`). See [Windows](windows.md#default-cut-off)
    and [Accuracy](accuracy.md).

Direct transform
:   The evaluation of the NDFT sums as written, in
    ${\cal O}(|I_{\mathbf N}|M)$ operations. `nfft_trafo_direct` and
    `nfft_adjoint_direct` do this (`kernel/nfft/nfft.c:177`, `:334`). The tests
    use it as the reference. See
    [nfft_trafo_direct](../api/nfft.md#trafo_direct).

Flag
:   One bit of the plan member `flags`. A flag selects what the plan
    precomputes, allocates and frees (`include/nfft3.h:195-208`). Combine flags
    with the bitwise or operator. The member `fftw_flags` goes to the FFTW
    planner. See [Plans and flags](plans-and-flags.md#flags).

Index set
:   The set $I_{\mathbf N}$ of the frequencies $\mathbf k \in \mathbb Z^d$ with
    $-N_t/2 \le k_t < N_t/2$. It has $N_0 \cdots N_{d-1}$ elements, the plan
    member `N_total`. For $N_t = N$ in all dimensions, the literature also
    writes $I_N^d$. See [NFFT](../transforms/nfft.md#definition).

Node
:   A point $\mathbf x_j \in \mathbb T^d = [-\tfrac12, \tfrac12)^d$,
    $j = 0, \dots, M-1$. $M$ is the number of nodes. The plan member `x` holds
    coordinate $t$ of node $j$ in `x[j*d+t]` (`include/nfft3.h:137`).
    `nfft_check` rejects nodes outside the torus (`kernel/nfft/nfft.c:6190`).
    See [Data layout](plans-and-flags.md#data-layout).

Oversampling factor
:   The ratio $\sigma_t = n_t / N_t$ of the FFT length to the bandwidth
    (`kernel/nfft/nfft.c:5965`). `nfft_init` sets $n_t$ so that
    $2 \le \sigma_t < 4$ (`kernel/nfft/nfft.c:6065`). `nfft_check` requires
    $\sigma_t > 1$ (`kernel/nfft/nfft.c:6196`). A larger $\sigma$ gives a
    smaller error and a longer FFT. See
    [The two parameters](index.md#the-two-parameters).

Plan
:   The structure that holds one transform: the sizes, the nodes, the
    coefficients, the samples, the precomputed data and the FFTW plans
    (`include/nfft3.h:108-161`). An init function creates it, `nfft_finalize`
    frees it. See [Plans and flags](plans-and-flags.md#life-of-a-plan) and
    [nfft_plan](../api/nfft.md#plan).

Precomputation
:   The computation of window values before the transform. `PRE_PHI_HUT`
    stores the values of $\hat\varphi$ for $\mathbf D$. The flags in
    `PRE_ONE_PSI` store the values of $\varphi$ for $\mathbf B$.
    `nfft_precompute_one_psi` fills them after the nodes are set
    (`kernel/nfft/nfft.c:5939`). See
    [Precomputation](plans-and-flags.md#precomputation).

Window function
:   The function $\varphi$ that defines the factors $\mathbf B$ and
    $\mathbf D$ of the fast transform. $\mathbf B$ weights the grid values with
    $\varphi$. $\mathbf D$ divides by its Fourier transform $\hat\varphi$. The
    build selects one window. `nfft_get_window_name` reports it. See
    [Windows](windows.md).

## Terms in other sources

Other libraries and publications use their own terms. Some of them clash with
the terms on this page. Check the formula, not only the name.

The forward NDFT of this site maps the coefficients $\hat f_{\mathbf k}$ on a
regular grid to the samples $f_j$ at the nodes $\mathbf x_j$ (see
[NFFT](../transforms/nfft.md#definition)). Some sources call this transform
NUDFT-II or a type 2 transform. They call the adjoint NDFT, which maps samples
at the nodes to coefficients on the grid, NUDFT-I or a type 1 transform. A
third transform with nonequispaced nodes in both domains has the type number 3
in these sources. The NFFT3 library offers it as the
[NNFFT](../transforms/nnfft.md).

These sources describe the mathematical terms and the names of the transforms:
the Wikipedia page
[Non-uniform discrete Fourier transform](https://en.wikipedia.org/wiki/Non-uniform_discrete_Fourier_transform)
and the
[math section](https://finufft.readthedocs.io/en/latest/math.html#math)
of the FINUFFT documentation.

Sources also differ in these points:

- The sign in the exponent. This site uses $-2\pi\mathrm{i}$ for the forward
  transform and $+2\pi\mathrm{i}$ for the adjoint.
- The scaling. This site uses the angle $2\pi\,\mathbf k\mathbf x_j$ with nodes
  in $[-\tfrac12,\tfrac12)^d$. Other sources use nodes in $[0,2\pi)$ or
  $[-\pi,\pi)$ and the angle $\mathbf k\mathbf x_j$.
- The word "forward". Here it means the transform from coefficients to
  samples. A source with a different sign convention can use it for the
  other direction.
- The word "bandwidth". Here $N_t$ is the number of frequencies in dimension
  $t$. Other sources use it for the largest frequency, which is about $N_t/2$.
