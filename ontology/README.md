# Training competency registry

`competencies.toml` is the catalog-wide controlled vocabulary for abilities
that a training can require or provide.  Training repositories keep ownership
of their own metadata and refer to registry entries by identifier.  Those
identifiers are intended to become stable after this draft has been reviewed.

This first version is deliberately a registry rather than a full ontology.  It
defines concrete, observable abilities found in the current catalog, but it
does not yet encode prerequisite rules, course mappings, relationships between
competencies, or proficiency levels.

## Scope

Include an entry when a participant's ability can be demonstrated by a small
task, such as submitting a Slurm job or slicing a NumPy array.  Do not add:

- broad claims such as "experience programming in Python";
- software, hardware, account, or installation requirements;
- course attendance as a proxy for an ability;
- material explicitly described as useful but not required;
- topics that the training itself teaches rather than requires.

Those distinctions matter: a prerequisite heading in a course page can contain
all of these, but only concrete, observable abilities belong in this registry.

## Identifier policy

Identifiers use lowercase dotted names.  The first component is the domain;
the remainder describes an ability, not a product version or a course.  An ID
should remain stable when its label or description is improved.  Once course
mappings use an ID, remove it only through an explicit deprecation and
replacement process.

The registry is marked `draft` while the first course mappings are reviewed, so
its identifiers are not stable yet.

## Intended next steps

1. Map original prerequisite statements to these identifiers outside the
   registry, preserving whether each statement is required, recommended,
   conditional, or an alternative.
2. Add missing competencies only when a concrete statement cannot be mapped
   without changing its meaning.
3. Add competencies provided by each training from its learning outcomes.
4. Introduce relationships or proficiency levels only when a real selection
   use case requires them.
