from __future__ import annotations

import json
import shutil
from pathlib import Path

from conftest import run_git

from notebook_classifier.scanner import scan_repository

FIXTURES = Path(__file__).parent / "fixtures"


def test_scan_collects_git_and_repository_evidence(course_repository: Path) -> None:
    inventory = scan_repository(course_repository)

    assert inventory.repository_name == "example-training"
    assert inventory.branch == "main"
    assert inventory.dirty is True
    assert inventory.tracked_notebook_count == 1
    assert inventory.untracked_notebooks == ("notebooks/exercise.ipynb",)
    assert inventory.ignored_notebooks == (
        "notebooks/.ipynb_checkpoints/tutorial.ipynb",
    )
    assert inventory.pixi_environments == ("default", "optional")
    assert inventory.pixi_tasks == ("lab", "optional:prepare")
    assert inventory.environment_files == ("pixi.toml",)
    assert inventory.training_id == "example-training"
    assert inventory.training_material_paths == ("notebooks",)
    assert inventory.notebooks[0].path == "notebooks/tutorial.ipynb"
    assert inventory.findings == ()


def test_scan_output_is_deterministic_at_same_state(course_repository: Path) -> None:
    first = scan_repository(course_repository).to_dict()
    second = scan_repository(course_repository).to_dict()

    assert json.dumps(first, sort_keys=True) == json.dumps(second, sort_keys=True)


def test_scan_reports_invalid_tracked_notebook(course_repository: Path) -> None:
    invalid = course_repository / "notebooks" / "invalid.ipynb"
    shutil.copyfile(FIXTURES / "invalid.ipynb", invalid)
    run_git(course_repository, "add", str(invalid.relative_to(course_repository)))

    inventory = scan_repository(course_repository)

    assert inventory.findings == ("notebook_parse_error:notebooks/invalid.ipynb",)
    assert inventory.notebooks[0].parse_error is not None
