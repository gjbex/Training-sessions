"""Create deterministic validation plans without executing course content."""

from __future__ import annotations

import copy
import hashlib
import json
import re
from dataclasses import asdict, dataclass, replace
from enum import StrEnum
from functools import cache
from importlib.resources import files
from typing import Any

from jsonschema import Draft202012Validator

from notebook_classifier import __version__
from notebook_classifier.manifest import ManifestResolution, ResolvedNotebook
from notebook_classifier.models import NotebookInventory, RepositoryInventory

PLAN_SCHEMA_VERSION = 1
RESULT_SCHEMA_VERSION = 1
GENERATOR_NAME = "training-notebook-classifier"
SUPPORTED_PLATFORMS = ("linux-64",)
VALIDATION_TIERS = ("required", "extended", "manual", "excluded", "unknown")
DELIVERY_SCOPES = (
    "core",
    "optional",
    "extended",
    "historical",
    "not_delivered",
    "unknown",
)
LIFECYCLES = ("active", "replaced", "retired", "suspended")
CONSTRAINTS = ("gui", "network", "gpu", "hpc", "large_data", "manual_interaction")
REVIEW_POLICIES = ("warn", "require-current")

_REQUIRED_CLASSIFICATION_FIELDS = (
    "role",
    "delivery_scope",
    "output_policy",
    "validation_tier",
    "environment",
)


class PlannedAction(StrEnum):
    """Course-runner disposition proposed by a validation plan."""

    CANDIDATE = "candidate"
    MANUAL = "manual"
    EXCLUDED = "excluded"
    BLOCKED = "blocked"


class PlanReason(StrEnum):
    """Stable machine-readable reasons for a planned action."""

    SELECTED = "selected"
    VALIDATION_TIER_MANUAL = "validation_tier_manual"
    VALIDATION_TIER_EXCLUDED = "validation_tier_excluded"
    VALIDATION_TIER_NOT_SELECTED = "validation_tier_not_selected"
    DELIVERY_SCOPE_NOT_SELECTED = "delivery_scope_not_selected"
    NOTEBOOK_ID_NOT_SELECTED = "notebook_id_not_selected"
    LIFECYCLE_NOT_SELECTED = "lifecycle_not_selected"
    LIFECYCLE_NOT_EXECUTABLE = "lifecycle_not_executable"
    NOTEBOOK_NOT_TRACKED = "notebook_not_tracked"
    NOTEBOOK_ID_MISSING = "notebook_id_missing"
    NOTEBOOK_PARSE_ERROR = "notebook_parse_error"
    CLASSIFICATION_UNKNOWN = "classification_unknown"
    ENVIRONMENT_MISSING = "environment_missing"
    REVIEW_NOT_CURRENT = "review_not_current"
    CONSTRAINT_NOT_ALLOWED = "constraint_not_allowed"


class PlanningError(RuntimeError):
    """Raised when inventory and manifest evidence cannot form a valid plan."""


@dataclass(frozen=True)
class PlanSelection:
    """Explicit, normalized policy used to select validation candidates."""

    include_tiers: tuple[str, ...] = ("required",)
    include_scopes: tuple[str, ...] = ()
    include_ids: tuple[str, ...] = ()
    include_lifecycles: tuple[str, ...] = ("active",)
    review_policy: str = "warn"
    allowed_constraints: tuple[str, ...] = ()
    platform: str = "linux-64"

    @classmethod
    def create(
        cls,
        *,
        include_tiers: tuple[str, ...] = ("required",),
        include_scopes: tuple[str, ...] = (),
        include_ids: tuple[str, ...] = (),
        include_lifecycles: tuple[str, ...] = ("active",),
        review_policy: str = "warn",
        allowed_constraints: tuple[str, ...] = (),
        platform: str = "linux-64",
    ) -> PlanSelection:
        """Validate and normalize a plan selection."""

        if not include_tiers:
            raise ValueError("at least one validation tier must be selected")
        if not include_lifecycles:
            raise ValueError("at least one lifecycle must be selected")
        if review_policy not in REVIEW_POLICIES:
            raise ValueError(f"unsupported review policy: {review_policy}")
        if platform not in SUPPORTED_PLATFORMS:
            raise ValueError(f"unsupported platform: {platform}")
        return cls(
            include_tiers=_ordered_unique(
                include_tiers, VALIDATION_TIERS, "validation tier"
            ),
            include_scopes=_ordered_unique(
                include_scopes, DELIVERY_SCOPES, "delivery scope"
            ),
            include_ids=_normalized_ids(include_ids),
            include_lifecycles=_ordered_unique(
                include_lifecycles, LIFECYCLES, "lifecycle"
            ),
            review_policy=review_policy,
            allowed_constraints=_ordered_unique(
                allowed_constraints, CONSTRAINTS, "constraint"
            ),
            platform=platform,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "include_tiers": list(self.include_tiers),
            "include_scopes": list(self.include_scopes),
            "include_ids": list(self.include_ids),
            "include_lifecycles": list(self.include_lifecycles),
            "review_policy": self.review_policy,
            "allowed_constraints": list(self.allowed_constraints),
            "platform": self.platform,
        }


@dataclass(frozen=True)
class PlanDiagnostic:
    """One deterministic finding produced while constructing a plan."""

    level: str
    code: str
    message: str
    path: str | None = None
    notebook_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ValidationPlanEntry:
    """Resolved evidence and proposed action for one notebook identity."""

    notebook_id: str | None
    path: str
    tracked: bool
    current_blob: str | None
    reviewed_blob: str | None
    review_state: str
    properties: dict[str, Any]
    provenance: dict[str, str]
    matched_rules: tuple[str, ...]
    replacement_id: str | None
    action: str
    reasons: tuple[str, ...]
    unresolved_fields: tuple[str, ...]
    required_target_inputs: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        for name in (
            "matched_rules",
            "reasons",
            "unresolved_fields",
            "required_target_inputs",
        ):
            payload[name] = list(payload[name])
        return payload


@dataclass(frozen=True)
class EnvironmentGroup:
    """Candidate notebook IDs grouped without embedding environment commands."""

    environment: str
    notebook_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "environment": self.environment,
            "notebook_ids": list(self.notebook_ids),
        }


@dataclass(frozen=True)
class ValidationPlan:
    """A deterministic, versioned projection of static repository evidence."""

    repository_id: str
    repository_commit: str
    repository_dirty: bool
    manifest_path: str
    manifest_schema_version: int
    manifest_source_digest: str
    inventory_schema_version: int
    inventory_digest: str
    selection: PlanSelection
    entries: tuple[ValidationPlanEntry, ...]
    environment_groups: tuple[EnvironmentGroup, ...]
    untracked_notebooks: tuple[str, ...]
    diagnostics: tuple[PlanDiagnostic, ...]
    plan_digest: str
    schema_version: int = PLAN_SCHEMA_VERSION
    generator_name: str = GENERATOR_NAME
    generator_version: str = __version__

    def to_dict(self, *, include_digest: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema_version": self.schema_version,
            "generator": {
                "name": self.generator_name,
                "version": self.generator_version,
            },
            "repository": {
                "id": self.repository_id,
                "commit": self.repository_commit,
                "dirty": self.repository_dirty,
                "platform": self.selection.platform,
            },
            "source": {
                "manifest_path": self.manifest_path,
                "manifest_schema_version": self.manifest_schema_version,
                "manifest_source_digest": self.manifest_source_digest,
                "inventory_schema_version": self.inventory_schema_version,
                "inventory_digest": self.inventory_digest,
            },
            "selection": self.selection.to_dict(),
            "entries": [entry.to_dict() for entry in self.entries],
            "environment_groups": [
                group.to_dict() for group in self.environment_groups
            ],
            "untracked_notebooks": list(self.untracked_notebooks),
            "diagnostics": [item.to_dict() for item in self.diagnostics],
        }
        if include_digest:
            payload["plan_digest"] = self.plan_digest
        return payload

    @property
    def has_blocked_entries(self) -> bool:
        return any(entry.action == PlannedAction.BLOCKED for entry in self.entries)


def create_validation_plan(
    inventory: RepositoryInventory,
    resolution: ManifestResolution,
    selection: PlanSelection | None = None,
) -> ValidationPlan:
    """Create and schema-check a plan from already resolved static evidence."""

    chosen = selection or PlanSelection.create()
    _validate_evidence_alignment(inventory, resolution)
    inventory_by_path = {notebook.path: notebook for notebook in inventory.notebooks}

    diagnostics = [
        PlanDiagnostic(
            level=item.level,
            code=item.code,
            message=item.message,
            path=item.location,
        )
        for item in resolution.diagnostics
    ]
    if inventory.untracked_notebooks:
        diagnostics.append(
            PlanDiagnostic(
                level="warning",
                code="untracked_notebooks_present",
                message=(
                    f"{len(inventory.untracked_notebooks)} untracked notebook(s) "
                    "are outside the validation manifest contract"
                ),
            )
        )

    entries: list[ValidationPlanEntry] = []
    for notebook in sorted(resolution.notebooks, key=lambda item: item.path):
        entry, entry_diagnostics = _plan_entry(
            notebook,
            inventory_by_path.get(notebook.path),
            inventory.pixi_environments,
            chosen,
        )
        entries.append(entry)
        diagnostics.extend(entry_diagnostics)

    sorted_diagnostics = tuple(
        sorted(
            diagnostics,
            key=lambda item: (
                item.path or "",
                item.notebook_id or "",
                item.level,
                item.code,
                item.message,
            ),
        )
    )
    groups = _environment_groups(entries)
    plan_without_digest = ValidationPlan(
        repository_id=resolution.repository_id,
        repository_commit=resolution.repository_commit,
        repository_dirty=inventory.dirty,
        manifest_path=resolution.manifest_path,
        manifest_schema_version=resolution.schema_version,
        manifest_source_digest=resolution.manifest_source_digest,
        inventory_schema_version=inventory.schema_version,
        inventory_digest=_payload_digest(inventory.to_dict()),
        selection=chosen,
        entries=tuple(entries),
        environment_groups=groups,
        untracked_notebooks=tuple(sorted(inventory.untracked_notebooks)),
        diagnostics=sorted_diagnostics,
        plan_digest="",
    )
    digest = _payload_digest(plan_without_digest.to_dict(include_digest=False))
    plan = replace(plan_without_digest, plan_digest=digest)
    schema_errors = validate_plan_document(plan.to_dict())
    if schema_errors:
        raise PlanningError("generated plan violates its schema: " + schema_errors[0])
    return plan


def validate_plan_document(document: dict[str, Any]) -> tuple[str, ...]:
    """Return stable JSON-Schema errors for a validation-plan document."""

    validator = Draft202012Validator(_plan_schema())
    return tuple(
        f"{'.'.join(str(part) for part in error.absolute_path) or '<root>'}: "
        f"{error.message}"
        for error in sorted(
            validator.iter_errors(document), key=lambda item: list(item.path)
        )
    )


def canonical_plan_json(document: dict[str, Any]) -> str:
    """Serialize plan content canonically for stable digest calculation."""

    return json.dumps(
        document,
        ensure_ascii=False,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def _plan_entry(
    notebook: ResolvedNotebook,
    inventory_notebook: NotebookInventory | None,
    available_environments: tuple[str, ...],
    selection: PlanSelection,
) -> tuple[ValidationPlanEntry, tuple[PlanDiagnostic, ...]]:
    properties = copy.deepcopy(notebook.properties)
    constraints = tuple(properties.get("constraints", ()))
    properties["constraints"] = list(constraints)
    unresolved: list[str] = []
    diagnostics: list[PlanDiagnostic] = []

    unknown_fields = tuple(
        field
        for field in _REQUIRED_CLASSIFICATION_FIELDS
        if properties.get(field) == "unknown"
    )
    if unknown_fields:
        unresolved.extend(f"classification.{field}" for field in unknown_fields)
        diagnostics.append(
            _entry_diagnostic(
                notebook,
                "error",
                "classification_unknown",
                "required classification remains unknown: " + ", ".join(unknown_fields),
            )
        )

    if properties.get("runtime") == "unknown":
        diagnostics.append(
            _entry_diagnostic(
                notebook,
                "warning",
                "runtime_unknown",
                "runtime category is unknown; no numeric timeout was inferred",
            )
        )

    if notebook.review_state != "current":
        diagnostics.append(
            _entry_diagnostic(
                notebook,
                "warning",
                "review_not_current",
                f"review state is {notebook.review_state}",
            )
        )

    if inventory_notebook is not None and inventory_notebook.parse_error is not None:
        unresolved.append("notebook.parse_error")
        diagnostics.append(
            _entry_diagnostic(
                notebook,
                "error",
                "notebook_parse_error",
                "notebook could not be parsed during static inventory",
            )
        )

    environment = properties.get("environment")
    if (
        environment not in (None, "unknown")
        and environment not in available_environments
    ):
        unresolved.append("environment.definition")
        diagnostics.append(
            _entry_diagnostic(
                notebook,
                "warning",
                "environment_missing",
                f"declared Pixi environment is not available: {environment}",
            )
        )

    unsupported_constraints = tuple(
        item for item in constraints if item not in selection.allowed_constraints
    )
    if unsupported_constraints:
        unresolved.extend(
            f"constraint.{constraint}" for constraint in unsupported_constraints
        )
        diagnostics.append(
            _entry_diagnostic(
                notebook,
                "warning",
                "constraint_not_allowed",
                "constraint is not allowed by this plan: "
                + ", ".join(unsupported_constraints),
            )
        )

    identity_blockers: list[str] = []
    if properties.get("lifecycle") == "active":
        if notebook.notebook_id is None:
            identity_blockers.append(PlanReason.NOTEBOOK_ID_MISSING)
            unresolved.append("classification.notebook_id")
        if unknown_fields:
            identity_blockers.append(PlanReason.CLASSIFICATION_UNKNOWN)

    selection_reasons: list[str] = []
    lifecycle = str(properties.get("lifecycle"))
    tier = str(properties.get("validation_tier"))
    scope = str(properties.get("delivery_scope"))
    if lifecycle not in selection.include_lifecycles:
        selection_reasons.append(PlanReason.LIFECYCLE_NOT_SELECTED)
    if tier not in selection.include_tiers:
        selection_reasons.append(PlanReason.VALIDATION_TIER_NOT_SELECTED)
    if selection.include_scopes and scope not in selection.include_scopes:
        selection_reasons.append(PlanReason.DELIVERY_SCOPE_NOT_SELECTED)
    if selection.include_ids and notebook.notebook_id not in selection.include_ids:
        selection_reasons.append(PlanReason.NOTEBOOK_ID_NOT_SELECTED)

    required_target_inputs: tuple[str, ...] = ()
    if identity_blockers:
        action = PlannedAction.BLOCKED
        reasons = identity_blockers
    elif selection_reasons:
        action = PlannedAction.EXCLUDED
        reasons = selection_reasons
    elif lifecycle != "active":
        action = PlannedAction.EXCLUDED
        reasons = [PlanReason.LIFECYCLE_NOT_EXECUTABLE]
    elif tier == "excluded":
        action = PlannedAction.EXCLUDED
        reasons = [PlanReason.VALIDATION_TIER_EXCLUDED]
    elif tier == "manual":
        action = PlannedAction.MANUAL
        reasons = [PlanReason.VALIDATION_TIER_MANUAL]
        required_target_inputs = ("manual_procedure",)
    else:
        execution_blockers: list[str] = []
        if not notebook.tracked:
            execution_blockers.append(PlanReason.NOTEBOOK_NOT_TRACKED)
            unresolved.append("repository.tracked_path")
        if (
            inventory_notebook is not None
            and inventory_notebook.parse_error is not None
        ):
            execution_blockers.append(PlanReason.NOTEBOOK_PARSE_ERROR)
        if environment not in available_environments:
            execution_blockers.append(PlanReason.ENVIRONMENT_MISSING)
        if (
            selection.review_policy == "require-current"
            and notebook.review_state != "current"
        ):
            execution_blockers.append(PlanReason.REVIEW_NOT_CURRENT)
            unresolved.append("review.current")
        if unsupported_constraints:
            execution_blockers.append(PlanReason.CONSTRAINT_NOT_ALLOWED)
        if execution_blockers:
            action = PlannedAction.BLOCKED
            reasons = execution_blockers
        else:
            action = PlannedAction.CANDIDATE
            reasons = [PlanReason.SELECTED]
            required_target_inputs = ("execution_mode", "timeout_seconds")

    entry = ValidationPlanEntry(
        notebook_id=notebook.notebook_id,
        path=notebook.path,
        tracked=notebook.tracked,
        current_blob=notebook.current_blob,
        reviewed_blob=notebook.reviewed_blob,
        review_state=notebook.review_state,
        properties=properties,
        provenance=dict(sorted(notebook.provenance.items())),
        matched_rules=notebook.matched_rules,
        replacement_id=notebook.replacement_id,
        action=str(action),
        reasons=tuple(str(reason) for reason in _unique(reasons)),
        unresolved_fields=tuple(sorted(set(unresolved))),
        required_target_inputs=required_target_inputs,
    )
    return entry, tuple(diagnostics)


def _environment_groups(
    entries: list[ValidationPlanEntry],
) -> tuple[EnvironmentGroup, ...]:
    by_environment: dict[str, list[str]] = {}
    for entry in entries:
        if entry.action != PlannedAction.CANDIDATE or entry.notebook_id is None:
            continue
        environment = str(entry.properties["environment"])
        by_environment.setdefault(environment, []).append(entry.notebook_id)
    return tuple(
        EnvironmentGroup(environment=name, notebook_ids=tuple(sorted(notebook_ids)))
        for name, notebook_ids in sorted(by_environment.items())
    )


def _validate_evidence_alignment(
    inventory: RepositoryInventory,
    resolution: ManifestResolution,
) -> None:
    if inventory.commit != resolution.repository_commit:
        raise PlanningError("inventory and manifest resolution use different commits")
    if (
        inventory.training_id is not None
        and inventory.training_id != resolution.repository_id
    ):
        raise PlanningError(
            "inventory and manifest resolution use different repository IDs"
        )

    inventory_blobs = {item.path: item.blob_id for item in inventory.notebooks}
    resolved_blobs = {
        item.path: item.current_blob for item in resolution.notebooks if item.tracked
    }
    if inventory_blobs != resolved_blobs:
        raise PlanningError(
            "inventory and manifest resolution use different notebook states"
        )


def _entry_diagnostic(
    notebook: ResolvedNotebook,
    level: str,
    code: str,
    message: str,
) -> PlanDiagnostic:
    return PlanDiagnostic(
        level=level,
        code=code,
        message=message,
        path=notebook.path,
        notebook_id=notebook.notebook_id,
    )


def _ordered_unique(
    values: tuple[str, ...],
    allowed: tuple[str, ...],
    label: str,
) -> tuple[str, ...]:
    invalid = sorted(set(values) - set(allowed))
    if invalid:
        raise ValueError(f"unsupported {label}: {', '.join(invalid)}")
    selected = set(values)
    return tuple(item for item in allowed if item in selected)


def _normalized_ids(values: tuple[str, ...]) -> tuple[str, ...]:
    invalid = sorted(
        value
        for value in set(values)
        if re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", value) is None
    )
    if invalid:
        raise ValueError(f"invalid notebook ID: {', '.join(invalid)}")
    return tuple(sorted(set(values)))


def _unique(values: list[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _payload_digest(payload: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_plan_json(payload).encode("utf-8")).hexdigest()


@cache
def _plan_schema() -> dict[str, Any]:
    resource = files("notebook_classifier.schemas").joinpath(
        "notebook-validation-plan.schema.json"
    )
    return json.loads(resource.read_text(encoding="utf-8"))
