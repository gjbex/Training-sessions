"""Validate course-owned notebook results against an immutable plan."""

from __future__ import annotations

import copy
import hashlib
import json
from dataclasses import asdict, dataclass
from functools import cache
from importlib.resources import files
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator, FormatChecker

from notebook_classifier.planning import canonical_plan_json, validate_plan_document

SUMMARY_SCHEMA_VERSION = 1
EVIDENCE_BOUNDARY = (
    "These results report only the checks explicitly recorded by the course-owned "
    "runner. Successful execution does not establish scientific or pedagogical "
    "correctness."
)


class ResultsError(RuntimeError):
    """Raised when result inputs cannot be read as JSON documents."""


@dataclass(frozen=True)
class ResultDiagnostic:
    """One stable validation or provenance finding."""

    level: str
    code: str
    message: str
    notebook_id: str | None = None
    path: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ResultAssessment:
    """Validated, report-ready interpretation of one plan/result pair."""

    summary: dict[str, Any]
    diagnostics: tuple[ResultDiagnostic, ...]

    @property
    def has_errors(self) -> bool:
        return any(item.level == "error" for item in self.diagnostics)

    def to_dict(self) -> dict[str, Any]:
        return {
            **copy.deepcopy(self.summary),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }


def load_json_document(path: Path, *, label: str) -> dict[str, Any]:
    """Read a JSON object with an actionable, input-specific error."""

    try:
        document = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ResultsError(f"{label} does not exist: {path}") from error
    except json.JSONDecodeError as error:
        raise ResultsError(
            f"{label} is not valid JSON at line {error.lineno}, "
            f"column {error.colno}: {error.msg}"
        ) from error
    if not isinstance(document, dict):
        raise ResultsError(f"{label} must contain a JSON object")
    return document


def validate_result_document(document: dict[str, Any]) -> tuple[str, ...]:
    """Return stable JSON-Schema errors for a result document."""

    validator = Draft202012Validator(_result_schema(), format_checker=FormatChecker())
    return tuple(
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: "
        f"{error.message}"
        for error in sorted(
            validator.iter_errors(document), key=lambda item: list(item.path)
        )
    )


def assess_results(
    plan: dict[str, Any],
    results: dict[str, Any],
    *,
    artifact_root: Path | None = None,
) -> ResultAssessment:
    """Validate schema, provenance, outcome semantics, and artifact confinement."""

    diagnostics: list[ResultDiagnostic] = []
    plan_schema_errors = validate_plan_document(plan)
    diagnostics.extend(
        _diagnostic("plan_schema_invalid", message) for message in plan_schema_errors
    )
    result_schema_errors = validate_result_document(results)
    diagnostics.extend(
        _diagnostic("result_schema_invalid", message)
        for message in result_schema_errors
    )

    if plan_schema_errors:
        return ResultAssessment(
            summary=_empty_summary(plan), diagnostics=tuple(diagnostics)
        )

    expected_digest = _plan_digest(plan)
    plan_digest_invalid = plan.get("plan_digest") != expected_digest
    if plan_digest_invalid:
        diagnostics.append(
            _diagnostic(
                "plan_digest_invalid",
                "the plan digest does not match the canonical plan content",
            )
        )

    plan_entries = plan["entries"]
    plan_by_id: dict[str, dict[str, Any]] = {}
    duplicate_plan_ids: set[str] = set()
    for entry in plan_entries:
        notebook_id = entry["notebook_id"]
        if notebook_id is None:
            continue
        if notebook_id in plan_by_id:
            duplicate_plan_ids.add(notebook_id)
        else:
            plan_by_id[notebook_id] = entry
    for notebook_id in sorted(duplicate_plan_ids):
        diagnostics.append(
            _diagnostic(
                "duplicate_plan_notebook_id",
                f"plan notebook ID occurs more than once: {notebook_id}",
                notebook_id=notebook_id,
            )
        )

    result_entries = [] if result_schema_errors else results["entries"]
    results_by_id: dict[str, dict[str, Any]] = {}
    duplicate_result_ids: set[str] = set()
    for entry in result_entries:
        notebook_id = entry["notebook_id"]
        if notebook_id in results_by_id:
            duplicate_result_ids.add(notebook_id)
        else:
            results_by_id[notebook_id] = entry
    for notebook_id in sorted(duplicate_result_ids):
        diagnostics.append(
            _diagnostic(
                "duplicate_result_notebook_id",
                f"result notebook ID occurs more than once: {notebook_id}",
                notebook_id=notebook_id,
            )
        )
    for notebook_id in sorted(set(results_by_id) - set(plan_by_id)):
        entry = results_by_id[notebook_id]
        diagnostics.append(
            _diagnostic(
                "unknown_result_notebook_id",
                f"result notebook ID is absent from the plan: {notebook_id}",
                notebook_id=notebook_id,
                path=entry["path"],
            )
        )

    global_provenance_error = plan_digest_invalid or bool(duplicate_plan_ids)
    if not result_schema_errors:
        comparisons = (
            ("plan_digest", results["plan_digest"], plan["plan_digest"]),
            ("repository_id", results["repository"]["id"], plan["repository"]["id"]),
            (
                "repository_commit",
                results["repository"]["commit"],
                plan["repository"]["commit"],
            ),
            (
                "repository_platform",
                results["repository"]["platform"],
                plan["repository"]["platform"],
            ),
        )
        for label, observed, expected in comparisons:
            if observed != expected:
                global_provenance_error = True
                diagnostics.append(
                    _diagnostic(
                        f"{label}_mismatch",
                        f"result {label} {observed!r} does not match plan {expected!r}",
                    )
                )

    resolved_artifact_root = artifact_root.resolve() if artifact_root else None
    if resolved_artifact_root is not None and not resolved_artifact_root.is_dir():
        diagnostics.append(
            _diagnostic(
                "artifact_root_invalid",
                f"artifact root is not a directory: {resolved_artifact_root}",
            )
        )

    summary_entries: list[dict[str, Any]] = []
    outcome_counts = {name: 0 for name in ("pass", "fail", "error", "not_run")}
    action_counts = {name: 0 for name in ("candidate", "manual", "excluded", "blocked")}
    environment_metrics: dict[str, dict[str, Any]] = {}
    total_duration = 0.0
    exception_count = 0

    for plan_entry in plan_entries:
        action = plan_entry["action"]
        action_counts[action] += 1
        notebook_id = plan_entry["notebook_id"]
        environment = str(plan_entry["properties"].get("environment", "unknown"))
        metrics = environment_metrics.setdefault(
            environment,
            {
                "environment": environment,
                "planned_candidates": 0,
                "reported": 0,
                "duration_seconds": 0.0,
                "outcomes": {name: 0 for name in ("pass", "fail", "error", "not_run")},
            },
        )
        if action == "candidate":
            metrics["planned_candidates"] += 1

        result_entry = results_by_id.get(notebook_id) if notebook_id else None
        reported_outcome: str | None = None
        effective_outcome = "not_run"
        duration: float | None = None
        entry_invalid = global_provenance_error or notebook_id in duplicate_result_ids

        if result_entry is None:
            if action in {"candidate", "manual"}:
                diagnostics.append(
                    _diagnostic(
                        "selected_result_missing",
                        f"{action} entry has no result and is counted as not_run",
                        notebook_id=notebook_id,
                        path=plan_entry["path"],
                    )
                )
        else:
            metrics["reported"] += 1
            reported_outcome = result_entry["outcome"]
            effective_outcome = reported_outcome
            duration = result_entry["duration_seconds"]
            if duration is not None:
                total_duration += duration
                metrics["duration_seconds"] += duration

            for field, observed, expected in (
                ("path", result_entry["path"], plan_entry["path"]),
                (
                    "source_blob",
                    result_entry["source_blob"],
                    plan_entry["current_blob"],
                ),
                ("environment", result_entry["environment"], environment),
            ):
                if observed != expected:
                    entry_invalid = True
                    diagnostics.append(
                        _diagnostic(
                            f"result_{field}_mismatch",
                            f"result {field} {observed!r} does not match plan "
                            f"{expected!r}",
                            notebook_id=notebook_id,
                            path=plan_entry["path"],
                        )
                    )
            observed_environment = result_entry["observed_environment"]
            if (
                observed_environment is not None
                and observed_environment["name"] != environment
            ):
                entry_invalid = True
                diagnostics.append(
                    _diagnostic(
                        "result_observed_environment_mismatch",
                        "result observed_environment name "
                        f"{observed_environment['name']!r} does not match plan "
                        f"{environment!r}",
                        notebook_id=notebook_id,
                        path=plan_entry["path"],
                    )
                )

            if action in {"excluded", "blocked"} and reported_outcome != "not_run":
                entry_invalid = True
                diagnostics.append(
                    _entry_error(
                        "unexpected_execution_result",
                        "an excluded or blocked entry may only report not_run",
                        plan_entry,
                    )
                )
            if action in {"candidate", "manual"} and reported_outcome == "not_run":
                diagnostics.append(
                    _entry_error(
                        "selected_entry_not_run",
                        "a selected entry was explicitly not run",
                        plan_entry,
                    )
                )

            semantic_errors = _validate_entry_semantics(result_entry)
            if semantic_errors:
                entry_invalid = True
                diagnostics.extend(
                    _entry_error(code, message, plan_entry)
                    for code, message in semantic_errors
                )

            artifact_errors = _validate_artifacts(result_entry, resolved_artifact_root)
            if artifact_errors:
                entry_invalid = True
                diagnostics.extend(
                    _entry_error(code, message, plan_entry)
                    for code, message in artifact_errors
                )

            exception_count += int(reported_outcome == "error")
            exception_count += sum(
                check["outcome"] == "error" for check in result_entry["checks"]
            )

        if entry_invalid and result_entry is not None:
            effective_outcome = "error"
        outcome_counts[effective_outcome] += 1
        metrics["outcomes"][effective_outcome] += 1
        summary_entries.append(
            {
                "notebook_id": notebook_id,
                "path": plan_entry["path"],
                "planned_action": action,
                "reported": result_entry is not None,
                "reported_outcome": reported_outcome,
                "effective_outcome": effective_outcome,
                "reason_code": (
                    result_entry["reason_code"]
                    if result_entry is not None
                    else "result_missing"
                ),
                "environment": environment,
                "observed_environment": (
                    result_entry["observed_environment"]
                    if result_entry is not None
                    else None
                ),
                "duration_seconds": duration,
            }
        )

    diagnostics.sort(
        key=lambda item: (
            item.level,
            item.code,
            item.path or "",
            item.notebook_id or "",
            item.message,
        )
    )
    error_count = sum(item.level == "error" for item in diagnostics)
    warning_count = sum(item.level == "warning" for item in diagnostics)
    summary = {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "plan_digest": plan["plan_digest"],
        "repository": copy.deepcopy(plan["repository"]),
        "runner": (
            copy.deepcopy(results.get("runner")) if not result_schema_errors else None
        ),
        "complete": error_count == 0,
        "successful": all(
            entry["planned_action"] not in {"candidate", "manual"}
            or entry["effective_outcome"] == "pass"
            for entry in summary_entries
        ),
        "counts": {
            "planned_actions": action_counts,
            "effective_outcomes": outcome_counts,
            "diagnostics": {"errors": error_count, "warnings": warning_count},
        },
        "metrics": {
            "total_duration_seconds": round(total_duration, 9),
            "exception_count": exception_count,
        },
        "environments": [
            {
                **metrics,
                "duration_seconds": round(metrics["duration_seconds"], 9),
            }
            for _, metrics in sorted(environment_metrics.items())
        ],
        "entries": summary_entries,
    }
    return ResultAssessment(summary=summary, diagnostics=tuple(diagnostics))


def _validate_entry_semantics(entry: dict[str, Any]) -> list[tuple[str, str]]:
    errors: list[tuple[str, str]] = []
    outcome = entry["outcome"]
    checks = entry["checks"]
    check_outcomes = [item["outcome"] for item in checks]
    if not entry["worktree_unchanged"]:
        errors.append(
            ("worktree_changed", "runner reports that the source worktree changed")
        )
    if len({item["name"] for item in checks}) != len(checks):
        errors.append(("duplicate_check_name", "check names must be unique per entry"))
    if outcome == "pass":
        if not checks:
            errors.append(
                ("pass_without_checks", "pass requires at least one explicit check")
            )
        if any(value != "pass" for value in check_outcomes):
            errors.append(
                ("pass_with_nonpass_check", "pass contains a non-passing check")
            )
    if outcome == "fail" and "fail" not in check_outcomes:
        errors.append(("fail_without_failed_check", "fail requires a failed check"))
    if outcome in {"pass", "fail"} and any(
        entry[field] is None
        for field in ("started_at", "duration_seconds", "timeout_seconds")
    ):
        errors.append(
            (
                "attempt_timing_missing",
                "pass and fail require start time, duration, and timeout",
            )
        )
    if outcome in {"pass", "fail"} and entry["observed_environment"] is None:
        errors.append(
            (
                "observed_environment_missing",
                "an attempted result requires observed environment identity",
            )
        )
    if outcome == "not_run" and (
        any(
            entry[field] is not None
            for field in ("started_at", "duration_seconds", "timeout_seconds")
        )
        or entry["artifacts"]
        or checks
        or entry["observed_environment"] is not None
    ):
        errors.append(
            (
                "not_run_contains_execution_evidence",
                "not_run must not contain timing, artifacts, or checks",
            )
        )
    return errors


def _validate_artifacts(
    entry: dict[str, Any], artifact_root: Path | None
) -> list[tuple[str, str]]:
    artifacts = entry["artifacts"]
    if not artifacts:
        return []
    if artifact_root is None:
        return [
            (
                "artifact_root_required",
                "an explicit artifact root is required before artifacts are opened",
            )
        ]
    if not artifact_root.is_dir():
        return [
            (
                "artifact_root_invalid",
                f"artifact root is not a directory: {artifact_root}",
            )
        ]

    errors: list[tuple[str, str]] = []
    seen: set[str] = set()
    for artifact in artifacts:
        relative = artifact["path"]
        if relative in seen:
            errors.append(
                (
                    "duplicate_artifact_path",
                    f"duplicate artifact path: {relative}",
                )
            )
            continue
        seen.add(relative)
        candidate = (artifact_root / relative).resolve()
        if candidate != artifact_root and artifact_root not in candidate.parents:
            errors.append(
                (
                    "artifact_outside_root",
                    f"artifact resolves outside the declared root: {relative}",
                )
            )
            continue
        if not candidate.is_file():
            errors.append(("artifact_missing", f"artifact is not a file: {relative}"))
            continue
        observed_digest = _file_digest(candidate)
        if observed_digest != artifact["digest"]:
            errors.append(
                (
                    "artifact_digest_mismatch",
                    f"artifact digest does not match content: {relative}",
                )
            )
    return errors


def _empty_summary(plan: dict[str, Any]) -> dict[str, Any]:
    repository = plan.get("repository") if isinstance(plan, dict) else None
    return {
        "schema_version": SUMMARY_SCHEMA_VERSION,
        "evidence_boundary": EVIDENCE_BOUNDARY,
        "plan_digest": plan.get("plan_digest") if isinstance(plan, dict) else None,
        "repository": copy.deepcopy(repository),
        "runner": None,
        "complete": False,
        "successful": False,
        "counts": {
            "planned_actions": {},
            "effective_outcomes": {},
            "diagnostics": {"errors": 1, "warnings": 0},
        },
        "metrics": {"total_duration_seconds": 0.0, "exception_count": 0},
        "environments": [],
        "entries": [],
    }


def _plan_digest(plan: dict[str, Any]) -> str:
    content = copy.deepcopy(plan)
    content.pop("plan_digest", None)
    return hashlib.sha256(canonical_plan_json(content).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _diagnostic(
    code: str,
    message: str,
    *,
    notebook_id: str | None = None,
    path: str | None = None,
) -> ResultDiagnostic:
    return ResultDiagnostic(
        level="error",
        code=code,
        message=message,
        notebook_id=notebook_id,
        path=path,
    )


def _entry_error(
    code: str, message: str, plan_entry: dict[str, Any]
) -> ResultDiagnostic:
    return _diagnostic(
        code,
        message,
        notebook_id=plan_entry["notebook_id"],
        path=plan_entry["path"],
    )


@cache
def _result_schema() -> dict[str, Any]:
    resource = files("notebook_classifier.schemas").joinpath(
        "notebook-validation-result.schema.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))
