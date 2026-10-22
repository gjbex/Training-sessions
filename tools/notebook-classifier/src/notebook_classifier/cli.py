"""Command-line interface for static notebook inventory and manifest checks."""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from collections.abc import Sequence
from pathlib import Path

from notebook_classifier.git import GitError
from notebook_classifier.manifest import (
    ManifestError,
    ManifestValidationError,
    resolve_manifest,
    validate_manifest,
)
from notebook_classifier.planning import (
    CONSTRAINTS,
    DELIVERY_SCOPES,
    LIFECYCLES,
    REVIEW_POLICIES,
    SUPPORTED_PLATFORMS,
    VALIDATION_TIERS,
    PlanningError,
    PlanSelection,
    create_validation_plan,
)
from notebook_classifier.reporting import render_validation_markdown
from notebook_classifier.results import (
    ResultAssessment,
    ResultsError,
    assess_results,
    load_json_document,
)
from notebook_classifier.scaffolding import (
    SCAFFOLD_CI_CHOICES,
    SCAFFOLD_SCHEDULES,
    ScaffoldError,
    check_scaffold,
    render_scaffold,
    write_scaffold,
)
from notebook_classifier.scanner import scan_repository
from notebook_classifier.server import run_review_server


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="notebook-classifier",
        description="Inspect training notebooks without executing them.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    scan = subparsers.add_parser("scan", help="write a static notebook inventory")
    scan.add_argument(
        "--repository",
        type=Path,
        required=True,
        help="path inside the Git repository to inspect",
    )
    scan.add_argument(
        "--output",
        type=str,
        default="-",
        help="JSON output path, or - for standard output",
    )
    scan.add_argument(
        "--compact",
        action="store_true",
        help="write compact rather than indented JSON",
    )

    validate = subparsers.add_parser(
        "validate-manifest",
        help="validate a notebook classification manifest",
    )
    validate.add_argument(
        "--repository",
        type=Path,
        required=True,
        help="path inside the Git repository",
    )
    validate.add_argument(
        "--manifest",
        type=Path,
        default=Path("validation/manifest.toml"),
        help="manifest path inside the repository",
    )
    validate.add_argument(
        "--json",
        action="store_true",
        help="write machine-readable diagnostics",
    )

    resolve = subparsers.add_parser(
        "resolve-manifest",
        help="write effective classifications and per-property provenance",
    )
    resolve.add_argument(
        "--repository",
        type=Path,
        required=True,
        help="path inside the Git repository",
    )
    resolve.add_argument(
        "--manifest",
        type=Path,
        default=Path("validation/manifest.toml"),
        help="manifest path inside the repository",
    )
    resolve.add_argument(
        "--output",
        type=str,
        default="-",
        help="JSON output path, or - for standard output",
    )
    resolve.add_argument(
        "--compact",
        action="store_true",
        help="write compact rather than indented JSON",
    )

    plan = subparsers.add_parser(
        "create-validation-plan",
        help="write a deterministic notebook validation plan without execution",
    )
    plan.add_argument(
        "--repository",
        type=Path,
        required=True,
        help="path inside the Git repository",
    )
    plan.add_argument(
        "--manifest",
        type=Path,
        default=Path("validation/manifest.toml"),
        help="manifest path inside the repository",
    )
    plan.add_argument(
        "--include-tier",
        action="append",
        choices=VALIDATION_TIERS,
        help="validation tier to select; repeatable (default: required)",
    )
    plan.add_argument(
        "--include-scope",
        action="append",
        choices=DELIVERY_SCOPES,
        help="delivery scope to select; repeatable (default: all scopes)",
    )
    plan.add_argument(
        "--include-id",
        action="append",
        help="stable notebook ID to select; repeatable (default: all IDs)",
    )
    plan.add_argument(
        "--include-lifecycle",
        action="append",
        choices=LIFECYCLES,
        help="lifecycle to select; repeatable (default: active)",
    )
    plan.add_argument(
        "--review-policy",
        choices=REVIEW_POLICIES,
        default="warn",
        help="warn about non-current reviews or block selected entries",
    )
    plan.add_argument(
        "--allow-constraint",
        action="append",
        choices=CONSTRAINTS,
        help="declared constraint permitted by the target runner; repeatable",
    )
    plan.add_argument(
        "--platform",
        choices=SUPPORTED_PLATFORMS,
        default="linux-64",
        help="supported execution platform (default: linux-64)",
    )
    plan.add_argument(
        "--output",
        type=str,
        default="-",
        help="JSON output path, or - for standard output",
    )
    plan.add_argument(
        "--compact",
        action="store_true",
        help="write compact rather than indented JSON",
    )

    validate_results = subparsers.add_parser(
        "validate-validation-results",
        help="validate course-owned results against a validation plan",
    )
    _add_result_input_arguments(validate_results)
    validate_results.add_argument(
        "--json",
        action="store_true",
        help="write the complete machine-readable assessment",
    )

    summarize = subparsers.add_parser(
        "summarize-validation",
        help="summarize validated execution evidence without running notebooks",
    )
    _add_result_input_arguments(summarize)
    summarize.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="summary format (default: markdown)",
    )
    summarize.add_argument(
        "--output",
        type=str,
        default="-",
        help="summary output path, or - for standard output",
    )

    scaffold = subparsers.add_parser(
        "scaffold-validation",
        help="write or check a review-only target validation scaffold",
    )
    scaffold.add_argument(
        "--repository",
        type=Path,
        required=True,
        help="path inside the Git repository to plan for",
    )
    scaffold.add_argument(
        "--manifest",
        type=Path,
        default=Path("validation/manifest.toml"),
        help="manifest path inside the repository",
    )
    scaffold.add_argument(
        "--output-directory",
        type=Path,
        required=True,
        help="new external review directory, or existing directory with --check",
    )
    scaffold.add_argument(
        "--ci",
        choices=SCAFFOLD_CI_CHOICES,
        default="github-actions",
        help="CI draft to render (default: github-actions)",
    )
    scaffold.add_argument(
        "--schedule",
        choices=SCAFFOLD_SCHEDULES,
        default="manual",
        help="workflow trigger policy (default: manual)",
    )
    scaffold.add_argument(
        "--check",
        action="store_true",
        help="compare an existing scaffold without modifying it",
    )

    review = subparsers.add_parser(
        "review",
        help="review classifications in a loopback-only web interface",
    )
    review.add_argument(
        "--repository",
        type=Path,
        required=True,
        help="path inside the Git repository",
    )
    review.add_argument(
        "--manifest",
        type=Path,
        default=Path("validation/manifest.toml"),
        help="manifest path inside the repository",
    )
    review.add_argument(
        "--port",
        type=int,
        default=0,
        help="loopback TCP port; 0 chooses an available port (default: 0)",
    )
    review.add_argument(
        "--no-open",
        action="store_true",
        help="print the URL without opening a browser",
    )
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parser = create_parser()
    namespace = parser.parse_args(arguments)
    try:
        if namespace.command == "scan":
            return _scan(namespace)
        if namespace.command == "validate-manifest":
            return _validate_manifest(namespace)
        if namespace.command == "resolve-manifest":
            return _resolve_manifest(namespace)
        if namespace.command == "create-validation-plan":
            return _create_validation_plan(namespace)
        if namespace.command == "validate-validation-results":
            return _validate_validation_results(namespace)
        if namespace.command == "summarize-validation":
            return _summarize_validation(namespace)
        if namespace.command == "scaffold-validation":
            return _scaffold_validation(namespace)
        if namespace.command == "review":
            return _review(namespace)
    except (
        GitError,
        ManifestError,
        OSError,
        PlanningError,
        ResultsError,
        ScaffoldError,
        ValueError,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 2
    parser.error(f"unknown command: {namespace.command}")
    return 2


def _scan(namespace: argparse.Namespace) -> int:
    inventory = scan_repository(namespace.repository)
    indent = None if namespace.compact else 2
    payload = json.dumps(
        inventory.to_dict(),
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
    )
    if indent is not None:
        payload += "\n"
    _write_output(namespace.output, payload)
    return 1 if inventory.findings else 0


def _validate_manifest(namespace: argparse.Namespace) -> int:
    diagnostics = validate_manifest(namespace.repository, namespace.manifest)
    if namespace.json:
        print(
            json.dumps(
                [diagnostic.to_dict() for diagnostic in diagnostics],
                indent=2,
                sort_keys=True,
            )
        )
    elif diagnostics:
        for diagnostic in diagnostics:
            location = f" [{diagnostic.location}]" if diagnostic.location else ""
            print(
                f"{diagnostic.level}: {diagnostic.code}{location}: {diagnostic.message}"
            )
    else:
        print("manifest is valid")
    return 1 if any(item.level == "error" for item in diagnostics) else 0


def _resolve_manifest(namespace: argparse.Namespace) -> int:
    try:
        resolution = resolve_manifest(namespace.repository, namespace.manifest)
    except ManifestValidationError as error:
        for diagnostic in error.diagnostics:
            location = f" [{diagnostic.location}]" if diagnostic.location else ""
            print(
                f"{diagnostic.level}: {diagnostic.code}{location}: "
                f"{diagnostic.message}",
                file=sys.stderr,
            )
        return 1
    indent = None if namespace.compact else 2
    payload = json.dumps(
        resolution.to_dict(),
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
    )
    if indent is not None:
        payload += "\n"
    _write_output(namespace.output, payload)
    return 0


def _create_validation_plan(namespace: argparse.Namespace) -> int:
    try:
        inventory = scan_repository(namespace.repository)
        resolution = resolve_manifest(namespace.repository, namespace.manifest)
    except ManifestValidationError as error:
        for diagnostic in error.diagnostics:
            location = f" [{diagnostic.location}]" if diagnostic.location else ""
            print(
                f"{diagnostic.level}: {diagnostic.code}{location}: "
                f"{diagnostic.message}",
                file=sys.stderr,
            )
        return 1

    selection = PlanSelection.create(
        include_tiers=tuple(namespace.include_tier or ("required",)),
        include_scopes=tuple(namespace.include_scope or ()),
        include_ids=tuple(namespace.include_id or ()),
        include_lifecycles=tuple(namespace.include_lifecycle or ("active",)),
        review_policy=namespace.review_policy,
        allowed_constraints=tuple(namespace.allow_constraint or ()),
        platform=namespace.platform,
    )
    plan = create_validation_plan(inventory, resolution, selection)
    indent = None if namespace.compact else 2
    payload = json.dumps(
        plan.to_dict(),
        indent=indent,
        sort_keys=True,
        ensure_ascii=False,
    )
    if indent is not None:
        payload += "\n"
    _write_output(namespace.output, payload)
    return 1 if plan.has_blocked_entries else 0


def _validate_validation_results(namespace: argparse.Namespace) -> int:
    assessment = _load_result_assessment(namespace)
    if namespace.json:
        print(json.dumps(assessment.to_dict(), indent=2, sort_keys=True))
    elif assessment.diagnostics:
        for diagnostic in assessment.diagnostics:
            location = diagnostic.notebook_id or diagnostic.path
            suffix = f" [{location}]" if location else ""
            print(
                f"{diagnostic.level}: {diagnostic.code}{suffix}: {diagnostic.message}",
                file=sys.stderr,
            )
    else:
        print("validation results match the plan and declared artifacts")
    return 1 if assessment.has_errors else 0


def _summarize_validation(namespace: argparse.Namespace) -> int:
    assessment = _load_result_assessment(namespace)
    if namespace.format == "json":
        payload = (
            json.dumps(
                assessment.to_dict(), indent=2, sort_keys=True, ensure_ascii=False
            )
            + "\n"
        )
    else:
        payload = render_validation_markdown(assessment)
    _write_output(namespace.output, payload)
    return 1 if assessment.has_errors else 0


def _load_result_assessment(namespace: argparse.Namespace) -> ResultAssessment:
    plan = load_json_document(namespace.plan, label="validation plan")
    results = load_json_document(namespace.results, label="validation results")
    return assess_results(plan, results, artifact_root=namespace.artifact_root)


def _scaffold_validation(namespace: argparse.Namespace) -> int:
    try:
        inventory = scan_repository(namespace.repository)
        resolution = resolve_manifest(namespace.repository, namespace.manifest)
    except ManifestValidationError as error:
        for diagnostic in error.diagnostics:
            location = f" [{diagnostic.location}]" if diagnostic.location else ""
            print(
                f"{diagnostic.level}: {diagnostic.code}{location}: "
                f"{diagnostic.message}",
                file=sys.stderr,
            )
        return 1

    plan = create_validation_plan(inventory, resolution)
    rendered = render_scaffold(
        plan.to_dict(), ci=namespace.ci, schedule=namespace.schedule
    )
    if namespace.check:
        differences = check_scaffold(
            namespace.repository, namespace.output_directory, rendered
        )
        for difference in differences:
            print(f"{difference.state}: {difference.path}", file=sys.stderr)
        if not differences:
            print("scaffold matches the current template and plan")
        return int(bool(differences) or plan.has_blocked_entries)

    write_scaffold(namespace.repository, namespace.output_directory, rendered)
    print(f"wrote review scaffold to {namespace.output_directory.resolve()}")
    if plan.has_blocked_entries:
        print(
            "warning: the source plan has blocked entries; review its diagnostics",
            file=sys.stderr,
        )
    return int(plan.has_blocked_entries)


def _review(namespace: argparse.Namespace) -> int:
    run_review_server(
        namespace.repository,
        namespace.manifest,
        port=namespace.port,
        open_browser=not namespace.no_open,
    )
    return 0


def _write_output(destination: str, payload: str) -> None:
    if destination == "-":
        sys.stdout.write(payload)
        return
    path = Path(destination).expanduser().resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
        text=True,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8") as handle:
            handle.write(payload)
        temporary.replace(path)
    except BaseException:
        temporary.unlink(missing_ok=True)
        raise


def _add_result_input_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--plan",
        type=Path,
        required=True,
        help="validation plan JSON produced by create-validation-plan",
    )
    parser.add_argument(
        "--results",
        type=Path,
        required=True,
        help="course-owned validation result JSON",
    )
    parser.add_argument(
        "--artifact-root",
        type=Path,
        help="explicit root for all artifact paths referenced by the result",
    )
