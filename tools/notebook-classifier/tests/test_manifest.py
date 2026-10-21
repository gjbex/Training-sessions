from __future__ import annotations

from pathlib import Path

from conftest import run_git

from notebook_classifier.manifest import validate_manifest


def write_manifest(repository: Path, text: str) -> Path:
    directory = repository / "validation"
    directory.mkdir(exist_ok=True)
    path = directory / "manifest.toml"
    path.write_text(text.lstrip(), encoding="utf-8")
    return path


def valid_manifest() -> str:
    return """
schema_version = 1
repository_id = "example-training"

[defaults]
lifecycle = "active"

[[rules]]
id = "tutorials"
include = ["notebooks/*.ipynb"]

[rules.properties]
role = "tutorial"
environment = "default"

[[notebooks]]
id = "tutorial"
path = "notebooks/tutorial.ipynb"

[notebooks.properties]
output_policy = "preserve_source"
validation_tier = "required"
"""


def test_valid_manifest(course_repository: Path) -> None:
    manifest = write_manifest(course_repository, valid_manifest())

    diagnostics = validate_manifest(course_repository, manifest)

    assert diagnostics == ()


def test_unknown_key_is_rejected(course_repository: Path) -> None:
    manifest = write_manifest(
        course_repository,
        valid_manifest().replace(
            'repository_id = "example-training"',
            'repository_id = "example-training"\nunexpected = true',
        ),
    )

    diagnostics = validate_manifest(course_repository, manifest)

    assert any(diagnostic.code == "schema_violation" for diagnostic in diagnostics)


def test_invalid_review_date_is_rejected(course_repository: Path) -> None:
    manifest = write_manifest(
        course_repository,
        valid_manifest().replace(
            'path = "notebooks/tutorial.ipynb"',
            'path = "notebooks/tutorial.ipynb"\nreviewed_on = "2026-02-31"',
        ),
    )

    diagnostics = validate_manifest(course_repository, manifest)

    assert any(diagnostic.code == "schema_violation" for diagnostic in diagnostics)


def test_duplicate_and_unsafe_notebook_are_rejected(course_repository: Path) -> None:
    manifest = write_manifest(
        course_repository,
        valid_manifest()
        + """

[[notebooks]]
id = "tutorial"
path = "../outside.ipynb"

[notebooks.properties]
lifecycle = "active"
""",
    )

    diagnostics = validate_manifest(course_repository, manifest)
    codes = {diagnostic.code for diagnostic in diagnostics}

    assert "duplicate_notebook_id" in codes
    assert "unsafe_notebook_path" in codes


def test_unsafe_rule_pattern_is_rejected(course_repository: Path) -> None:
    manifest = write_manifest(
        course_repository,
        valid_manifest().replace(
            'include = ["notebooks/*.ipynb"]',
            'include = ["../other-repository/*.ipynb"]',
        ),
    )

    diagnostics = validate_manifest(course_repository, manifest)

    assert any(diagnostic.code == "unsafe_rule_pattern" for diagnostic in diagnostics)


def test_windows_style_traversal_is_rejected(course_repository: Path) -> None:
    manifest = write_manifest(
        course_repository,
        valid_manifest().replace(
            'path = "notebooks/tutorial.ipynb"',
            'path = "..\\\\outside.ipynb"',
        ),
    )

    diagnostics = validate_manifest(course_repository, manifest)

    assert any(diagnostic.code == "unsafe_notebook_path" for diagnostic in diagnostics)


def test_repository_id_must_match_training_metadata(course_repository: Path) -> None:
    manifest = write_manifest(
        course_repository,
        valid_manifest().replace("example-training", "wrong-training", 1),
    )

    diagnostics = validate_manifest(course_repository, manifest)

    assert any(
        diagnostic.code == "repository_id_mismatch" for diagnostic in diagnostics
    )


def test_missing_manifest_is_reported(course_repository: Path) -> None:
    diagnostics = validate_manifest(course_repository, Path("validation/missing.toml"))

    assert diagnostics[0].code == "manifest_missing"


def test_replaced_notebook_requires_known_replacement(course_repository: Path) -> None:
    manifest = write_manifest(
        course_repository,
        valid_manifest()
        + """

[[notebooks]]
id = "old-tutorial"
path = "notebooks/old.ipynb"
replacement_id = "missing"

[notebooks.properties]
lifecycle = "replaced"
""",
    )

    diagnostics = validate_manifest(course_repository, manifest)

    assert any(diagnostic.code == "replacement_unknown" for diagnostic in diagnostics)


def test_manifest_path_cannot_escape_repository(course_repository: Path) -> None:
    outside = course_repository.parent / "outside.toml"
    outside.write_text(valid_manifest(), encoding="utf-8")

    try:
        validate_manifest(course_repository, outside)
    except ValueError as error:
        assert "escapes repository root" in str(error)
    else:
        raise AssertionError("outside manifest path was accepted")


def test_active_untracked_notebook_is_a_warning(course_repository: Path) -> None:
    manifest = write_manifest(
        course_repository,
        valid_manifest()
        + """

[[notebooks]]
id = "exercise"
path = "notebooks/exercise.ipynb"

[notebooks.properties]
lifecycle = "active"
""",
    )

    diagnostics = validate_manifest(course_repository, manifest)

    assert any(
        diagnostic.code == "active_notebook_not_tracked"
        and diagnostic.level == "warning"
        for diagnostic in diagnostics
    )


def test_tracked_notebook_stays_valid_after_manifest_is_added(
    course_repository: Path,
) -> None:
    manifest = write_manifest(course_repository, valid_manifest())
    run_git(course_repository, "add", str(manifest.relative_to(course_repository)))

    diagnostics = validate_manifest(course_repository, manifest)

    assert diagnostics == ()
