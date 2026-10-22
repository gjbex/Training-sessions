# Validation planning and scaffolding implementation plan

Status: Stages V0–V3 implemented; Stages V4 and V5 pending

Date: 2026-10-21

## Decision summary

`Training-sessions` should provide the reusable machinery that turns a reviewed
notebook manifest into a deterministic validation plan and safe starter
infrastructure.  A course repository should own the concrete runner, scientific
assertions, Pixi tasks, CI workflow, schedules, budgets, and decisions about
which failures block delivery.

This split follows the existing ownership boundary:

- `Training-sessions` owns manifest semantics, plan semantics, interchange
  schemas, generators, and generic consistency checks;
- each course repository owns its facts in the manifest and all executable
  validation policy;
- generated files become ordinary course-repository files after review; they
  are not silently rewritten by `Training-sessions`.

The first consumer is Scientific Python.  The implementation must remain
generic and use synthetic fixtures for its own tests; Scientific Python content
must not be copied into this repository.

## Purpose

Assess and then exploit how much of a notebook validation suite can be derived
from reviewed classification data.  The functionality should answer these
questions reproducibly:

1. Which notebooks are candidates for a requested validation run?
2. Which environment, output policy, and constraints apply to each candidate?
3. Which notebooks require a manual decision or cannot be scheduled safely?
4. What repository-local information is still needed before execution?
5. Can a result be traced to the exact plan, repository revision, and notebook
   blob that produced it?

The implementation is useful only if it reduces duplicated repository-specific
configuration.  A high notebook pass rate is not by itself evidence that the
manifest is useful, and successful execution is not proof of scientific or
pedagogical correctness.

## Scope

### In scope for `Training-sessions`

- a versioned validation-plan schema;
- deterministic plan generation from the existing inventory and resolved
  manifest models;
- complete accounting for current, historical, manual, excluded, and blocked
  notebook entries;
- structured diagnostics for stale reviews, missing environments, unsupported
  constraints, unknown runtimes, and incomplete decisions;
- a versioned result-interchange schema that course-owned runners can emit;
- validation of result provenance against the originating plan;
- human-readable summaries that keep `not_run` distinct from `pass`;
- safe scaffolding for a repository-owned runner, execution-policy file,
  assertion directory, tests, and CI workflow draft;
- comparison and `--check` support for generated scaffolding;
- synthetic unit and integration fixtures;
- documentation for course maintainers.

### Owned by the target course repository

- environment creation and notebook execution;
- notebook-specific timeouts and expected artifacts;
- scientifically meaningful assertions and justified numerical tolerances;
- expected errors, intentionally unexecuted cells, and manual procedures;
- repository-native test commands and Pixi tasks;
- CI provider configuration, triggers, schedules, permissions, budgets, and
  artifact retention;
- whether a finding is advisory or delivery-blocking;
- retention of delivery evidence and baseline reports.

### Non-goals

- Execute notebooks or repository commands from `notebook-classifier`.
- Infer scientific assertions from notebook text.
- Treat kernel exit status as scientific correctness.
- Put arbitrary shell fragments in the classification manifest or plan.
- Generate numerical tolerances without a domain justification.
- Modify `pixi.toml`, workflow files, or course content without a separately
  reviewed course-repository change.
- Enable notebook execution on every pull request by default.
- Claim native Windows or macOS support.  The supported platform is Linux,
  including Linux under WSL.
- Guarantee that a native Linux CI run covers WSL-specific mounted-filesystem
  behaviour.

## Evidence baseline

The Scientific Python pilot supplies a useful initial case:

- 47 tracked and classified notebooks;
- 19 required notebooks and 28 extended notebooks;
- 17 required notebooks in the default environment, one in `hdf5`, and one in
  `xarray`;
- all required notebooks use `preserve_source`;
- eight notebooks have interactive signals but no confirmed constraint;
- four notebooks have an unknown runtime;
- the manifest uses stable IDs, current blob evidence, validation tiers,
  environments, output policies, constraints, and lifecycle states.

These facts are inputs to the pilot, not acceptance assumptions.  The generated
plan must expose unresolved information rather than convert static signals into
confirmed constraints.

## Semantic model

Keep three states separate.

### Classification

A maintainer-owned statement in `validation/manifest.toml`, such as role,
environment, tier, constraint, or output policy.  Classification is not an
execution result.

### Plan

A deterministic projection of a resolved manifest and repository inventory for
a requested selection.  Each entry receives a planned action:

- `candidate`: the entry is eligible for a course-owned runner;
- `manual`: the manifest says human validation is required;
- `excluded`: policy deliberately excludes the entry;
- `blocked`: execution cannot be proposed honestly because required planning
  information is missing or inconsistent.

The plan must not use `pass` or `fail`.  `not_run` is an execution outcome and
is therefore reserved for results.

### Result

A course-owned runner's evidence about attempted execution:

- `pass`: every check declared by that execution contract passed;
- `fail`: an expected check ran and found a defect;
- `error`: infrastructure prevented the check from completing reliably;
- `not_run`: the entry was not attempted, with a required reason code.

Reports must say what each passing check establishes.  They must not turn a
successful notebook execution into a claim that the teaching or science is
correct.

## Proposed workflow

```text
validation/manifest.toml + Git inventory
                |
                v
      resolve existing semantics
                |
                v
    create versioned validation plan
                |
                +--> plan diagnostics and unresolved decisions
                |
                +--> reviewed scaffold in an output directory
                |       |
                |       `--> target-owned runner, policy, tests, CI draft
                |
                v
       target-owned execution
                |
                v
        versioned result document
                |
                v
  provenance check and generic summary
```

Plan creation remains read-only.  Scaffolding writes only to an explicit output
directory and refuses to overwrite files.  Applying or adapting that scaffold
inside a course repository is a separate, reviewable change.

## Validation-plan contract

### Required document metadata

- plan schema version;
- generator name and version;
- repository ID and exact Git commit;
- source manifest path and digest;
- resolved-manifest schema version and digest;
- requested selection policy and supported platform;
- stable digest of the plan content.

Do not include generation timestamps, absolute local paths, host names, or other
volatile values in the deterministic plan payload.  Run timing belongs in the
result document.  Calculate the plan digest over the canonical payload with the
digest field itself omitted.

### Required entry data

- stable notebook ID and repository-relative path;
- current Git blob ID when present and reviewed Git blob ID when recorded;
- review state;
- role, delivery scope, output policy, validation tier, environment, runtime,
  constraints, and lifecycle;
- replacement ID where applicable;
- planned action and one or more machine-readable reason codes;
- provenance for values that affect selection;
- unresolved execution-contract fields required from the target repository.

Every resolved manifest entry and every current tracked notebook must be
accounted for.  A selection filter changes the planned action; it must not make
entries disappear from the plan.

### Selection behaviour

The first implementation should support explicit, composable filters rather
than inventing a universal meaning for `delivery`:

```bash
notebook-classifier create-validation-plan \
    --repository /path/to/course \
    --include-tier required \
    --platform linux-64 \
    --output plan.json
```

Multiple `--include-tier` and `--include-scope` options are cumulative.  Course
repositories define named policies such as `smoke`, `extended`, or `delivery`
in their own execution configuration.  The shared tool may support those names
later only if cross-repository evidence establishes common semantics.

Lifecycle, review state, and constraints affect planned action through explicit
reason codes.  Stale review evidence should normally produce a diagnostic, not
silently remove an otherwise selected notebook.  A strict course workflow may
promote that diagnostic to a blocking condition.

## Result-interchange contract

The result schema is intentionally smaller than a complete test framework.  It
should record:

- result schema version and producing runner version;
- plan digest, repository commit, and platform;
- notebook ID, path, and source blob;
- declared and observed environment identity;
- outcome and reason code;
- start time, duration, and timeout where applicable;
- executed-notebook, log, generated-file, and assertion artifacts by relative
  path and digest;
- individual check names, outcomes, and concise diagnostics;
- whether the worktree remained unchanged.

The generic summarizer must reject or prominently flag results whose plan
digest, commit, ID, path, or source blob does not match.  Result files are
evidence, not trusted instructions; paths must be validated before artifacts
are opened.

## Scaffolding contract

The scaffold generator should produce a review tree, not edit a course
repository in place.  Its initial contents should be:

```text
validation-scaffold/
|-- README.md
|-- execution.toml
|-- run_validation.py
|-- assertions/
|   `-- README.md
|-- tests/
|   `-- test_validation_contract.py
|-- ci/
|   `-- github-actions-notebook-validation.yml
`-- integration-notes.md
```

The scaffold may include generic execution mechanics, but it must leave
scientific assertions and non-obvious tolerances as explicit maintainer tasks.
It should contain no notebook copied from the source repository and no absolute
path.

The CI draft should initially be manual-only, use least-privilege read access,
set concurrency and job timeouts, and call a repository-owned command.  Monthly
or selective triggers are opt-in template choices.  Ordinary pull requests
must not be enabled by default.

`scaffold-validation --check` should compare an existing target layout with the
current template and report drift without modifying it.  Template drift is
advisory: a course repository may intentionally diverge.

## Proposed package changes

```text
tools/notebook-classifier/
|-- VALIDATION_PLANNING_IMPLEMENTATION_PLAN.md
|-- src/notebook_classifier/
|   |-- planning.py
|   |-- results.py
|   |-- scaffolding.py
|   |-- reporting.py
|   |-- schemas/
|   |   |-- notebook-validation-plan.schema.json
|   |   `-- notebook-validation-result.schema.json
|   `-- scaffold/
|       |-- README.md.j2
|       |-- execution.toml.j2
|       |-- run_validation.py.j2
|       |-- test_validation_contract.py.j2
|       `-- github-actions-notebook-validation.yml.j2
`-- tests/
    |-- test_planning.py
    |-- test_results.py
    |-- test_scaffolding.py
    `-- fixtures/
        `-- validation_planning/
```

`planning` must consume the existing `RepositoryInventory` and
`ManifestResolution` models.  It must not reimplement TOML parsing, precedence,
or Git discovery.  `reporting` should consume only validated plan and result
models so it can be tested without a course checkout.

Use templates only for files that course repositories are expected to own.
Plan and result JSON must be produced from typed models and schemas, not text
templates.

## Command-line interface

Add these commands incrementally:

```bash
# Read-only: emit the complete deterministic plan.
notebook-classifier create-validation-plan \
    --repository /path/to/course \
    --include-tier required \
    --output plan.json

# Validate independently produced course-runner results.
notebook-classifier validate-validation-results \
    --plan plan.json \
    --results results.json

# Produce a generic evidence summary; never execute a course command.
notebook-classifier summarize-validation \
    --plan plan.json \
    --results results.json \
    --output report.md

# Write new files only into an explicit empty output directory.
notebook-classifier scaffold-validation \
    --repository /path/to/course \
    --output-directory /tmp/course-validation-scaffold \
    --ci github-actions
```

Machine-readable data goes to the requested file or standard output; human
diagnostics go to standard error.  Invalid input, incomplete planning under a
strict policy, schema mismatch, and internal failure need distinct documented
exit codes.

## Implementation stages

### Stage V0: contracts and falsifiable fixtures

Status: implemented.  The versioned schemas, deterministic digest, reason
codes, exit statuses, and synthetic planning cases are covered by the package
and its tests.

Deliver:

- plan and result semantic definitions;
- JSON Schemas with explicit versions and unknown-key rejection;
- small synthetic repositories covering required, extended, manual, excluded,
  stale, replaced, missing-environment, and constrained notebooks;
- reason-code vocabulary and exit-code table;
- deterministic canonicalization and digest rules.

Exit criteria:

- the 47-entry Scientific Python resolution can be represented without a
  Scientific-Python-specific schema field;
- every fixture entry appears exactly once in a plan;
- plan generation has no execution or network side effects;
- plan output is byte-for-byte stable for identical inputs.

### Stage V1: read-only plan generator

Status: implemented.  `create-validation-plan` consumes the existing inventory
and resolved manifest models and never executes course content.

Deliver:

- `planning.py` consuming existing inventory and manifest resolution;
- `create-validation-plan` with explicit tier, scope, lifecycle, review-state,
  constraint, and platform policies;
- complete-entry accounting and structured diagnostics;
- grouping metadata for environments without embedding environment commands;
- unit and CLI integration tests.

Exit criteria:

- repeated runs at one commit produce the same plan and digest;
- current, historical, filtered, manual, excluded, and blocked entries remain
  visible with reasons;
- untracked notebooks and stale reviews are reported explicitly;
- unknown runtime does not become an invented numeric timeout;
- no absolute checkout path appears in the plan.

### Stage V2: result validation and reporting

Status: implemented. Result documents are schema-checked and matched to their
plan, repository, notebook blobs, environments, checks, and confined artifacts.
JSON and Markdown summaries preserve missing results as `not_run` and downgrade
invalid evidence rather than counting it as a pass.

Deliver:

- result loader and schema validator;
- plan/result provenance matching;
- Markdown and JSON summary outputs;
- clear separation of `fail`, `error`, and `not_run`;
- duration, environment, and exception-count metrics;
- tests for partial, interrupted, duplicated, forged, and mismatched results.

Exit criteria:

- a missing result cannot be mistaken for a pass;
- mismatched commits, blobs, IDs, or plan digests are prominent failures;
- summaries state that execution evidence does not establish scientific or
  pedagogical correctness;
- artifacts outside the declared result root are rejected.

### Stage V3: safe scaffold generator

Status: implemented. The generator writes only to a new review directory
outside the target repository. Execution is disabled by default; the generated
runner isolates configured execution in temporary repository copies and the CI
draft remains outside `.github/workflows` until separately reviewed.

Deliver:

- reviewed templates for the target-owned execution registry, runner, contract
  tests, assertion layout, and GitHub Actions draft;
- `scaffold-validation` writing only to a new explicit output directory;
- `--check` comparison without modification;
- template metadata recording generator and template versions;
- documentation for adapting rather than blindly accepting the scaffold.

Exit criteria:

- existing files are never overwritten;
- the generated runner operates on a temporary copy and writes executed
  notebooks and generated artifacts outside source paths;
- the draft workflow is manual-only unless scheduling is explicitly requested;
- workflow permissions are read-only and commands remain repository-owned;
- assertion placeholders cannot produce a false pass.

### Stage V4: Scientific Python handoff pilot

Status: implemented locally on 2026-10-22. All 47 entries were accounted for,
all 19 required notebooks received explicit results, the smoke profile passed,
and the required profile exposed five actionable course-maintenance errors.
Measurements and handoff findings are recorded in
`pilots/scientific-python-validation-handoff.md`. Hosted CI activation and the
`20261023` delivery baseline remain intentionally pending.

This stage creates changes in Scientific Python only under a separate explicit
task.  `Training-sessions` supplies the generator and records measurements.

Pilot sequence:

1. Generate a plan for the four existing smoke candidates.
2. Review and adapt the scaffold in Scientific Python.
3. Execute the four candidates locally on Linux in their locked environments.
4. Add one justified numerical invariant and one generated-artifact check.
5. Introduce a temporary deterministic defect and verify it is caught.
6. Expand to all 19 required notebooks, grouped by environment.
7. Record every repository-specific override and missing manifest concept.
8. Exercise a rename, stale blob, missing environment, and interrupted run.
9. Run the accepted repository-owned command from a clean checkout.

Do not commit an intentionally defective notebook.  The defect test should use
a temporary fixture or reversible mutation in an isolated copy.

Exit criteria:

- all 47 manifest entries are accounted for in the plan;
- all 19 required entries receive an honest planned action and, if attempted,
  an explicit result state;
- validation never modifies tracked instructional material;
- one command reproduces the accepted required checks;
- failures identify notebook ID, environment, check, and useful evidence;
- `not_run` is visible and cannot be counted as a pass;
- total runtime and environment setup cost are measured;
- the number and nature of target-specific overrides are recorded.

### Stage V5: cross-repository assessment

Use the planner and scaffold with:

- one differently structured notebook-heavy repository;
- one repository where notebooks are secondary to scripts, slides, or compiled
  examples.

Compare:

- percentage of execution candidates handled by the generic scaffold;
- number of per-notebook and per-repository overrides;
- repeated missing concepts and reason codes;
- plan stability when paths and repository structure change;
- runtime and maintenance cost;
- template divergence and false assumptions about environment tooling.

Promote execution fields into shared manifest semantics only when they recur
across repositories and remain understandable to maintainers.  Validate any
schema change against the whole available metadata corpus.

## Testing strategy

### Unit tests

- every manifest entry is represented exactly once;
- deterministic ordering and plan digest;
- filter composition and reason precedence;
- active, replaced, retired, and suspended lifecycle behaviour;
- stale, missing, and current review states;
- unknown runtime and unsupported constraint handling;
- duplicate IDs, missing paths, and missing environments;
- schema forward-compatibility rejection;
- result outcome and reason-code validation;
- plan/result provenance mismatch;
- scaffold escaping and path traversal attempts.

### Integration tests

- create a plan from a temporary Git repository;
- rename a notebook while retaining its stable ID;
- add an untracked notebook and confirm it is reported but not silently added;
- alter a reviewed notebook blob and confirm the stale diagnostic;
- validate complete, partial, interrupted, and duplicated result sets;
- generate a scaffold into an empty directory and refuse a second write;
- confirm plan generation and result summarization do not modify the source
  repository;
- verify operation without network access.

### Scientific correctness boundary

Generic tests can establish execution, provenance, output location, and result
accounting.  Course-owned tests must establish numerical properties such as a
bounded residual, conservation law, monotonicity, symmetry, or comparison with
an analytical solution.  Exact floating-point equality and large golden
notebook outputs should not be generated as defaults.

Every non-obvious tolerance must be justified by the algorithm, scale,
conditioning, and supported platform.  A passing generated-file existence test
alone is weak; validate content, dimensions, checksum, or another stable
property when that artifact matters.

## Safety and CI policy

- Treat manifests, notebooks, plans, results, and artifact paths as untrusted
  data.
- Never evaluate manifest values as Python or shell code.
- Resolve all repository and artifact paths against explicit roots.
- Use argument arrays and `shell=False` in generated Python runners.
- Execute notebooks only in the target-owned runner and a temporary work area.
- Default plotting to a non-interactive backend when the target contract allows
  it; do not pretend this validates interactive behaviour.
- Do not enable network access, secrets, write tokens, or pull-request execution
  in the generic workflow draft.
- Pin the generator and action dependencies used by an accepted target
  workflow; record those versions in results.
- Distinguish native Linux CI evidence from optional WSL-specific local checks.

## Measures of usefulness

The Scientific Python pilot should record:

- plan coverage: accounted entries divided by resolved entries;
- generic execution ratio: candidates needing no notebook-specific runner code;
- override count and categories;
- actionable-diagnostic ratio;
- total runtime, environment setup time, and per-notebook durations;
- manual, blocked, error, failure, pass, and `not_run` counts;
- number of manifest concepts that proved ambiguous or insufficient;
- number of files changed when a notebook moves or its tier changes;
- scaffold lines retained, adapted, and replaced by the target repository.

Do not set a success threshold for the generic execution ratio before the first
run.  The falsification criterion is clearer: if most notebooks need unrelated
one-off logic, the manifest is not yet a sufficient basis for reusable test
generation.

The existing Scientific Python design proposes an approximately 12-minute
required-run budget.  Treat that as a hypothesis to measure, not a constraint
to meet by silently dropping checks.

## Compatibility and release policy

- Version plan and result schemas independently from the classification
  manifest schema.
- Include the producing tool version in every plan and result.
- Reject unsupported major schema versions; allow compatible minor additions
  only if unknown fields cannot alter semantics.
- Keep migrations explicit and test them with frozen fixtures.
- During the pilot, Scientific Python may pin a Training-sessions commit.  A
  reusable workflow should eventually depend on a tagged package release, not a
  moving branch.
- A committed plan may document a delivery baseline, but routine validation
  should regenerate it and compare its digest so stale plans cannot pass
  unnoticed.

## Main risks and trade-offs

### Shared planner versus target independence

A shared planner prevents divergent interpretations of manifest semantics, but
it creates a version dependency.  Explicit schema versions and a pinned tool
release are preferable to copying resolution logic into every course.

### Generated runner versus shared runtime

A generated runner leaves a course independently maintainable but can drift
from later template improvements.  A shared runtime reduces duplication but
makes validation depend on installing `Training-sessions` tooling.  Start with
a small generated, target-owned adapter and measure divergence before deciding
whether an execution runtime should become a separately released package.

### CI generation versus security and cost

Generating workflow YAML is convenient but can introduce executable changes
and recurring cost.  Generate a review draft with manual execution and minimal
permissions; make schedules and selective triggers explicit target decisions.

### More manifest fields versus comprehensibility

Adding timeouts, artifacts, and assertions to the classification manifest can
reduce duplication, but it can also turn the manifest into a build language.
Keep repository-specific execution details in `execution.toml` until repeated
cross-repository evidence justifies a shared field.

## Definition of done for the Training-sessions functionality

- A documented command generates a deterministic, versioned plan from a clean
  course checkout without executing course code.
- Every current and retained historical manifest entry is accounted for.
- Plans contain no arbitrary commands or host-specific paths.
- A result schema and validator prevent missing or mismatched evidence from
  being reported as passing.
- A scaffold can be generated into an empty directory without modifying the
  target repository.
- The scaffold defaults to safe Linux-only, manual CI and requires explicit
  target-owned assertions.
- Synthetic tests cover hostile paths, incomplete manifests, stale evidence,
  partial runs, and scaffold conflicts.
- The Scientific Python pilot measures runtime, overrides, schema gaps, and
  maintenance operations rather than merely reporting a pass percentage.
- Documentation states clearly what execution evidence proves and what remains
  manual, scientific, pedagogical, interactive, or too costly to validate.

## Decisions and remaining question

Stages V0–V3 use the documented project-specific canonical JSON serializer,
warn about stale review evidence by default, block unapproved constraints, use
`nbclient` directly in the generated target-owned runner, and identify retained
artifacts by confined relative path and SHA-256 digest. Concise check messages
remain embedded in result documents.

The remaining packaging question is when the classifier and validation planner
should become separately versioned packages. Resolve that from the Scientific
Python handoff and cross-repository evidence; do not add
Scientific-Python-specific branches to shared code.
