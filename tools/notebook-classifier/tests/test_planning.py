from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import replace
from importlib.resources import files
from pathlib import Path

import pytest
from conftest import FIXTURES, run_git
from jsonschema import Draft202012Validator, FormatChecker

from notebook_classifier.manifest import resolve_manifest
from notebook_classifier.planning import (
    PlannedAction,
    PlanningError,
    PlanReason,
    PlanSelection,
    canonical_plan_json,
    create_validation_plan,
    validate_plan_document,
)
from notebook_classifier.scanner import scan_repository


def _properties(
    *,
    tier: str,
    environment: str = "default",
    lifecycle: str = "active",
    constraints: tuple[str, ...] = (),
    role: str = "tutorial",
    scope: str = "core",
) -> str:
    constraint_values = ", ".join(f'"{value}"' for value in constraints)
    return f"""
role = "{role}"
delivery_scope = "{scope}"
output_policy = "preserve_source"
validation_tier = "{tier}"
environment = "{environment}"
lifecycle = "{lifecycle}"
constraints = [{constraint_values}]
runtime = "short"
""".strip()


def _entry(
    notebook_id: str,
    path: str,
    *,
    tier: str,
    environment: str = "default",
    lifecycle: str = "active",
    replacement_id: str | None = None,
    constraints: tuple[str, ...] = (),
    reviewed_blob: str | None = None,
    scope: str = "core",
) -> str:
    replacement = (
        f'replacement_id = "{replacement_id}"\n' if replacement_id is not None else ""
    )
    review = f'reviewed_blob = "{reviewed_blob}"\n' if reviewed_blob else ""
    properties = _properties(
        tier=tier,
        environment=environment,
        lifecycle=lifecycle,
        constraints=constraints,
        scope=scope,
    )
    return f"""
[[notebooks]]
id = "{notebook_id}"
path = "{path}"
{replacement}{review}
[notebooks.properties]
{properties}
""".strip()


def _write_manifest(repository: Path, *entries: str) -> Path:
    path = repository / "validation" / "manifest.toml"
    path.parent.mkdir(exist_ok=True)
    path.write_text(
        'schema_version = 1\nrepository_id = "example-training"\n\n'
        + "\n\n".join(entries)
        + "\n",
        encoding="utf-8",
    )
    return path


def _add_notebook(
    repository: Path,
    name: str,
    *,
    fixture: str = "exercise.ipynb",
) -> str:
    relative_path = f"notebooks/{name}.ipynb"
    shutil.copyfile(FIXTURES / fixture, repository / relative_path)
    run_git(repository, "add", relative_path)
    return relative_path


def test_plan_is_deterministic_schema_valid_and_path_independent(
    course_repository: Path,
) -> None:
    _write_manifest(
        course_repository,
        _entry("tutorial", "notebooks/tutorial.ipynb", tier="required"),
    )

    first = create_validation_plan(
        scan_repository(course_repository), resolve_manifest(course_repository)
    )
    second = create_validation_plan(
        scan_repository(course_repository), resolve_manifest(course_repository)
    )
    payload = first.to_dict()
    content_without_digest = dict(payload)
    digest = content_without_digest.pop("plan_digest")

    assert payload == second.to_dict()
    assert validate_plan_document(payload) == ()
    assert (
        digest
        == hashlib.sha256(
            canonical_plan_json(content_without_digest).encode("utf-8")
        ).hexdigest()
    )
    assert str(course_repository) not in json.dumps(payload)
    assert len(payload["entries"]) == 1
    assert payload["entries"][0]["action"] == "candidate"
    assert payload["entries"][0]["required_target_inputs"] == [
        "execution_mode",
        "timeout_seconds",
    ]
    assert payload["environment_groups"] == [
        {"environment": "default", "notebook_ids": ["tutorial"]}
    ]
    assert payload["untracked_notebooks"] == ["notebooks/exercise.ipynb"]


def test_plan_accounts_for_candidate_manual_excluded_and_historical_entries(
    course_repository: Path,
) -> None:
    extended = _add_notebook(course_repository, "extended")
    manual = _add_notebook(course_repository, "manual")
    excluded = _add_notebook(course_repository, "excluded")
    _write_manifest(
        course_repository,
        _entry("tutorial", "notebooks/tutorial.ipynb", tier="required"),
        _entry("extended", extended, tier="extended", environment="optional"),
        _entry("manual", manual, tier="manual"),
        _entry("excluded", excluded, tier="excluded"),
        _entry(
            "old-tutorial",
            "notebooks/old-tutorial.ipynb",
            tier="extended",
            lifecycle="replaced",
            replacement_id="tutorial",
        ),
    )
    selection = PlanSelection.create(
        include_tiers=("required", "extended", "manual", "excluded"),
        include_lifecycles=("active", "replaced"),
    )

    plan = create_validation_plan(
        scan_repository(course_repository),
        resolve_manifest(course_repository),
        selection,
    )
    by_id = {entry.notebook_id: entry for entry in plan.entries}

    assert len(plan.entries) == 5
    assert by_id["tutorial"].action == "candidate"
    assert by_id["extended"].action == "candidate"
    assert by_id["manual"].action == "manual"
    assert by_id["manual"].required_target_inputs == ("manual_procedure",)
    assert by_id["excluded"].action == "excluded"
    assert by_id["excluded"].reasons == ("validation_tier_excluded",)
    assert by_id["old-tutorial"].action == "excluded"
    assert by_id["old-tutorial"].reasons == ("lifecycle_not_executable",)
    assert plan.environment_groups[0].notebook_ids == ("tutorial",)
    assert plan.environment_groups[1].notebook_ids == ("extended",)


def test_missing_environment_and_unallowed_constraint_block_selected_entry(
    course_repository: Path,
) -> None:
    _write_manifest(
        course_repository,
        _entry(
            "tutorial",
            "notebooks/tutorial.ipynb",
            tier="required",
            environment="missing",
            constraints=("network",),
        ),
    )

    blocked = create_validation_plan(
        scan_repository(course_repository), resolve_manifest(course_repository)
    ).entries[0]
    network_allowed = create_validation_plan(
        scan_repository(course_repository),
        resolve_manifest(course_repository),
        PlanSelection.create(allowed_constraints=("network",)),
    ).entries[0]

    assert blocked.action == "blocked"
    assert blocked.reasons == ("environment_missing", "constraint_not_allowed")
    assert "environment.definition" in blocked.unresolved_fields
    assert "constraint.network" in blocked.unresolved_fields
    assert network_allowed.action == "blocked"
    assert network_allowed.reasons == ("environment_missing",)


def test_stale_review_warns_by_default_and_strict_policy_blocks(
    course_repository: Path,
) -> None:
    _write_manifest(
        course_repository,
        _entry(
            "tutorial",
            "notebooks/tutorial.ipynb",
            tier="required",
            reviewed_blob="0" * 40,
        ),
    )
    inventory = scan_repository(course_repository)
    resolution = resolve_manifest(course_repository)

    warning_plan = create_validation_plan(inventory, resolution)
    strict_plan = create_validation_plan(
        inventory,
        resolution,
        PlanSelection.create(review_policy="require-current"),
    )

    assert warning_plan.entries[0].action == "candidate"
    assert strict_plan.entries[0].action == "blocked"
    assert strict_plan.entries[0].reasons == ("review_not_current",)
    assert any(item.code == "review_not_current" for item in strict_plan.diagnostics)


def test_scope_filter_and_linux_only_policy_are_explicit(
    course_repository: Path,
) -> None:
    _write_manifest(
        course_repository,
        _entry(
            "tutorial",
            "notebooks/tutorial.ipynb",
            tier="required",
            scope="optional",
        ),
    )
    selection = PlanSelection.create(
        include_tiers=("required", "required"),
        include_scopes=("core",),
        include_lifecycles=("active", "active"),
    )

    plan = create_validation_plan(
        scan_repository(course_repository),
        resolve_manifest(course_repository),
        selection,
    )

    assert selection.include_tiers == ("required",)
    assert selection.include_lifecycles == ("active",)
    assert plan.entries[0].action == "excluded"
    assert plan.entries[0].reasons == ("delivery_scope_not_selected",)
    with pytest.raises(ValueError, match="unsupported platform"):
        PlanSelection.create(platform="win-64")


def test_stable_id_filter_retains_nonselected_entries(
    course_repository: Path,
) -> None:
    second_path = _add_notebook(course_repository, "second")
    _write_manifest(
        course_repository,
        _entry("tutorial", "notebooks/tutorial.ipynb", tier="required"),
        _entry("second", second_path, tier="required"),
    )

    plan = create_validation_plan(
        scan_repository(course_repository),
        resolve_manifest(course_repository),
        PlanSelection.create(include_ids=("tutorial", "tutorial")),
    )
    by_id = {entry.notebook_id: entry for entry in plan.entries}

    assert plan.selection.include_ids == ("tutorial",)
    assert by_id["tutorial"].action == "candidate"
    assert by_id["second"].action == "excluded"
    assert by_id["second"].reasons == ("notebook_id_not_selected",)


def test_invalid_stable_id_filter_is_rejected() -> None:
    with pytest.raises(ValueError, match="invalid notebook ID"):
        PlanSelection.create(include_ids=("../tutorial",))


def test_unknown_active_notebook_is_blocked_not_filtered_away(
    course_repository: Path,
) -> None:
    _write_manifest(course_repository)

    plan = create_validation_plan(
        scan_repository(course_repository), resolve_manifest(course_repository)
    )
    entry = plan.entries[0]

    assert entry.action == "blocked"
    assert entry.reasons == ("notebook_id_missing", "classification_unknown")
    assert "classification.validation_tier" in entry.unresolved_fields


def test_parse_failure_blocks_only_when_its_tier_is_selected(
    course_repository: Path,
) -> None:
    invalid = _add_notebook(
        course_repository,
        "invalid",
        fixture="invalid.ipynb",
    )
    _write_manifest(
        course_repository,
        _entry("tutorial", "notebooks/tutorial.ipynb", tier="required"),
        _entry("invalid", invalid, tier="extended"),
    )
    inventory = scan_repository(course_repository)
    resolution = resolve_manifest(course_repository)

    required_plan = create_validation_plan(inventory, resolution)
    extended_plan = create_validation_plan(
        inventory,
        resolution,
        PlanSelection.create(include_tiers=("extended",)),
    )
    required_invalid = next(
        entry for entry in required_plan.entries if entry.notebook_id == "invalid"
    )
    extended_invalid = next(
        entry for entry in extended_plan.entries if entry.notebook_id == "invalid"
    )

    assert required_invalid.action == "excluded"
    assert extended_invalid.action == "blocked"
    assert extended_invalid.reasons == ("notebook_parse_error",)


def test_mismatched_inventory_and_resolution_are_rejected(
    course_repository: Path,
) -> None:
    _write_manifest(
        course_repository,
        _entry("tutorial", "notebooks/tutorial.ipynb", tier="required"),
    )
    inventory = scan_repository(course_repository)
    resolution = resolve_manifest(course_repository)

    with pytest.raises(PlanningError, match="different commits"):
        create_validation_plan(replace(inventory, commit="0" * 40), resolution)


def test_plan_schema_rejects_unknown_keys(course_repository: Path) -> None:
    _write_manifest(
        course_repository,
        _entry("tutorial", "notebooks/tutorial.ipynb", tier="required"),
    )
    payload = create_validation_plan(
        scan_repository(course_repository), resolve_manifest(course_repository)
    ).to_dict()
    payload["unexpected"] = True

    assert any(
        "Additional properties" in item for item in validate_plan_document(payload)
    )


def test_plan_vocabulary_matches_manifest_schema() -> None:
    schema_package = files("notebook_classifier.schemas")
    manifest_schema = json.loads(
        schema_package.joinpath("notebook-validation.schema.json").read_text(
            encoding="utf-8"
        )
    )
    plan_schema = json.loads(
        schema_package.joinpath("notebook-validation-plan.schema.json").read_text(
            encoding="utf-8"
        )
    )
    manifest_properties = manifest_schema["$defs"]["classificationProperties"][
        "properties"
    ]
    plan_properties = plan_schema["$defs"]["classification"]["properties"]

    for name in (
        "role",
        "delivery_scope",
        "output_policy",
        "validation_tier",
        "lifecycle",
        "runtime",
    ):
        assert plan_properties[name]["enum"] == manifest_properties[name]["enum"]
    assert (
        plan_properties["constraints"]["items"]["enum"]
        == manifest_properties["constraints"]["items"]["enum"]
    )
    assert plan_schema["$defs"]["entry"]["properties"]["action"]["enum"] == [
        str(item) for item in PlannedAction
    ]
    assert plan_schema["$defs"]["entry"]["properties"]["reasons"]["items"]["enum"] == [
        str(item) for item in PlanReason
    ]


def test_validation_interchange_schemas_are_valid_json_schemas() -> None:
    schema_package = files("notebook_classifier.schemas")
    for name in (
        "notebook-validation-plan.schema.json",
        "notebook-validation-result.schema.json",
    ):
        schema = json.loads(schema_package.joinpath(name).read_text(encoding="utf-8"))
        Draft202012Validator.check_schema(schema)


def test_result_schema_accepts_not_run_and_rejects_extra_key() -> None:
    schema = json.loads(
        files("notebook_classifier.schemas")
        .joinpath("notebook-validation-result.schema.json")
        .read_text(encoding="utf-8")
    )
    validator = Draft202012Validator(schema, format_checker=FormatChecker())
    result = {
        "schema_version": 1,
        "runner": {"name": "example-runner", "version": "1"},
        "plan_digest": "a" * 64,
        "repository": {
            "id": "example-training",
            "commit": "b" * 40,
            "platform": "linux-64",
        },
        "entries": [
            {
                "notebook_id": "tutorial",
                "path": "notebooks/tutorial.ipynb",
                "source_blob": None,
                "environment": "default",
                "observed_environment": None,
                "outcome": "not_run",
                "reason_code": "not_selected",
                "started_at": None,
                "duration_seconds": None,
                "timeout_seconds": None,
                "artifacts": [],
                "checks": [],
                "worktree_unchanged": True,
            }
        ],
    }

    assert list(validator.iter_errors(result)) == []
    result["unexpected"] = True
    assert list(validator.iter_errors(result))
