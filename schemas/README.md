# Training metadata schemas

This directory contains the canonical structural contracts for metadata used
across the training catalogue.

## `training.schema.json`

`training.schema.json` is a JSON Schema Draft 4 description of a repository's
`training.toml` when `schema_version = 2`.  Draft 4 is used for compatibility
with TOML tooling such as Taplo.

The schema covers document-local structure, including required fields, value
types, enumerations, identifier syntax, arrays of learning outcomes,
prerequisites, materials, trainers, and sessions.  It distinguishes
competencies provided by learning outcomes from competencies required as
prerequisites through their location in the document.

The schema does not replace catalogue-level semantic validation.  A separate
validator must load `ontology/competencies.toml` and all relevant training
documents to check at least:

- competency references resolve to registry entries;
- training identifiers are unique;
- declared session counts and durations agree with itemized schedules;
- referenced repository paths exist;
- learning-path constraints are interpreted consistently.

The repository-local TOML documents and this catalogue-owned schema and
ontology are authoritative.  Database indexes and graph representations should
be generated from those version-controlled sources.
