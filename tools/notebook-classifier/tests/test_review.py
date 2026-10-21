from __future__ import annotations

import shutil
import tomllib
from pathlib import Path

from conftest import FIXTURES, run_git

from notebook_classifier.review import ReviewState


def complete_values() -> dict[str, object]:
    return {
        "role": "tutorial",
        "delivery_scope": "core",
        "output_policy": "preserve_source",
        "validation_tier": "required",
        "environment": "default",
        "lifecycle": "active",
        "runtime": "short",
        "constraints": None,
        "rationale": "Core instructor-led tutorial.",
    }


def test_decision_is_drafted_without_modifying_source_notebook(
    course_repository: Path, tmp_path: Path
) -> None:
    notebook = course_repository / "notebooks" / "tutorial.ipynb"
    before = notebook.read_bytes()
    state = ReviewState(course_repository, draft_root=tmp_path / "drafts")

    state.update_notebook(
        "notebooks/tutorial.ipynb", complete_values(), reviewer="Maintainer"
    )

    resolved = state.resolved_notebook("notebooks/tutorial.ipynb")
    assert resolved.review_state == "current"
    assert resolved.properties["role"] == "tutorial"
    assert resolved.provenance["role"] == "notebook_override"
    assert state.progress().complete == 1
    assert state.progress().decisions_complete == 1
    assert state.missing_required_decisions(resolved) == ()
    assert state.has_unsaved_changes
    assert notebook.read_bytes() == before
    assert not (course_repository / "validation" / "manifest.toml").exists()
    assert list((tmp_path / "drafts").rglob("*.json"))


def test_matching_draft_is_resumed(course_repository: Path, tmp_path: Path) -> None:
    root = tmp_path / "drafts"
    first = ReviewState(course_repository, draft_root=root)
    first.update_notebook(
        "notebooks/tutorial.ipynb", complete_values(), reviewer="Maintainer"
    )

    resumed = ReviewState(course_repository, draft_root=root)

    assert resumed.resumed_draft
    assert (
        resumed.resolved_notebook("notebooks/tutorial.ipynb").properties[
            "delivery_scope"
        ]
        == "core"
    )


def test_rule_is_inherited_but_explicit_override_wins(
    course_repository: Path, tmp_path: Path
) -> None:
    state = ReviewState(course_repository, draft_root=tmp_path / "drafts")
    state.add_rule(
        rule_id="all-tutorials",
        include="notebooks/*.ipynb",
        exclude=(),
        property_name="role",
        value="tutorial",
    )
    inherited = state.resolved_notebook("notebooks/tutorial.ipynb")
    assert inherited.properties["role"] == "tutorial"
    assert inherited.provenance["role"] == "rule:all-tutorials"

    state.update_notebook(
        "notebooks/tutorial.ipynb",
        {"role": "demonstration"},
        reviewer="Maintainer",
    )

    overridden = state.resolved_notebook("notebooks/tutorial.ipynb")
    assert overridden.properties["role"] == "demonstration"
    assert overridden.provenance["role"] == "notebook_override"


def test_bulk_update_records_each_selected_notebook(
    course_repository: Path, tmp_path: Path
) -> None:
    exercise = course_repository / "notebooks" / "exercise.ipynb"
    shutil.copyfile(FIXTURES / "exercise.ipynb", exercise)
    run_git(course_repository, "add", str(exercise.relative_to(course_repository)))
    state = ReviewState(course_repository, draft_root=tmp_path / "drafts")

    state.bulk_update(
        ["notebooks/tutorial.ipynb", "notebooks/exercise.ipynb"],
        property_name="delivery_scope",
        value="core",
        reviewer="Maintainer",
    )

    for path in ("notebooks/tutorial.ipynb", "notebooks/exercise.ipynb"):
        resolved = state.resolved_notebook(path)
        assert resolved.properties["delivery_scope"] == "core"
        assert resolved.provenance["delivery_scope"] == "notebook_override"
        assert resolved.review_state == "current"
        assert state.missing_required_decisions(resolved) == (
            "role",
            "output_policy",
            "validation_tier",
            "environment",
        )
    assert state.progress().decisions_complete == 0


def test_final_save_writes_only_manifest(
    course_repository: Path, tmp_path: Path
) -> None:
    notebook = course_repository / "notebooks" / "tutorial.ipynb"
    before = notebook.read_bytes()
    state = ReviewState(course_repository, draft_root=tmp_path / "drafts")
    state.update_notebook(
        "notebooks/tutorial.ipynb", complete_values(), reviewer="Maintainer"
    )

    destination = state.save_manifest()

    assert destination == course_repository / "validation" / "manifest.toml"
    document = tomllib.loads(destination.read_text(encoding="utf-8"))
    assert document["notebooks"][0]["properties"]["role"] == "tutorial"
    assert notebook.read_bytes() == before
    assert not list((tmp_path / "drafts").rglob("*.json"))
