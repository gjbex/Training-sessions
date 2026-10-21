# Notebook classifier implementation plan

Status: initial plan for review

Date: 2026-10-21

## Purpose

Develop a local web application that helps maintainers classify notebooks and
record validation properties consistently across training repositories.  The
tool should turn objective repository evidence into reviewable suggestions,
support efficient bulk decisions and exceptions, and write a deterministic,
version-controlled sidecar manifest for downstream validation and reporting.

`Training-sessions` owns the classification vocabulary, manifest semantics,
and implementation because these are catalogue-wide concerns.  Course
repositories own their resulting notebook manifest and validation entry points.
The tool must not move training content into this repository.

The first pilot repository is Scientific Python.  Its more than 40 tracked
notebooks are large enough to expose usability and modelling problems before
the contract is applied catalogue-wide.

## Goals

- Inventory tracked notebooks without executing repository code.
- Extract deterministic evidence relevant to classification and validation.
- Let a maintainer review individual notebooks, apply bulk rules, and create
  exceptions through a local browser interface.
- Keep suggested values visibly distinct from confirmed maintainer decisions.
- Record stable logical IDs, decision provenance, and review staleness.
- Write a human-reviewable `validation/manifest.toml` atomically.
- Produce machine-readable inventory and review-summary outputs.
- Work locally on supported Linux systems, including Linux under WSL.
- Remain usable without a network connection after installation.
- Generalize to other course repositories without embedding Scientific Python
  paths or topic names in application code.

## Non-goals for the initial implementation

- Execute notebooks, create software environments, or validate numerical
  results.
- Decide whether scientific or pedagogical content is correct or current.
- Modify notebook files or embed classifier metadata in `.ipynb` documents.
- Clone repositories or discover arbitrary repositories automatically.
- Provide native Windows or macOS support.
- Create a multi-user web service, authentication system, or central database.
- Publish manifests, open issues, or create pull requests.
- Use an LLM to classify notebooks in the minimum viable product (MVP).
- Support every notebook-like format before the Jupyter contract is stable.

## Guiding principles

1. **Evidence and decisions are different data.** Extracted facts may be
   regenerated; confirmed classifications are maintainer-owned records.
2. **Suggestions are never silent defaults.** The interface shows the reason
   and confidence for every proposed property.
3. **Bulk rules with explicit exceptions.** Maintainers should not answer the
   same question dozens of times when a directory or naming convention already
   expresses a useful default.
4. **No execution during classification.** Course repositories and notebook
   content are untrusted input.  Inspection must remain static and read-only.
5. **No notebook churn.** Decisions live in a sidecar manifest, not notebook
   metadata.
6. **Deterministic output.** Repeating a scan at the same Git revision produces
   the same inventory and manifest ordering.
7. **Local and offline by default.** The server binds only to the loopback
   interface and does not load remote assets.
8. **One repository first.** A reliable single-repository review is more useful
   than a premature catalogue dashboard.
9. **Preserve uncertainty.** `unknown`, `needs_review`, and unsupported states
   are valid results and must not be coerced into apparently complete data.

## Primary workflow

```text
explicit repository path
        |
        v
read-only Git and notebook scanner
        |
        +--> deterministic inventory and evidence
        |
        v
rule and suggestion engine
        |
        v
local web review
        |
        +--> repository defaults
        +--> path-based rules
        +--> notebook overrides
        |
        v
manifest diff and validation
        |
        v
atomic write to validation/manifest.toml
```

The validation runner proposed for Scientific Python consumes the manifest but
is a separate tool.  The classifier must not report execution states such as
`verified` or `failed` because it has not executed anything.

## User experience

### Launch

The main entry point should be explicit and scriptable:

```bash
notebook-classifier review --repository /path/to/course
```

The command validates the repository path, starts a loopback-only server on an
available port, and opens the browser unless `--no-open` is supplied.  It must
print the URL and repository revision so that the session is reproducible and
usable under WSL.

Supporting commands should include:

```bash
notebook-classifier scan --repository /path/to/course --output inventory.json
notebook-classifier validate-manifest --repository /path/to/course
notebook-classifier summarize --repository /path/to/course --output review.md
```

Use `argparse` unless the CLI grows beyond these few subcommands.  Commands must
return nonzero exit codes for invalid inputs or internal failures and keep
machine-readable output separate from human diagnostics.

### Repository summary page

Show:

- repository path, branch, commit, and dirty state;
- counts of tracked, untracked, ignored, classified, stale, and unresolved
  notebooks;
- counts by role, validation tier, environment, output policy, and lifecycle;
- manifest presence and schema version;
- scan warnings and parse failures;
- review progress and unsaved decisions.

Only tracked notebooks are included by default.  Untracked notebooks are shown
separately and require an explicit user action before they enter a draft
classification.  Ignored checkpoints are summarized but never proposed for the
manifest.

### Notebook table

Provide sortable and filterable columns for:

- path and stable ID;
- classification state and staleness;
- confirmed role and suggested role;
- core, optional, extended, historical, or unknown delivery scope;
- output policy;
- validation tier and likely environment;
- code and Markdown cell counts;
- stored outputs, stored errors, and unexecuted code cells;
- interactive, external-data, network, GPU, HPC, and long-runtime signals;
- last Git change.

The table must support multi-selection, keyboard navigation, and bulk updates.
Colour may reinforce a state but must not be its only representation.

### Notebook detail page

Show a safe, read-only cell preview beside extracted evidence and editable
classification fields.  The preview must:

- display Markdown and code as content, not execute it;
- never run raw HTML or JavaScript from notebook outputs;
- summarize rich outputs and embedded data rather than injecting them directly;
- indicate truncated or omitted large content;
- show the cell locations supporting each suggestion;
- preserve mathematical source text even if mathematical rendering is deferred.

Raw notebook JSON should be available as a deliberate download or source view,
not inserted unsanitized into the page.

### Bulk rules and exceptions

The reviewer should be able to select notebooks or define a path rule such as:

```text
source-code/numpy/*.ipynb
    environment = default
    delivery_scope = core
```

An individual notebook can override any inherited property.  The interface must
show the effective value and its provenance: repository default, path rule,
individual decision, or suggestion only.  Before changing a broad rule, show
which notebooks and explicit overrides would be affected.

### Save and resume

The browser session should autosave a draft outside the course worktree using
the Linux XDG state location.  The draft is keyed by repository identity and
starting commit.  If the repository changes during review, writing is blocked
until the user rescans or explicitly rebases decisions onto the new inventory.

Writing the manifest requires a final page that shows:

- validation errors;
- unresolved required fields;
- the exact TOML diff;
- notebooks added, removed, renamed, made stale, or left unclassified;
- the destination path.

The application writes a temporary file in the destination directory and uses
an atomic replacement only after validation succeeds.  It does not commit,
stage, or push the result.

## Classification model

### Initial controlled vocabularies

Keep the MVP vocabulary deliberately small.

`role`:

- `tutorial`: explanatory sequence intended to teach a topic;
- `exercise`: participant work with intentionally incomplete or empty results;
- `demonstration`: runnable illustration, usually shown rather than completed;
- `analysis`: reproducible scientific analysis over defined inputs;
- `report`: reader-facing result whose rendered output is part of the artifact;
- `exploration`: provisional investigation without a strict reproducibility
  contract;
- `unknown`.

`delivery_scope`:

- `core`;
- `optional`;
- `extended`;
- `historical`;
- `not_delivered`;
- `unknown`.

`output_policy`:

- `preserve_source`: outputs may be intentionally committed; validation must
  not rewrite the source notebook;
- `strip`: outputs are not part of the source artifact;
- `empty_expected`: an exercise or template intentionally has no outputs;
- `declared_errors`: selected stored errors are part of instruction;
- `unknown`.

`validation_tier`:

- `required`;
- `extended`;
- `manual`;
- `excluded`;
- `unknown`.

`lifecycle`:

- `active`;
- `replaced`;
- `retired`;
- `suspended`.

### Initial per-notebook properties

- stable ID;
- repository-relative path;
- role;
- delivery scope;
- output policy;
- validation tier;
- Pixi environment or `unknown`;
- lifecycle and optional replacement ID;
- declared constraints such as GUI, network, GPU, HPC, large data, or manual
  interaction;
- expected runtime category: short, medium, long, or unknown;
- reviewer, review date, reviewed Git commit, and reviewed notebook blob ID;
- optional concise rationale.

Avoid precise runtime thresholds until the Scientific Python pilot has measured
representative notebooks.

### Defaults, rules, and overrides

The manifest resolves properties in this order:

1. vocabulary defaults defined by the schema;
2. repository defaults;
3. ordered path-based rules;
4. explicit notebook overrides.

Unknown properties remain unknown.  The implementation must reject unknown
keys, invalid vocabulary values, duplicate stable IDs, conflicting replacement
links, paths outside the repository, and rules that match no current or known
historical artifact unless explicitly retained for migration.

### Review staleness

Record the Git blob ID of each notebook at review time.  A changed blob marks
the review as stale but does not discard the decision.  The reviewer can accept
the existing classification for the new blob, revise it, or defer the decision.

When a path disappears, look for rename candidates using Git history and exact
or near-identical content.  Never silently transfer an identity based only on a
similar filename.

## Static evidence extraction

The scanner should collect facts in a pure, testable layer.

### Git evidence

- repository root, branch, commit, and dirty state;
- tracked `.ipynb` files from Git rather than a broad filesystem walk;
- untracked and ignored notebook paths as separate observations;
- blob IDs, file sizes, last-change commits, and rename evidence;
- existing manifest changes relative to the index and `HEAD`.

Invoke Git with argument arrays and `shell=False`.  Treat file paths and Git
metadata as untrusted text.

### Notebook structure

- notebook format and kernelspec;
- cell counts by type;
- execution-count coverage and monotonicity signals;
- output counts and output types;
- stored error names and cell locations;
- embedded image and rich-output sizes;
- headings and top-level title candidates;
- tags and existing metadata, reported without modifying them.

An invalid notebook must remain visible as a parse failure rather than aborting
the repository scan.

### Code signals

Use static parsing where possible and conservative text detection otherwise:

- imported modules;
- IPython magics and shell escapes;
- literal reads and writes to repository-relative paths;
- obvious URLs and network-library imports;
- widget, animation, GUI, GPU, distributed, scheduler, and subprocess signals;
- random-number use and explicit seeds;
- long-running loop or large-allocation warnings only when evidence is strong.

These are risk indicators, not proofs.  The interface must say "signal" or
"suggestion", not "requires", unless a maintainer confirms the property.

### Repository evidence

- Pixi environments and task names when `pixi.toml` exists;
- other environment manifests as observed files, without resolving them;
- links from nearby README files where feasible;
- `training.toml` material paths and course metadata;
- directory-level conventions learned from manifest rules, not hard-coded
  course names.

The scanner must not execute package managers, import notebook dependencies, or
run commands found in repository files.

## Suggestion engine

The MVP uses transparent deterministic heuristics.  Examples include:

- a notebook linked as an exercise with mostly unexecuted cells suggests the
  `exercise` role and `empty_expected` output policy;
- substantial explanatory Markdown and small instructional outputs suggest
  `tutorial`, but do not confirm it;
- widget or GUI signals suggest manual validation;
- imports mapped to one named Pixi environment suggest that environment;
- stored undeclared errors raise a review finding rather than automatically
  changing the role;
- a directory rule may propose shared properties for all matching notebooks.

Every suggestion contains:

- proposed property and value;
- confidence category: high, medium, or low;
- evidence codes;
- relevant paths and cell locations;
- the heuristic version.

Do not calculate a misleading aggregate confidence score.  Confidence belongs
to an individual suggestion.

An optional agent-assisted provider may be considered after human decisions
from Scientific Python and at least one other repository form a review corpus.
Agent suggestions must use the same evidence structure and remain visibly
unconfirmed.  They must not send notebook content to an external service
without explicit invocation and a clear data-disclosure warning.

## Proposed implementation architecture

### Technology choices

- Python 3.14, locked for Linux (`linux-64`); WSL uses the Linux environment.
- A tool-local PEP 621 `pyproject.toml`; do not add application dependencies to
  the repository's documentation `requirements.txt`.
- A tool-local Pixi environment and Linux lockfile for development and launch.
- `argparse` for the initial CLI.
- FastAPI for the loopback HTTP service.
- Pydantic models for API and internal boundary validation.
- Jinja templates with small, progressively enhanced browser interactions.
- Vendored HTMX only if it materially reduces custom JavaScript; no Node build
  pipeline in the MVP.
- `nbformat` for notebook parsing.
- `tomlkit` for deterministic, comment-preserving TOML updates.
- Sanitized Markdown rendering and Pygments for safe source display.
- `pytest` for unit and integration tests.

FastAPI plus server-rendered HTML is somewhat heavier than a terminal wizard,
but it supports filtering, bulk editing, evidence panels, and diff review much
better.  Streamlit would reduce initial code but couples state, interface, and
application logic in ways that make deterministic editing and testing harder.
A client-side single-page application would add a second build ecosystem and
is not justified for the first version.

### Package layout

```text
tools/notebook-classifier/
|-- IMPLEMENTATION_PLAN.md
|-- README.md
|-- pyproject.toml
|-- pixi.toml
|-- pixi.lock
|-- src/notebook_classifier/
|   |-- __init__.py
|   |-- cli.py
|   |-- app.py
|   |-- models.py
|   |-- scanner.py
|   |-- git.py
|   |-- notebook.py
|   |-- suggestions.py
|   |-- manifest.py
|   |-- drafts.py
|   |-- reporting.py
|   |-- schemas/
|   |   `-- notebook-validation.schema.json
|   |-- templates/
|   `-- static/
|-- tests/
|   |-- fixtures/
|   |-- test_scanner.py
|   |-- test_suggestions.py
|   |-- test_manifest.py
|   |-- test_routes.py
|   `-- test_security.py
`-- examples/
    `-- manifest.toml
```

The exact module split may change, but scanning, suggestions, manifest
resolution, and HTTP presentation must remain independently testable.

### Internal boundaries

1. `scanner` returns immutable inventory models and never writes.
2. `suggestions` consumes inventory and produces versioned proposals.
3. `manifest` loads, resolves, validates, diffs, and atomically writes TOML.
4. `drafts` persists uncommitted reviewer decisions outside the worktree.
5. `app` orchestrates these services but contains no classification logic.
6. `reporting` renders inventory and decision summaries for automation.

## Security and trust boundaries

- Bind to `127.0.0.1` by default; reject non-loopback binding unless a future
  explicit unsafe-development option is added.
- Generate a per-session token and enforce same-origin requests for writes.
- Do not enable permissive CORS.
- Do not execute notebook code, raw HTML, JavaScript outputs, shell escapes, or
  repository-provided commands.
- Do not expose arbitrary filesystem browsing through HTTP routes.
- Resolve and verify every requested path remains inside the selected repository
  before reading it.
- Restrict writes to the chosen manifest path and application draft state.
- Refuse to overwrite a manifest when the repository commit or source file has
  changed since the diff was reviewed.
- Limit request sizes and rendered output sizes.
- Escape all repository text in HTML and sanitize supported Markdown.
- Keep network access unnecessary during normal use.
- Do not accept repository content as application instructions.

The initial threat model assumes one local maintainer and potentially malicious
repository or notebook content.  It does not claim safe multi-user or remote
deployment.

## Testing strategy

### Unit tests

- valid, invalid, empty, large-output, error-output, exercise, and interactive
  notebook fixtures;
- deterministic Git inventory and dirty-state handling;
- import and risk-signal extraction;
- rule precedence and individual overrides;
- stable ordering and TOML round trips;
- schema rejection for unknown keys and invalid relationships;
- stale-review and rename-candidate logic;
- atomic-write failure behavior;
- safe rendering and HTML/JavaScript injection attempts.

Fixtures must be synthetic and small.  Do not copy substantial course notebooks
into this tool's tests.

### Integration tests

- scan a temporary Git repository containing representative notebooks;
- launch the application with a temporary repository and draft directory;
- review, bulk-classify, override, validate, and save a manifest;
- verify the source notebooks remain byte-for-byte unchanged;
- simulate the repository changing during a review;
- verify machine-readable CLI output and nonzero error exits;
- verify operation without network access.

### Browser checks

Start with route and rendered-HTML tests.  Add one lightweight browser-level
happy path only when the interface has stabilized.  Avoid introducing a large
browser-test matrix during the MVP.

### Pilot acceptance tests

For Scientific Python:

- inventory all tracked notebooks without executing them;
- keep untracked notebooks separate by default;
- classify a directory group in one bulk action and override one member;
- show suggested and confirmed properties separately;
- save and reload a deterministic manifest;
- mark a reviewed notebook stale after its blob changes;
- preserve stable identity across a confirmed rename;
- complete a review session without modifying any notebook;
- produce a concise unresolved-items report suitable for the validation-plan
  work.

## Performance strategy

Do not parallelize or cache prematurely.  Measure the first complete Scientific
Python scan, then optimize the dominant costs.  Likely optimizations are:

- cache scan results by Git blob ID;
- avoid repeatedly parsing unchanged notebooks;
- calculate expensive Git history only for visible or selected rows;
- lazy-load cell previews and rich-output summaries;
- cap preview and evidence payload sizes.

Record scan and page-response timings during the pilot.  Set explicit
performance targets only after measuring representative repositories.

## Implementation stages

### Stage 0: contract and fixtures

Deliver:

- controlled vocabulary definitions;
- draft manifest schema and precedence rules;
- synthetic notebook fixtures;
- example manifest;
- written security and ownership boundaries.

Exit criteria:

- Scientific Python's known cases can be expressed without course-specific
  schema fields;
- unknown and deferred decisions remain representable;
- the manifest does not require modifying notebooks.

### Stage 1: read-only scanner and CLI

Deliver:

- installable tool-local package and Pixi environment;
- Git-based notebook inventory;
- static notebook and repository evidence extraction;
- deterministic JSON inventory;
- `scan` and `validate-manifest` subcommands;
- unit tests for malformed and hostile input.

Exit criteria:

- a Scientific Python scan completes without executing repository code;
- rerunning at the same commit produces equivalent output;
- parse failures are reported without losing the rest of the inventory.

### Stage 2: manifest engine

Status: implemented in the tool-local package.  Stage 3 will provide the human
review interface over these APIs.

Deliver:

- repository defaults, ordered path rules, and notebook overrides;
- schema validation and effective-value resolution;
- review provenance and blob-based staleness;
- atomic TOML writing and manifest diff generation;
- draft persistence outside the worktree.

Exit criteria:

- round trips preserve semantics and intentional comments;
- broad rules and exceptions resolve predictably;
- concurrent repository changes prevent unsafe writes.

### Stage 3: local web MVP

Deliver:

- loopback-only launcher;
- repository summary, notebook table, filters, and detail view;
- safe cell preview;
- editable decisions and per-property suggestion evidence;
- bulk edit, rule creation, override, progress, and final diff pages;
- keyboard-accessible core review flow.

Exit criteria:

- the Scientific Python review can be completed and resumed in the browser;
- the reviewer can distinguish facts, suggestions, inherited values, and
  confirmed decisions at every step;
- saving changes never modifies source notebooks.

### Stage 4: Scientific Python pilot

Deliver:

- a reviewed Scientific Python manifest;
- measured scan and review characteristics;
- a record of ambiguous or missing schema concepts;
- usability findings and prioritized revisions;
- an unresolved-items report feeding the validation pilot.

Do not stabilize the schema merely because all notebooks have values.  Review
whether the values are meaningful and whether bulk rules reduced work without
hiding exceptions.

### Stage 5: cross-repository hardening

Pilot the revised tool on at least:

- one repository dominated by notebooks but structured differently from
  Scientific Python;
- one repository where notebooks are secondary to scripts, slides, or compiled
  examples.

Deliver:

- schema and UI changes justified by cross-repository evidence;
- repository adapters only where generic inspection cannot express a real need;
- migration support for earlier manifest versions;
- documentation for course maintainers.

### Stage 6: catalogue overview and optional agent suggestions

Only after the single-repository workflow is stable, consider:

- a read-only catalogue view aggregating manifest completeness and staleness;
- batch opening of individual repository review sessions;
- report generation across locally available repositories;
- opt-in agent suggestions with explicit data-disclosure controls;
- reusable validation-runner integration.

A central database remains unnecessary while version-controlled manifests are
the authoritative records.

## Definition of done for the first usable release

- The package installs reproducibly on supported Linux and WSL systems.
- A documented command launches the local review interface.
- The scanner never executes course code or loads remote assets.
- Scientific Python can be inventoried, reviewed, saved, resumed, and rescanned.
- Bulk rules and per-notebook overrides are supported and visibly resolved.
- Suggested and confirmed properties cannot be confused in the UI or exports.
- The manifest has deterministic ordering, explicit versioning, and structural
  validation.
- Repository changes and stale reviews are detected before writing.
- Source notebooks remain unchanged throughout classification.
- Static, malformed-input, route, and security tests pass.
- Limitations and unclassified notebooks are reported explicitly.
- No automatic commits, pushes, issues, or external AI calls occur.

## Open design decisions

1. Should the course manifest remain `validation/manifest.toml`, or use a more
   specific name before catalogue-wide adoption?
2. Which classification fields are mandatory for an active core notebook?
3. Should a stable ID be generated from the initial path and then frozen, or
   always be chosen explicitly by the reviewer?
4. How should declared instructional errors identify allowed cells without
   making the manifest depend on fragile cell positions?
5. Which subset of Markdown and mathematical rendering is required in the MVP?
6. Should the Scientific Python pilot preserve unsupported Pixi platform
   metadata in the manifest, or record only the supported Linux environment?
7. Which second and third repositories provide the most informative structural
   contrast for hardening?
8. When should a changed notebook require complete re-review rather than simple
   confirmation of its previous classification?

Resolve these decisions through the Stage 0 fixtures and Scientific Python
pilot rather than embedding undocumented assumptions in the implementation.
