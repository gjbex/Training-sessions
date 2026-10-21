from __future__ import annotations

import json
import shutil
from pathlib import Path

from conftest import run_git

from notebook_classifier.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_cli_writes_json(course_repository: Path, tmp_path: Path) -> None:
    output = tmp_path / "inventory.json"

    status = main(
        [
            "scan",
            "--repository",
            str(course_repository),
            "--output",
            str(output),
        ]
    )

    assert status == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["repository_name"] == "example-training"
    assert payload["schema_version"] == 1


def test_scan_cli_preserves_inventory_when_one_notebook_is_invalid(
    course_repository: Path,
    tmp_path: Path,
) -> None:
    invalid = course_repository / "notebooks" / "invalid.ipynb"
    shutil.copyfile(FIXTURES / "invalid.ipynb", invalid)
    run_git(course_repository, "add", str(invalid.relative_to(course_repository)))
    output = tmp_path / "inventory.json"

    status = main(
        [
            "scan",
            "--repository",
            str(course_repository),
            "--output",
            str(output),
        ]
    )

    assert status == 1
    payload = json.loads(output.read_text(encoding="utf-8"))
    assert len(payload["notebooks"]) == 2
    assert payload["findings"] == ["notebook_parse_error:notebooks/invalid.ipynb"]


def test_validate_manifest_cli_reports_missing_manifest(
    course_repository: Path,
    capsys,
) -> None:
    status = main(
        ["validate-manifest", "--repository", str(course_repository), "--json"]
    )

    assert status == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["code"] == "manifest_missing"


def test_resolve_manifest_cli_writes_effective_json(
    course_repository: Path,
    tmp_path: Path,
) -> None:
    manifest = course_repository / "validation" / "manifest.toml"
    manifest.parent.mkdir()
    manifest.write_text(
        """
schema_version = 1
repository_id = "example-training"

[defaults]
role = "tutorial"

[[notebooks]]
id = "tutorial"
path = "notebooks/tutorial.ipynb"

[notebooks.properties]
output_policy = "preserve_source"
""".lstrip(),
        encoding="utf-8",
    )
    output = tmp_path / "resolution.json"

    status = main(
        [
            "resolve-manifest",
            "--repository",
            str(course_repository),
            "--output",
            str(output),
        ]
    )

    assert status == 0
    payload = json.loads(output.read_text(encoding="utf-8"))
    tutorial = payload["notebooks"][0]
    assert tutorial["properties"]["role"] == "tutorial"
    assert tutorial["provenance"]["role"] == "repository_default"
    assert tutorial["review_state"] == "unreviewed"


def test_resolve_manifest_cli_distinguishes_validation_failure(
    course_repository: Path,
    capsys,
) -> None:
    manifest = course_repository / "validation" / "manifest.toml"
    manifest.parent.mkdir()
    manifest.write_text(
        'schema_version = 1\nrepository_id = "wrong-training"\n',
        encoding="utf-8",
    )

    status = main(["resolve-manifest", "--repository", str(course_repository)])

    captured = capsys.readouterr()
    assert status == 1
    assert captured.out == ""
    assert "repository_id_mismatch" in captured.err


def test_non_repository_is_an_actionable_error(tmp_path: Path, capsys) -> None:
    status = main(["scan", "--repository", str(tmp_path)])

    assert status == 2
    assert "error:" in capsys.readouterr().err
