from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def run_git(repository: Path, *arguments: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repository), *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout


@pytest.fixture
def course_repository(tmp_path: Path) -> Path:
    repository = tmp_path / "example-training"
    repository.mkdir()
    run_git(repository, "init", "-b", "main")

    notebooks = repository / "notebooks"
    notebooks.mkdir()
    shutil.copyfile(FIXTURES / "tutorial.ipynb", notebooks / "tutorial.ipynb")
    (repository / "pixi.toml").write_text(
        """
[workspace]
channels = ["conda-forge"]
platforms = ["linux-64"]

[tasks]
lab = "jupyter lab notebooks"

[feature.optional.tasks]
prepare = "python prepare.py"

[environments]
default = []
optional = []
""".lstrip(),
        encoding="utf-8",
    )
    (repository / "training.toml").write_text(
        """
schema_version = 2
id = "example-training"

[[materials]]
kind = "source-code"
path = "notebooks"
""".lstrip(),
        encoding="utf-8",
    )
    (repository / ".gitignore").write_text(".ipynb_checkpoints/\n", encoding="utf-8")
    run_git(repository, "add", ".")
    run_git(
        repository,
        "-c",
        "user.name=Notebook Classifier Tests",
        "-c",
        "user.email=notebook-classifier@example.invalid",
        "commit",
        "-m",
        "Add fixture course",
    )

    shutil.copyfile(FIXTURES / "exercise.ipynb", notebooks / "exercise.ipynb")
    checkpoint = notebooks / ".ipynb_checkpoints"
    checkpoint.mkdir()
    shutil.copyfile(FIXTURES / "tutorial.ipynb", checkpoint / "tutorial.ipynb")
    return repository
