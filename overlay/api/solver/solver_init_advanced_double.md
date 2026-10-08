---
symbol: solver_init_advanced_double
kind: function
source: header
---
Creates a solver plan for real data and selects the iteration.

The plan allocates the iteration vectors that the chosen method needs. The flags choose the method: LANDWEBER, STEEPEST_DESCENT, CGNR or CGNE. Add PRECOMPUTE_WEIGHT to weight the samples, PRECOMPUTE_DAMP to damp the coefficients, and NORMS_FOR_LANDWEBER to update the norms in the Landweber iteration.

Parameters:

`ths`
:   The solver plan

`mv`
:   The plan of the transform, for example a nfft plan

`flags`
:   The iteration and weight flags
