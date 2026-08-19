# Training-sessions

Overview of training sessions on (parallel) programming, scientific
computing, data analysis and HPC workflows.


## What is it?

This repository itself contains no training material.

It contains:

1. `scientific_computing_skills_and_trainings.pptx`: a PowerPoint
   presentation that provides an overview of the training sessions
   that are available, mapped to skill required in the context of
   scientific computing.
1. `docs`: the website that provides an overview of the training sessions,
   see: https://gjbex.github.io/Training-sessions/
1. `misc`: some supporting material such as reference slides,
   email templates and such.
1. `demo_material`: some material on software to create demos,
   mostly in terminal sessions.
1. `ontology`: the catalogue-wide controlled vocabulary of competencies that
   trainings can require or provide.
1. `schemas`: the canonical structural contracts for distributed training
   metadata, including `training.schema.json` for repository-local
   `training.toml` files.


## Training catalogue metadata

Training repositories own their course facts in a repository-local
`training.toml`.  This repository owns the catalogue-level interpretation of
those facts:

- `schemas/training.schema.json` defines the structure of a version 2
  `training.toml` document;
- `ontology/competencies.toml` defines the competencies referenced by learning
  outcomes and prerequisites;
- catalogue validation must additionally check that every competency reference
  resolves to the ontology and that cross-field rules hold;
- learning-path and catalogue tools should treat validated TOML as their source
  data and derive indexes or graph representations from it.

The JSON Schema validates one document at a time.  It cannot by itself verify
ontology membership, duration arithmetic, unique identifiers across
repositories, or the semantic adequacy of a proposed learning path.


## Create a custom HPC learning path with Codex

This repository includes a Codex skill that turns a concrete HPC goal into an
evidence-backed, prerequisite-aware training path.  It asks a few adaptive
questions about the intended work, current abilities and practical constraints,
then proposes a minimal core path with optional branches, readiness checks and
explicit gaps or uncertainty.

With Codex cloud, you do not need to clone the repository yourself: select this
GitHub repository as the task environment and use a prompt such as:

> Use `$hpc-learning-path-planner` from this repository to help me create a
> training path for my HPC goal. Start by asking up to three questions about
> what I want to do, my current experience and my constraints.

Codex checks out the selected repository and discovers the skill under
`.agents/skills`.  For detailed course evidence, it may also need internet or
GitHub access to read the training repositories linked from this catalogue.  If
that access is unavailable, the result should be treated as provisional because
some course details cannot be verified.

Using a local Codex environment remains supported: clone or open this repository
locally and start Codex anywhere inside it.  The root `AGENTS.md` and the
repository-local skill then provide the same project-specific guidance.


## New training repositories

Use the
[training-template](https://github.com/gjbex/training-template)
repository when creating a new training repository.  It provides the
standard layout, classic GitHub Pages setup using Jekyll and
`jekyll-theme-slate`, participant-facing documentation templates, setup
instructions, and placeholder-filling tooling.
