# Validation plan contract

Status: schema version 1, implemented for planning, results, and scaffolding

Date: 2026-10-21

## Evidence boundary

`notebook-classifier create-validation-plan` performs static inspection.  It
does not create environments, execute notebooks, import course dependencies, or
claim that scientific or pedagogical content is correct.

The generated plan is a deterministic handoff to a course-owned runner.  It
contains every resolved manifest entry and every tracked notebook known to the
resolver.  Selection changes an entry's `action`; it never removes the entry.

## Schema versions

- `notebook-validation-plan.schema.json`: version 1;
- `notebook-validation-result.schema.json`: version 1.

Plan and result versions are independent of the classification-manifest schema.
Unknown keys are rejected so that a consumer cannot silently ignore semantics
introduced by a newer producer.

The result schema is an interchange contract implemented by Stage V2. Result
validation never executes the target repository and artifact paths are opened
only after confinement to an explicitly declared root.

## Result evidence semantics

The four result outcomes remain distinct:

| Outcome | Meaning |
| --- | --- |
| `pass` | Every explicit check in that entry passed. At least one check is required. |
| `fail` | A completed check found a defect. |
| `error` | Infrastructure or invalid evidence prevented a reliable conclusion. |
| `not_run` | No attempt occurred; timing, artifacts, and checks must be absent. |

The validator independently checks the plan digest, repository identity,
commit, platform, notebook ID, path, source blob, declared environment, and
observed environment name. A mismatch or invalid pass is represented as an
effective `error` in summaries. Missing selected entries are represented as
`not_run`, never `pass`.

Artifacts use repository-independent relative paths and SHA-256 digests. An
explicit artifact root is mandatory before any referenced file is opened;
missing files, symlink escapes, and digest mismatches invalidate the entry.

Summaries state the evidence boundary: passing the recorded checks, including
notebook execution, does not establish scientific or pedagogical correctness.

## Deterministic serialization and digest

The plan records a separate SHA-256 digest of the complete static inventory
used as input.  The plan digest is SHA-256 over the UTF-8 encoding of the plan
payload with `plan_digest` omitted.  Both payloads are serialized as JSON with:

- object keys sorted lexicographically;
- no insignificant whitespace;
- non-ASCII characters preserved;
- non-finite numeric values rejected.

The human-facing JSON file may be indented or compact.  Its `plan_digest` is
independent of that presentation choice.  Plans contain no generation time,
absolute checkout path, or host name.

## Planned actions

| Action | Meaning |
| --- | --- |
| `candidate` | Static evidence permits a course-owned runner to consider execution. |
| `manual` | The selected manifest tier requires a human procedure. |
| `excluded` | Selection or lifecycle policy deliberately leaves the entry out. |
| `blocked` | An otherwise relevant active entry lacks trustworthy planning evidence. |

These are not test outcomes.  In particular, `candidate` does not mean the
notebook was run or passed.

## Action reason codes

| Code | Meaning |
| --- | --- |
| `selected` | The entry matches selection and has no static blocker. |
| `validation_tier_manual` | The selected tier requires manual validation. |
| `validation_tier_excluded` | The manifest explicitly excludes the entry. |
| `validation_tier_not_selected` | Its tier is outside the requested selection. |
| `delivery_scope_not_selected` | Its delivery scope is outside the requested selection. |
| `notebook_id_not_selected` | Its stable ID is outside an explicitly requested subset. |
| `lifecycle_not_selected` | Its lifecycle is outside the requested selection. |
| `lifecycle_not_executable` | A selected non-active lifecycle is retained for history, not execution. |
| `notebook_not_tracked` | An active manifest entry has no tracked notebook. |
| `notebook_id_missing` | A tracked notebook lacks a stable manifest ID. |
| `notebook_parse_error` | Static notebook parsing failed. |
| `classification_unknown` | At least one required classification remains `unknown`. |
| `environment_missing` | The selected Pixi environment is not declared by the repository. |
| `review_not_current` | Strict review policy requires a current reviewed blob. |
| `constraint_not_allowed` | The plan did not explicitly allow a declared constraint. |

Reason-code order is deterministic.  Entry diagnostics supply human-readable
details, including which fields or constraints caused the reason.

## Selection policy

The default selection is:

- tier `required`;
- all delivery scopes;
- lifecycle `active`;
- review policy `warn`;
- no allowed external constraints;
- platform `linux-64`.

Repeated values within a selection are deduplicated and emitted in vocabulary
order.  Repeated `--include-tier`, `--include-scope`, and
`--include-lifecycle` options are cumulative. Stable IDs supplied with
`--include-id` are deduplicated and sorted. Filters of different kinds are
combined: an entry must match each filter that is present. An ID filter retains
non-selected entries as `excluded`; it never removes them from accounting.

`--review-policy warn` records stale, missing, and unreviewed evidence without
blocking a selected entry.  `--review-policy require-current` blocks it.

Declared constraints are blocked for selected execution candidates unless each
one is named with `--allow-constraint`.  This option records a target-runner
capability; it does not make `notebook-classifier` provide that capability.

## Required target input

A `candidate` still requires the target repository to provide:

- an execution mode;
- a numeric timeout.

A `manual` entry requires a documented manual procedure.  Scientific
assertions, expected artifacts, justified tolerances, and CI policy also remain
target-owned even though they are not mandatory for constructing the static
plan.

## Planning CLI exit status

| Status | Meaning |
| ---: | --- |
| 0 | A plan was written and no entry has action `blocked`. |
| 1 | Manifest validation prevented planning, or a plan was written with at least one blocked entry. |
| 2 | Invocation, Git, filesystem, or inventory/resolution consistency error. |

On status 1, callers must check whether the requested output exists before
reading it: structural manifest errors prevent plan creation, while planning
blockers are represented in a successfully written plan.

## Result and scaffold CLI exit status

| Status | Meaning |
| ---: | --- |
| 0 | Result evidence is structurally and semantically valid, or a scaffold was created/checked without drift or plan blockers. |
| 1 | Result/schema/provenance validation failed, or scaffold drift/plan blockers were found. A requested summary is still written. |
| 2 | Invocation, input I/O, unsafe output location, or overwrite refusal prevented the operation. |

A valid result may contain a genuine `fail`; status 0 from the validator means
the evidence is internally trustworthy, not that every course check passed.
Consumers that gate delivery must inspect effective outcome counts explicitly.

The scaffold command writes only to a non-existing directory outside the
target repository. Its `--check` mode is read-only, may inspect an applied
target layout, and ignores extra target-owned files while reporting missing,
changed, or unsafe generated paths. Default execution is disabled, default CI
is manual-only, and monthly scheduling requires `--schedule monthly`.

## Compatibility

Consumers must reject unsupported major schema versions.  The current version
uses a single integer and rejects unknown keys, so any schema change that adds a
field requires an explicit version and consumer update.  Migrations are deferred
until a second plan schema exists.
