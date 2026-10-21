"""Read-only Git operations for repository inventory."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path


class GitError(RuntimeError):
    """Raised when required Git evidence cannot be collected."""


@dataclass(frozen=True)
class GitRepository:
    """A validated local Git repository."""

    root: Path

    @classmethod
    def discover(cls, path: Path) -> GitRepository:
        candidate = path.expanduser().resolve()
        if not candidate.exists():
            raise GitError(f"repository path does not exist: {candidate}")
        result = _run_git(candidate, "rev-parse", "--show-toplevel")
        root = Path(result.stdout.strip()).resolve()
        return cls(root=root)

    def text(self, *arguments: str, check: bool = True) -> str:
        return _run_git(self.root, *arguments, check=check).stdout

    def nul_paths(self, *arguments: str) -> tuple[str, ...]:
        output = self.text(*arguments)
        return tuple(sorted(path for path in output.split("\0") if path))

    def branch(self) -> str | None:
        result = _run_git(
            self.root,
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
            check=False,
        )
        value = result.stdout.strip()
        return value or None

    def commit(self) -> str:
        return self.text("rev-parse", "HEAD").strip()

    def dirty(self) -> bool:
        return bool(self.text("status", "--porcelain=v1", "--untracked-files=all"))

    def tracked_notebooks(self) -> tuple[str, ...]:
        return self.nul_paths("ls-files", "-z", "--", "*.ipynb")

    def untracked_notebooks(self) -> tuple[str, ...]:
        return self.nul_paths(
            "ls-files", "--others", "--exclude-standard", "-z", "--", "*.ipynb"
        )

    def ignored_notebooks(self) -> tuple[str, ...]:
        return self.nul_paths(
            "ls-files",
            "--others",
            "--ignored",
            "--exclude-standard",
            "-z",
            "--",
            "*.ipynb",
        )

    def blob_id(self, relative_path: str) -> str:
        path = self.safe_path(relative_path)
        return self.text("hash-object", str(path)).strip()

    def last_changed_commit(self, relative_path: str) -> str | None:
        value = self.text(
            "log", "-1", "--format=%H", "--", relative_path, check=False
        ).strip()
        return value or None

    def safe_path(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if candidate != self.root and self.root not in candidate.parents:
            raise GitError(f"path escapes repository root: {relative_path}")
        return candidate


def _run_git(
    working_directory: Path,
    *arguments: str,
    check: bool = True,
) -> subprocess.CompletedProcess[str]:
    try:
        result = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(working_directory), *arguments],
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as error:
        raise GitError(f"unable to run Git: {error}") from error

    if check and result.returncode != 0:
        detail = result.stderr.strip() or result.stdout.strip() or "unknown Git error"
        raise GitError(detail)
    return result
