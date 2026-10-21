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
from notebook_classifier.manifest import validate_manifest
from notebook_classifier.scanner import scan_repository


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
    return parser


def main(arguments: Sequence[str] | None = None) -> int:
    parser = create_parser()
    namespace = parser.parse_args(arguments)
    try:
        if namespace.command == "scan":
            return _scan(namespace)
        if namespace.command == "validate-manifest":
            return _validate_manifest(namespace)
    except (GitError, OSError, ValueError) as error:
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
