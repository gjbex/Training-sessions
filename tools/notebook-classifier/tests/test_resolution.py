from __future__ import annotations

from pathlib import Path

from conftest import run_git

from notebook_classifier.git import GitRepository
from notebook_classifier.manifest import resolve_manifest, validate_manifest


def write_resolution_manifest(repository: Path, reviewed_blob: str) -> Path:
    directory = repository / "validation"
    directory.mkdir(exist_ok=True)
    path = directory / "manifest.toml"
    path.write_text(
        f"""
schema_version = 1
repository_id = "example-training"

[defaults]
delivery_scope = "optional"
output_policy = "strip"

[[rules]]
id = "all-notebooks"
include = ["notebooks/*.ipynb"]

[rules.properties]
role = "tutorial"
validation_tier = "required"

[[rules]]
id = "tutorial-exception"
include = ["notebooks/tutorial.ipynb"]

[rules.properties]
role = "demonstration"
delivery_scope = "core"

[[notebooks]]
id = "tutorial"
path = "notebooks/tutorial.ipynb"
reviewed_by = "maintainer"
reviewed_on = "2026-10-21"
reviewed_commit = "{GitRepository.discover(repository).commit()}"
reviewed_blob = "{reviewed_blob}"

[notebooks.properties]
output_policy = "preserve_source"
validation_tier = "extended"
""".lstrip(),
        encoding="utf-8",
    )
    return path


def test_resolution_precedence_and_property_provenance(
    course_repository: Path,
) -> None:
    repository = GitRepository.discover(course_repository)
    blob = repository.blob_id("notebooks/tutorial.ipynb")
    write_resolution_manifest(course_repository, blob)

    resolution = resolve_manifest(course_repository)
    tutorial = resolution.notebooks[0]

    assert tutorial.path == "notebooks/tutorial.ipynb"
    assert tutorial.notebook_id == "tutorial"
    assert tutorial.matched_rules == ("all-notebooks", "tutorial-exception")
    assert tutorial.properties["role"] == "demonstration"
    assert tutorial.provenance["role"] == "rule:tutorial-exception"
    assert tutorial.properties["delivery_scope"] == "core"
    assert tutorial.provenance["delivery_scope"] == "rule:tutorial-exception"
    assert tutorial.properties["output_policy"] == "preserve_source"
    assert tutorial.provenance["output_policy"] == "notebook_override"
    assert tutorial.properties["runtime"] == "unknown"
    assert tutorial.provenance["runtime"] == "vocabulary_default"
    assert tutorial.review_state == "current"


def test_changed_blob_marks_review_stale(course_repository: Path) -> None:
    repository = GitRepository.discover(course_repository)
    blob = repository.blob_id("notebooks/tutorial.ipynb")
    write_resolution_manifest(course_repository, blob)
    notebook = course_repository / "notebooks" / "tutorial.ipynb"
    notebook.write_text(notebook.read_text(encoding="utf-8") + "\n", encoding="utf-8")

    resolution = resolve_manifest(course_repository)

    assert resolution.notebooks[0].review_state == "stale"
    assert resolution.notebooks[0].reviewed_blob == blob
    assert resolution.notebooks[0].current_blob != blob


def test_rule_exclusions_leave_non_matching_notebooks_at_defaults(
    course_repository: Path,
) -> None:
    run_git(course_repository, "add", "notebooks/exercise.ipynb")
    manifest = course_repository / "validation" / "manifest.toml"
    manifest.parent.mkdir()
    manifest.write_text(
        """
schema_version = 1
repository_id = "example-training"

[[rules]]
id = "tutorials-not-exercises"
include = ["notebooks/*.ipynb"]
exclude = ["notebooks/exercise.ipynb"]

[rules.properties]
role = "tutorial"
""".lstrip(),
        encoding="utf-8",
    )

    resolution = resolve_manifest(course_repository)
    by_path = {notebook.path: notebook for notebook in resolution.notebooks}

    assert by_path["notebooks/tutorial.ipynb"].properties["role"] == "tutorial"
    assert by_path["notebooks/exercise.ipynb"].properties["role"] == "unknown"
    assert by_path["notebooks/exercise.ipynb"].matched_rules == ()


def test_exact_blob_rename_is_candidate_not_identity_transfer(
    course_repository: Path,
) -> None:
    repository = GitRepository.discover(course_repository)
    blob = repository.blob_id("notebooks/tutorial.ipynb")
    write_resolution_manifest(course_repository, blob)
    run_git(
        course_repository,
        "mv",
        "notebooks/tutorial.ipynb",
        "notebooks/renamed.ipynb",
    )

    resolution = resolve_manifest(course_repository)
    by_path = {notebook.path: notebook for notebook in resolution.notebooks}

    old = by_path["notebooks/tutorial.ipynb"]
    renamed = by_path["notebooks/renamed.ipynb"]
    assert old.review_state == "missing"
    assert old.rename_candidates == ("notebooks/renamed.ipynb",)
    assert renamed.notebook_id is None
    assert renamed.review_state == "unreviewed"


def test_unmatched_rule_must_be_explicitly_retained(course_repository: Path) -> None:
    repository = GitRepository.discover(course_repository)
    blob = repository.blob_id("notebooks/tutorial.ipynb")
    manifest = write_resolution_manifest(course_repository, blob)
    text = manifest.read_text(encoding="utf-8")
    text += """

[[rules]]
id = "future-material"
include = ["future/*.ipynb"]

[rules.properties]
role = "tutorial"
"""
    manifest.write_text(text, encoding="utf-8")

    diagnostics = validate_manifest(course_repository, manifest)

    assert any(diagnostic.code == "rule_matches_nothing" for diagnostic in diagnostics)

    manifest.write_text(
        text.replace(
            'include = ["future/*.ipynb"]',
            'include = ["future/*.ipynb"]\nretain_if_unmatched = true',
        ),
        encoding="utf-8",
    )
    diagnostics = validate_manifest(course_repository, manifest)
    assert not any(
        diagnostic.code == "rule_matches_nothing" for diagnostic in diagnostics
    )


def test_replacement_cycles_are_rejected(course_repository: Path) -> None:
    path = course_repository / "validation" / "manifest.toml"
    path.parent.mkdir()
    path.write_text(
        """
schema_version = 1
repository_id = "example-training"

[[notebooks]]
id = "old-a"
path = "notebooks/old-a.ipynb"
replacement_id = "old-b"

[notebooks.properties]
lifecycle = "replaced"

[[notebooks]]
id = "old-b"
path = "notebooks/old-b.ipynb"
replacement_id = "old-a"

[notebooks.properties]
lifecycle = "replaced"
""".lstrip(),
        encoding="utf-8",
    )

    diagnostics = validate_manifest(course_repository, path)

    assert sum(item.code == "replacement_cycle" for item in diagnostics) == 1
