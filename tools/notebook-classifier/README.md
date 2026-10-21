# Notebook classifier

`notebook-classifier` inventories Jupyter notebooks in a Git repository and
validates the sidecar manifest that records maintainer decisions about notebook
roles, output policies, delivery scope, and validation tiers.

The current implementation covers Stage 0 and Stage 1 of the
[implementation plan](IMPLEMENTATION_PLAN.md): the classification contract,
synthetic fixtures, a read-only scanner, deterministic JSON output, and
manifest validation.  It does not yet provide the local web interface.

## Trust boundary

The scanner treats repositories and notebook content as untrusted data.  It:

- inspects only an explicitly supplied local Git repository;
- never executes notebook cells or repository commands;
- never imports dependencies named by a notebook;
- invokes Git without a shell;
- writes only the requested JSON inventory output;
- leaves notebook files unchanged.

The manifest validator reads `validation/manifest.toml` by default.  It reports
structural and semantic errors but does not edit the manifest.

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

## Developer checks

```bash
pixi run check
```

This runs Ruff linting, Ruff formatting checks, and the test suite.

## Current limitations

- Evidence extraction is intentionally conservative and heuristic.
- The scanner handles Jupyter notebooks only.
- It does not yet resolve defaults, rules, and overrides into an editable
  review model.
- It records notebook and repository evidence but does not make classification
  suggestions yet.
- The web review interface, draft persistence, and atomic manifest writer are
  later stages.

