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


## Create a custom HPC learning path with an AI coding agent

This repository includes an
[Agent Skill](https://agentskills.io/specification) that turns a concrete HPC
goal into an evidence-backed, prerequisite-aware training path.  It asks a few
adaptive questions about the intended work, current abilities and practical
constraints, then proposes a minimal core path with optional branches, readiness
checks and explicit gaps or uncertainty.

Point an AI coding agent at this repository and use this portable prompt:

> Read and follow
> `.agents/skills/hpc-learning-path-planner/SKILL.md` to help me create a
> training path for my HPC goal. Start by asking up to three questions about
> what I want to do, my current experience and my constraints.

The agent must be able to read this repository.  It may also need internet or
GitHub access to inspect detailed course evidence in the training repositories
linked from this catalogue.  If remote access is unavailable, treat the result
as provisional because some course details cannot be verified.

The setup depends on the agent environment:

- **Codex:** select this GitHub repository for a cloud task, or open a local
  checkout.  Codex automatically discovers the skill under `.agents/skills` and
  it can also be invoked as `$hpc-learning-path-planner`.
- **GitHub Copilot:** supported Copilot agents also discover project skills under
  `.agents/skills`.
- **Claude Code:** open a local checkout and use the portable prompt above.
  Claude Code uses `.claude/skills` for automatic project-skill discovery, so
  the current location is not discovered automatically.
- **Other agents:** if the environment supports repository access but does not
  discover Agent Skills or `AGENTS.md`, explicitly direct it to the `SKILL.md`
  file as shown above.


## New training repositories

Use the
[training-template](https://github.com/gjbex/training-template)
repository when creating a new training repository.  It provides the
standard layout, classic GitHub Pages setup using Jekyll and
`jekyll-theme-slate`, participant-facing documentation templates, setup
instructions, and placeholder-filling tooling.
