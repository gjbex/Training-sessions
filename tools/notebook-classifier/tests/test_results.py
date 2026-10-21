from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

import pytest

from notebook_classifier.cli import main
from notebook_classifier.manifest import resolve_manifest
from notebook_classifier.planning import create_validation_plan
from notebook_classifier.reporting import render_validation_markdown
from notebook_classifier.results import assess_results, validate_result_document
from notebook_classifier.scanner import scan_repository


def _plan(course_repository: Path) -> dict:
    manifest = course_repository / "validation" / "manifest.toml"
    manifest.parent.mkdir()
    manifest.write_text(
        """
schema_version = 1
repository_id = "example-training"

[[notebooks]]
id = "tutorial"
path = "notebooks/tutorial.ipynb"

[notebooks.properties]
role = "tutorial"
delivery_scope = "core"
output_policy = "preserve_source"
validation_tier = "required"
environment = "default"
lifecycle = "active"
constraints = []
runtime = "short"
""".lstrip(),
        encoding="utf-8",
    )
    return create_validation_plan(
        scan_repository(course_repository), resolve_manifest(course_repository)
    ).to_dict()


def _result(plan: dict, *, artifacts: list[dict] | None = None) -> dict:
    entry = plan["entries"][0]
    return {
        "schema_version": 1,
        "runner": {"name": "fixture-runner", "version": "1"},
        "plan_digest": plan["plan_digest"],
        "repository": {
            "id": plan["repository"]["id"],
            "commit": plan["repository"]["commit"],
            "platform": plan["repository"]["platform"],
        },
        "entries": [
            {
                "notebook_id": entry["notebook_id"],
                "path": entry["path"],
                "source_blob": entry["current_blob"],
                "environment": entry["properties"]["environment"],
                "observed_environment": {
                    "name": entry["properties"]["environment"],
                    "python_version": "3.14.0",
                },
                "outcome": "pass",
                "reason_code": "execution_completed",
                "started_at": "2026-10-21T12:00:00Z",
                "duration_seconds": 1.25,
                "timeout_seconds": 30,
                "artifacts": artifacts or [],
                "checks": [
                    {
                        "name": "notebook_execution",
                        "outcome": "pass",
                        "message": "kernel completed",
                    }
                ],
                "worktree_unchanged": True,
            }
        ],
    }


def _codes(assessment) -> set[str]:
    return {item.code for item in assessment.diagnostics}


def test_complete_result_is_schema_valid_and_reported_honestly(
    course_repository: Path,
) -> None:
    plan = _plan(course_repository)
    result = _result(plan)

    assessment = assess_results(plan, result)
    markdown = render_validation_markdown(assessment)

    assert validate_result_document(result) == ()
    assert not assessment.has_errors
    assert assessment.summary["counts"]["effective_outcomes"] == {
        "pass": 1,
        "fail": 0,
        "error": 0,
        "not_run": 0,
    }
    assert assessment.summary["metrics"] == {
        "total_duration_seconds": 1.25,
        "exception_count": 0,
    }
    assert "does not establish scientific or pedagogical correctness" in markdown


def test_partial_or_interrupted_result_is_not_mistaken_for_pass(
    course_repository: Path,
) -> None:
    plan = _plan(course_repository)
    result = _result(plan)
    result["entries"] = []

    assessment = assess_results(plan, result)

    assert assessment.has_errors
    assert "selected_result_missing" in _codes(assessment)
    assert assessment.summary["counts"]["effective_outcomes"]["not_run"] == 1
    assert assessment.summary["counts"]["effective_outcomes"]["pass"] == 0


def test_duplicate_unknown_and_forged_results_are_prominent_failures(
    course_repository: Path,
) -> None:
    plan = _plan(course_repository)
    result = _result(plan)
    duplicate = copy.deepcopy(result["entries"][0])
    unknown = copy.deepcopy(duplicate)
    unknown["notebook_id"] = "forged-notebook"
    result["entries"].extend([duplicate, unknown])
    result["plan_digest"] = "0" * 64

    assessment = assess_results(plan, result)

    assert {
        "duplicate_result_notebook_id",
        "unknown_result_notebook_id",
        "plan_digest_mismatch",
    } <= _codes(assessment)
    assert assessment.summary["entries"][0]["effective_outcome"] == "error"


def test_duplicate_result_alone_invalidates_an_apparent_pass(
    course_repository: Path,
) -> None:
    plan = _plan(course_repository)
    result = _result(plan)
    result["entries"].append(copy.deepcopy(result["entries"][0]))

    assessment = assess_results(plan, result)

    assert "duplicate_result_notebook_id" in _codes(assessment)
    assert assessment.summary["entries"][0]["effective_outcome"] == "error"


def test_forged_plan_digest_and_commit_cannot_validate_each_other(
    course_repository: Path,
) -> None:
    plan = _plan(course_repository)
    plan["plan_digest"] = "0" * 64
    result = _result(plan)
    result["repository"]["commit"] = "f" * 40

    assessment = assess_results(plan, result)

    assert {"plan_digest_invalid", "repository_commit_mismatch"} <= _codes(assessment)
    assert assessment.summary["entries"][0]["effective_outcome"] == "error"


def test_path_blob_and_environment_mismatch_invalidate_a_reported_pass(
    course_repository: Path,
) -> None:
    plan = _plan(course_repository)
    result = _result(plan)
    result_entry = result["entries"][0]
    result_entry["path"] = "notebooks/other.ipynb"
    result_entry["source_blob"] = "0" * 40
    result_entry["environment"] = "other"
    result_entry["observed_environment"]["name"] = "other"

    assessment = assess_results(plan, result)

    assert {
        "result_path_mismatch",
        "result_source_blob_mismatch",
        "result_environment_mismatch",
        "result_observed_environment_mismatch",
    } <= _codes(assessment)
    assert assessment.summary["counts"]["effective_outcomes"]["pass"] == 0
    assert assessment.summary["counts"]["effective_outcomes"]["error"] == 1


def test_pass_requires_checks_and_an_unchanged_worktree(
    course_repository: Path,
) -> None:
    plan = _plan(course_repository)
    result = _result(plan)
    result["entries"][0]["checks"] = []
    result["entries"][0]["worktree_unchanged"] = False

    assessment = assess_results(plan, result)

    assert {"pass_without_checks", "worktree_changed"} <= _codes(assessment)
    assert assessment.summary["entries"][0]["effective_outcome"] == "error"


@pytest.mark.parametrize("outcome", ["fail", "error"])
def test_fail_and_error_remain_distinct_reported_outcomes(
    course_repository: Path, outcome: str
) -> None:
    plan = _plan(course_repository)
    result = _result(plan)
    entry = result["entries"][0]
    entry["outcome"] = outcome
    entry["reason_code"] = f"fixture_{outcome}"
    entry["checks"][0]["outcome"] = outcome

    assessment = assess_results(plan, result)

    assert not assessment.has_errors
    assert assessment.summary["counts"]["effective_outcomes"][outcome] == 1


def test_artifacts_require_a_confined_root_and_matching_digest(
    course_repository: Path, tmp_path: Path
) -> None:
    plan = _plan(course_repository)
    artifact_root = tmp_path / "artifacts"
    artifact_root.mkdir()
    artifact = artifact_root / "executed.ipynb"
    artifact.write_bytes(b"evidence")
    descriptor = {
        "kind": "executed_notebook",
        "path": "executed.ipynb",
        "digest": hashlib.sha256(b"evidence").hexdigest(),
    }

    valid = assess_results(
        plan, _result(plan, artifacts=[descriptor]), artifact_root=artifact_root
    )
    missing_root = assess_results(plan, _result(plan, artifacts=[descriptor]))
    forged = copy.deepcopy(descriptor)
    forged["digest"] = "0" * 64
    wrong_digest = assess_results(
        plan, _result(plan, artifacts=[forged]), artifact_root=artifact_root
    )
    outside = tmp_path / "outside.ipynb"
    outside.write_bytes(b"outside")
    (artifact_root / "escape.ipynb").symlink_to(outside)
    escaped_descriptor = {
        "kind": "executed_notebook",
        "path": "escape.ipynb",
        "digest": hashlib.sha256(b"outside").hexdigest(),
    }
    escaped = assess_results(
        plan,
        _result(plan, artifacts=[escaped_descriptor]),
        artifact_root=artifact_root,
    )

    assert not valid.has_errors
    assert "artifact_root_required" in _codes(missing_root)
    assert "artifact_digest_mismatch" in _codes(wrong_digest)
    assert "artifact_outside_root" in _codes(escaped)


def test_result_cli_validates_and_writes_json_or_markdown(
    course_repository: Path, tmp_path: Path, capsys
) -> None:
    plan = _plan(course_repository)
    result = _result(plan)
    plan_path = tmp_path / "plan.json"
    result_path = tmp_path / "result.json"
    report_path = tmp_path / "report.md"
    plan_path.write_text(json.dumps(plan), encoding="utf-8")
    result_path.write_text(json.dumps(result), encoding="utf-8")

    validate_status = main(
        [
            "validate-validation-results",
            "--plan",
            str(plan_path),
            "--results",
            str(result_path),
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    summary_status = main(
        [
            "summarize-validation",
            "--plan",
            str(plan_path),
            "--results",
            str(result_path),
            "--output",
            str(report_path),
        ]
    )

    assert validate_status == summary_status == 0
    assert payload["complete"] is True
    assert "Notebook validation evidence summary" in report_path.read_text(
        encoding="utf-8"
    )
