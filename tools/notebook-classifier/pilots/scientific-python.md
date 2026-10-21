# Scientific Python classifier pilot

Status: complete

Date: 2026-10-21

## Purpose and evidence boundary

This pilot evaluated whether the notebook classifier can inventory and support
a complete maintainer review of the Scientific Python notebook corpus.  It did
not execute notebooks, validate numerical results, or judge whether scientific
or pedagogical content is current.

The recorded evidence is tied to:

- notebook-classifier commit `5b7df42` on `feature/notebook-classifier`;
- Scientific Python manifest commit `4ff978c` on `feature/validation`;
- notebook content commit `2145d8f`, recorded by the manifest review entries;
- Linux with Python 3.14.8.

The next planned Scientific Python delivery tag, `20261023`, was not present
when this report was prepared.  A scan after the subsequent restructuring is a
separate robustness follow-up, not part of this baseline pilot.

## Outcome

The pilot produced a committed and pushed
`validation/manifest.toml` containing 47 notebook entries.  Structural and
semantic validation reported no diagnostics.  All 47 tracked notebooks have a
current reviewed blob and non-unknown values for the five required decisions:

- role;
- delivery scope;
- output policy;
- validation tier;
- environment.

The review used only static repository and notebook evidence.  Saving the
manifest did not modify notebook files.

## Corpus characteristics

| Measure | Observed value |
| --- | ---: |
| Tracked notebooks | 47 |
| Untracked notebooks | 2 |
| Ignored notebooks | 37 |
| Parse failures | 0 |
| Notebook bytes | 22,344,861 |
| Stored outputs | 669 |
| Stored error outputs | 0 |
| Estimated embedded output bytes | 8,700,591 |

All 37 ignored notebooks were Jupyter checkpoint files.  Ignored and untracked
notebooks were not classified.

The final required classification distributions were:

- role: 19 tutorials, 17 demonstrations, and 11 exercises;
- delivery scope: 19 core, 20 optional, 7 extended, and 1 historical;
- output policy: 33 preserve-source and 14 strip;
- validation tier: 19 required and 28 extended;
- environment: 36 default and 11 spread over seven specialized environments.

## Performance observations

These measurements are single local observations with potentially warm
filesystem caches.  They are useful for detecting gross regressions but are
not portable performance claims.

| Operation | Observed value |
| --- | ---: |
| Static scan | 2.63 s |
| Static scan peak resident memory | 105,376 KiB |
| Web application initialization | 3.802 s |
| Dashboard response | 0.011 s |
| Dashboard response body | 40,740 bytes |
| Largest-notebook detail response | 0.139 s |
| Largest notebook | 10,900,564 bytes |
| Largest-notebook response body | 54,995 bytes |

The human review duration was not instrumented and cannot be reconstructed
from the manifest.  The review completed on 2026-10-21.  The final manifest
contains no repository defaults or path rules: 368 property values are
notebook overrides, while 54 values come from vocabulary defaults.  Bulk edits
therefore reduced interaction effort without creating persistent path rules.

## Schema findings

The pilot did not expose a Scientific-Python-specific concept that requires an
immediate schema extension.  It did expose semantics that should remain under
review during Stage 5:

1. **Constraints versus static signals.**  No notebook has an explicit
   constraint, although static inspection found interactive signals in eight
   notebooks and network signals in six.  Network signals can be ordinary
   documentation links, so automatic conversion to constraints would create
   false positives.  Constraints should remain maintainer decisions.
2. **Delivery scope versus lifecycle.**  A notebook can be historically scoped
   while its artifact lifecycle remains active.  This is expressible, but the
   distinction needs clearer maintainer documentation.
3. **Required versus optional completeness.**  Runtime, rationale, lifecycle,
   and constraints can legitimately retain defaults or be absent after the
   required classification is complete.  The interface must not present review
   freshness as equivalent to required-field completeness.
4. **Rules versus explicit decisions.**  The corpus has repeated values that
   could be represented by rules, but the maintainer used explicit notebook
   decisions.  Rules should not be introduced merely to reduce manifest size;
   Stage 5 should determine whether they remain understandable across
   structurally different repositories.

## Usability findings and revisions

| Priority | Finding | Disposition |
| --- | --- | --- |
| P0 | Strict origin comparison rejected a legitimate local form submission. | Fixed in `5b7df42`; CSRF and loopback checks remain. |
| P0 | The overview conflated current review evidence with complete required decisions. | Fixed in `5b7df42`; freshness and completeness are separate and missing fields are listed. |
| P1 | Suggested role added little value in the notebook table without its evidence. | Removed from the table in `5b7df42`; evidence remains on the detail page. |
| P2 | The dashboard label `ignored` did not explain that it is a Git status category. | Open: rename or add explanatory text. |
| P2 | Bulk property values use a free-text field and are validated only after submission. | Open: use property-dependent controls if later pilots confirm the need. |
| P2 | The path-rule workflow was not exercised by the final manifest. | Open: evaluate in Stage 5 rather than forcing an artificial rule into this pilot. |

The first three findings materially changed the implementation.  The remaining
items are not blockers for the validation pilot.

## Conclusion

The Scientific Python pilot satisfies the Stage 4 deliverables: a reviewed
manifest, measured scan and review characteristics, recorded schema findings,
prioritized usability findings, and an explicit unresolved-items handoff.

The manifest is a classification contract, not an execution result.  Notebook
execution and scientific correctness belong to the subsequent validation
workflow.

See [scientific-python-unresolved.md](scientific-python-unresolved.md) for the
validation-pilot handoff.
