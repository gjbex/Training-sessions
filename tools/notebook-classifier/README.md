# Notebook classifier

`notebook-classifier` inventories Jupyter notebooks in a Git repository and
validates the sidecar manifest that records maintainer decisions about notebook
roles, output policies, delivery scope, and validation tiers.

The current implementation covers Stage 0 through Stage 4 of the
[implementation plan](IMPLEMENTATION_PLAN.md): the classification contract,
synthetic fixtures, a read-only scanner, deterministic JSON output, and
manifest validation and resolution.  It also provides comment-preserving TOML
updates, reviewed diffs, conflict-checked atomic writes, blob-based review
staleness, exact-blob rename candidates, resumable drafts, and a local web
review interface.

The completed Scientific Python pilot, including measurements and usability
findings, is documented in
[`pilots/scientific-python.md`](pilots/scientific-python.md).  Its unresolved
validation handoff is
[`pilots/scientific-python-unresolved.md`](pilots/scientific-python-unresolved.md).
The proposed reusable plan generator, result contract, and safe scaffolding are
specified separately in the
[`validation planning implementation plan`](VALIDATION_PLANNING_IMPLEMENTATION_PLAN.md).
Stages V0 through V3 of that plan are implemented.  The versioned semantics, reason
codes, deterministic digest, and exit statuses are documented in the
[`validation plan contract`](VALIDATION_PLAN_CONTRACT.md).

## Trust boundary

The scanner treats repositories and notebook content as untrusted data.  It:

- inspects only an explicitly supplied local Git repository;
- never executes notebook cells or repository commands;
- never imports dependencies named by a notebook;
- invokes Git without a shell;
- writes only the requested JSON inventory output;
- leaves notebook files unchanged.

The manifest validator reads `validation/manifest.toml` by default.  It reports
structural and semantic errors but does not edit the manifest.  The web review
interface writes that manifest only after displaying the exact diff and
rechecking the repository snapshot.

The inventory records Git state, tracked/untracked/ignored notebooks, current
working-tree blob IDs, Pixi environments and task names, other environment
files, `training.toml` material paths, notebook structure, cell tags, stored
outputs and errors, imports, magics, shell escapes, URLs, and conservative risk
signals.  Notebook-format warnings are captured as data rather than leaking as
process warnings.

## Environment

The supported environment is Linux, including Linux under WSL.  Python 3.14 is
the only configured Python version for this tool.

From this directory:

```bash
pixi install --locked
pixi run notebook-classifier --help
```

The tool has its own `pyproject.toml`, Pixi environment, and lockfile.  It does
not use or modify the catalogue website's top-level `requirements.txt`.

## Commands

Launch the local review interface:

```bash
pixi run notebook-classifier review \
    --repository /path/to/course
```

The command chooses an available port, binds only to `127.0.0.1`, prints the
repository revision and a per-process session URL, and opens the browser.  Use
`--no-open` under WSL or when you prefer to open the printed URL yourself.  A
specific loopback port can be selected with `--port`; there is deliberately no
option to bind to another interface.

The application uses only packaged CSS and does not need a network connection.
It provides server-side filters and sorting, safe source previews, transparent
deterministic suggestions, explicit notebook overrides, bulk decisions,
previewed path rules, progress, and the final TOML diff.  Every edit is first
saved as an XDG draft outside the course repository.

Write a deterministic inventory:

```bash
pixi run notebook-classifier scan \
    --repository /path/to/course \
    --output inventory.json
```

Use `--output -` to write JSON to standard output.  A scan still writes its
complete inventory when one or more notebooks cannot be parsed, but exits with
status 1 so automation can detect the finding.

Validate a course manifest:

```bash
pixi run notebook-classifier validate-manifest \
    --repository /path/to/course
```

Use `--json` for machine-readable diagnostics or `--manifest` to choose a
non-default manifest path inside the repository.

Resolve repository defaults, ordered rules, and notebook overrides:

```bash
pixi run notebook-classifier resolve-manifest \
    --repository /path/to/course \
    --output resolution.json
```

The resolution includes every tracked notebook plus historical notebook paths
retained in the manifest.  Each effective property records its provenance as a
vocabulary default, repository default, matching rule, or notebook override.
Review state is reported as `unreviewed`, `current`, `stale`, or `missing` by
comparing the reviewed blob ID with current notebook content.

Create a deterministic validation plan without executing course content:

```bash
pixi run notebook-classifier create-validation-plan \
    --repository /path/to/course \
    --include-tier required \
    --platform linux-64 \
    --output validation-plan.json
```

The plan accounts for every resolved notebook, groups eligible candidates by
environment, and records filtered, manual, excluded, or blocked entries with
machine-readable reasons.  Its default selection is the active `required` tier
on `linux-64`.  Use repeated `--include-tier`, `--include-scope`,
`--include-lifecycle`, and `--allow-constraint` options to state another policy.
Use `--review-policy require-current` when a stale or unreviewed selected
notebook must block planning.

This command does not run a notebook.  Concrete execution, scientific
assertions, timeouts, artifacts, and CI policy remain the responsibility of the
course repository.

Validate course-owned result evidence against its exact plan:

```bash
pixi run notebook-classifier validate-validation-results \
    --plan validation-plan.json \
    --results validation-results.json \
    --artifact-root /tmp/notebook-validation-artifacts
```

The validator checks schemas, plan and repository provenance, notebook IDs,
paths and blobs, declared and observed environments, explicit checks, source
worktree state, and artifact confinement and digests. Missing selected results
are counted as `not_run`; invalid or forged evidence is never counted as a
pass. Use `--json` for the full machine-readable assessment.

Render the same assessment as Markdown or JSON without executing anything:

```bash
pixi run notebook-classifier summarize-validation \
    --plan validation-plan.json \
    --results validation-results.json \
    --artifact-root /tmp/notebook-validation-artifacts \
    --output validation-report.md
```

Generate a target-owned starter into a new review directory outside the course
repository:

```bash
pixi run notebook-classifier scaffold-validation \
    --repository /path/to/course \
    --output-directory /tmp/course-validation-scaffold \
    --ci github-actions
```

Generation refuses existing destinations and direct writes inside the target
repository. The runner is disabled until maintainers configure explicit
timeouts, runs notebooks only in temporary copies, and requires artifacts and
results outside the source checkout. The workflow is a manual-only draft under
`ci/`, not an active `.github/workflows` file. `--schedule monthly` is explicit
opt-in; `--check` reports missing or changed generated files without modifying
them. Local additions are ignored because target repositories are expected to
adapt the scaffold.

## Safe manifest changes and drafts

There is deliberately no unreviewed "write this file" CLI.  The application
loads a `ManifestSnapshot`, edits its comment-preserving
TOML document, and calls `prepare_manifest_change` to validate it and obtain the
exact unified diff.  Only that reviewed `ManifestChange` can be passed to
`write_manifest_atomic`.

The write is refused when any of these changed since the snapshot:

- the repository commit;
- tracked or untracked notebook paths or content;
- the source manifest;
- the candidate content after its diff was prepared.

`DraftStore` atomically persists a candidate outside the course repository.  It
uses `$XDG_STATE_HOME/notebook-classifier` when `XDG_STATE_HOME` is absolute,
and otherwise `~/.local/state/notebook-classifier`.  Drafts are keyed by the
canonical repository path, starting commit, and manifest path; they include the
source and candidate digests needed for an explicit resume or rebase decision.

## Developer checks

```bash
pixi run check
```

This runs Ruff linting, Ruff formatting checks, and the test suite.

## Current limitations

- Evidence extraction is intentionally conservative and heuristic.
- The scanner handles Jupyter notebooks only.
- Suggestions are deterministic heuristics, not content judgements, and must be
  confirmed by a maintainer.
- Markdown raw HTML is escaped and mathematical source is preserved, but the
  MVP does not render mathematics or expose a raw-JSON download.
- Bulk values are validated after submission rather than being presented in a
  property-dependent widget.
- If the repository commit, notebook set/content, or source manifest changes
  during review, writes are blocked; the MVP requires restarting the review
  session rather than rebasing the draft in the UI.
- Rename candidates require identical Git blob content; similarity-based
  candidates are intentionally deferred and identities are never transferred
  automatically.

