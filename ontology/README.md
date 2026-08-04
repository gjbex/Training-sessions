# Training competency registry

`competencies.toml` is the catalog-wide controlled vocabulary for abilities
that a training can require or provide.  Training repositories keep ownership
of their own metadata and refer to registry entries by identifier.  Those
identifiers are intended to become stable after this draft has been reviewed.

This is deliberately a registry rather than a full ontology.  It defines
concrete, observable abilities found on both sides of the current catalog:
competencies required before a training and competencies addressed by its
learning outcomes.  It does not yet encode prerequisite rules, course mappings,
relationships between competencies, or proficiency levels.

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

Learning outcomes are treated similarly.  A broad promise such as "have a
solid foundation" is not registered on its own.  Compound outcomes are split
or abstracted into reusable abilities that can plausibly be matched with
another training's prerequisites.  Conceptual understanding and practical use
remain separate competencies when they can be demonstrated independently.

A training that references an output competency claims to address and provide
practice for it.  It does not certify that every participant acquired the
competency.  Assessment or certification evidence may be represented later if
the catalog needs stronger claims.

## Coverage of the learning-outcome pass

The August 2026 pass inspected explicit learning outcomes in 26 catalog course
repositories whose participant page is `docs/README.md`, plus
`Best-practices-for-scientific-computing/docs/training_overview.md`.  Existing
competencies were reused where possible; new entries represent transferable
abilities rather than literal copies of course-specific wording.

No outcomes were inferred for catalog entries that currently provide only a
description or subject list, including the Linux and HPC introductions,
parallel programming with MPI, OpenMP, or STL/TBB, generative AI, and ParaView.
The defensive-programming repository was not available in the WSL catalog
checkout.  Those trainings require explicit learning outcomes before their
output coverage can be considered complete.

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
2. Map each participant-facing learning outcome to one or more competencies in
   its training repository; leave broad or non-observable outcomes unmapped.
3. Add missing competencies only when a concrete statement cannot be mapped
   without changing its meaning.
4. Introduce relationships or proficiency levels only when a real selection
   use case requires them.
