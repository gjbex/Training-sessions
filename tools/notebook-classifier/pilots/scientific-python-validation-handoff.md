# Scientific Python validation handoff pilot

Status: local Stage V4 handoff complete; CI activation and delivery tag pending

Date: 2026-10-21

Target branch: `feature/validation`

Target commit used for the measured runs: `6097ab73fb31dff0ee153957b51036e994ca21c5`

The target checkout was dirty because the Stage V4 implementation was under
review. A separate clean temporary checkout test is therefore part of the
handoff verification; these results must not be represented as evidence for
the pending `20261023` delivery tag.

## Result

The manifest was sufficient to produce deterministic, fully accounted plans.
The runner did not make all required notebooks pass, nor should it have: the
full run found four concrete maintenance defects rather than hiding them with
environment or error-tolerance overrides.

| Measure | Smoke profile | Required profile |
| --- | ---: | ---: |
| Manifest entries accounted for | 47/47 | 47/47 |
| Candidates | 4 | 19 |
| Pass | 4 | 15 |
| Fail | 0 | 0 |
| Error | 0 | 4 |
| Not run | 43 | 28 |
| Sum of notebook durations | 25.364 s | 436.461 s |
| End-to-end elapsed time | 29.135 s | 463.726 s |
| Provisional budget | 720 s | 720 s |

Required-profile environment setup took 0.262 seconds for `default`, 3.651
seconds for `hdf5`, and 2.380 seconds for `xarray` on the pilot host. All three
reported Python 3.12.13 from the repository's existing lockfile. The requested
Python 3.14 applies to the Training-sessions classifier itself; Scientific
Python's lock currently constrains its course environments to Python 3.12.

## Actionable findings

All four required-profile errors named the stable notebook ID, environment,
failing execution check, and underlying exception:

1. `source-code-numpy-fft-experiments` requests the historical kernel
   `conda-env-py35-py`, which is not installed.
2. `source-code-numpy-io-performance` is classified in `default` but imports
   `h5py`; the dependency is available in the repository's `hdf5` environment.
3. `source-code-numpy-numpy-linear-algebra` uses `y.shape[0]` before `y` is
   defined.
4. `source-code-xarray-xarray-intro` uses frequency `6H`; the locked pandas
   rejects uppercase `H` and suggests `6h`.

This gives an actionable-diagnostic ratio of 4/4 for the observed errors. The
classification of the I/O notebook is a data-quality problem, not evidence
that the shared manifest schema needs another field: its existing environment
can be corrected to `hdf5` after maintainer review.

## Target-owned policy and overrides

The target adds one execution registry containing:

- two profiles (`smoke` and `required`);
- a positive timeout for each of the 19 required notebooks;
- two target-specific numerical assertions;
- one generated-PNG declaration and structural validator;
- a Linux-only platform policy and a 720-second required-run budget.

Seventeen of the 19 required candidates need no notebook-specific Python code,
so the generic-execution ratio is 17/19 (89.5%). The two exceptions need
scientific assertion functions; the generated-file rule is declarative and
uses the generic artifact path. Paths and Pixi environment names are not
duplicated in this registry: they come from the generated plan.

The numerical tolerances are target-owned because they depend on the examples'
algorithms and scales. Timeouts, artifacts, and assertion names remain outside
the classification manifest until cross-repository evidence shows stable,
maintainer-friendly shared semantics.

## Robustness exercises

- **Rename:** execution policy refers only to stable IDs. A notebook move
  changes its manifest path and reviewed blob but not profiles, assertions,
  timeouts, the runner, or the workflow. The shared exact-blob rename fixture
  confirms that a move is proposed rather than silently transferring identity.
- **Stale blob:** a target contract test supplies a mismatched planned blob and
  receives an explicit execution error. Shared planner fixtures separately
  exercise advisory and strict stale-review policy.
- **Missing environment:** target and shared tests produce an explicit
  `environment_setup_error`; it cannot be counted as a pass.
- **Interrupted worker:** absence of a worker result becomes a
  `worker_process_error`; shared result tests also reject partial result sets.
- **Deterministic defect:** a temporary notebook with a deliberately excessive
  ODE/quadrature discrepancy is reported as a failed scientific assertion.
- **Source isolation:** every measured entry reported an unchanged worktree.
  Executed notebooks and generated files were stored outside the checkout.

The first smoke attempt also found an infrastructure assumption: copying the
entire working tree tried to copy a live `.codegraph/daemon.sock`. The runner
and shared scaffold template now construct temporary execution trees from
`git ls-files`, excluding sockets, ignored caches, and unrelated untracked
material. The repaired smoke run passed 4/4.

## Shared-tool changes prompted by the pilot

The handoff produced two generic improvements rather than
Scientific-Python-specific branches:

1. A repeatable stable-ID selection filter permits a small smoke profile while
   preserving all non-selected manifest entries as explicit `excluded`
   records. This is preferable to changing their reviewed validation tier.
2. Human summaries now distinguish valid, complete evidence from successful
   checks. A complete result set containing failures is no longer labelled
   merely `complete` in a way that could be mistaken for success.

Plans remain runtime artifacts. A plan embeds the repository commit, so
committing that same plan as evidence for its containing commit would create a
self-reference. The target regenerates plans and records their digest instead.

## Remaining work outside Stage V4

- Decide and review fixes for the four course findings; do not bury them in
  runner exceptions.
- Commit or otherwise discard the two untracked notebooks explicitly excluded
  from the 47-entry manifest (`adsorption.ipynb` and `apartments.ipynb`).
- Commit and release the shared classifier, then pin that release and all
  GitHub Actions to immutable revisions before activating the workflow draft.
- Run at least two maintainer review cycles before claiming that the report is
  operationally useful.
- When tag `20261023` exists, run and archive evidence for that exact tag before
  restructuring begins.
- Apply Stage V5 to differently structured repositories before promoting
  target-owned execution fields into shared catalogue semantics.

Successful execution remains evidence only for the checks recorded here. It
does not establish pedagogical quality, scientific correctness beyond the two
declared invariants, interactive behaviour, or currentness of explanatory
material.
