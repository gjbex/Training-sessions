# Scientific Python validation-pilot handoff

Status: open items after classifier pilot

Date: 2026-10-21

These are review and validation candidates, not manifest-validation errors.
The classifier has not executed any notebook.

## Repository scope

The following notebooks were untracked and therefore excluded from the
manifest:

- `source-code/adsorption.ipynb`;
- `source-code/apartments.ipynb`.

Before the validation runner treats the manifest as exhaustive, decide whether
these files will be tracked course material or remain outside the repository
contract.

## Manifest provenance cleanup

- `source-code/numpy/game_of_life.ipynb` records reviewer `G`, whereas the other
  46 entries record `Geert Jan Bex`.  Normalize it if reviewer identity is
  intended to be queried rather than treated as free-form display text.

## Optional decisions left at defaults

Runtime remains `unknown` through the vocabulary default for:

- `source-code/lagrange_multipliers.ipynb`;
- `source-code/matplotlib/top500.ipynb`;
- `source-code/vpython/pendulum.ipynb`;
- `source-code/vpython/spring.ipynb`.

`source-code/vpython/pendulum.ipynb` has no rationale.  The two VPython
notebooks above and `source-code/matplotlib/top500.ipynb` inherit the default
active lifecycle.  These omissions are schema-valid and do not make the five
required decisions incomplete, but they should be acknowledged when estimating
validation cost.

## Semantic review candidates

- `source-code/bokeh/bokeh_intro.ipynb` has historical delivery scope and an
  active lifecycle.  Confirm that this means a maintained historical artifact,
  rather than a retired notebook.
- Static inspection detected interactive signals in eight notebooks: the three
  Bokeh notebooks, the three VPython notebooks,
  `source-code/sympy/plotting/plotting_backends.ipynb`, and
  `source-code/sympy/sympy.ipynb`.  None has an explicit constraint.  Determine
  whether validation needs manual interaction, GUI support, or only a suitable
  headless backend.
- Static inspection detected network signals in six notebooks.  These may be
  URLs in explanatory text rather than runtime network dependencies.  Verify
  during validation; do not add a network constraint solely from this signal.

## Validation matrix

| Environment | Required | Extended |
| --- | ---: | ---: |
| default | 17 | 19 |
| hdf5 | 1 | 0 |
| xarray | 1 | 0 |
| bokeh | 0 | 3 |
| image | 0 | 1 |
| performance | 0 | 1 |
| sympy-plotting | 0 | 1 |
| vpython | 0 | 3 |
| **Total** | **19** | **28** |

All 19 required notebooks use `preserve_source`.  Among the extended
notebooks, 14 use `preserve_source` and 14 use `strip`.  Execution validation
must therefore use copies or temporary output paths and must never rewrite the
source notebooks merely to compare results.

## Suggested validation order

1. Run the 17 required notebooks in the default environment.
2. Run the required HDF5 and xarray notebooks in their declared environments.
3. Validate the 19 default-environment extended notebooks.
4. Validate specialized non-interactive environments.
5. Handle Bokeh, plotting, and VPython notebooks with explicit headless or
   manual procedures informed by the interactive-signal review.
6. Report execution failures separately from classification or content-review
   findings.

This order is operational guidance, not evidence that any notebook currently
executes successfully.
