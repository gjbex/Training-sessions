"""Transparent, deterministic notebook classification suggestions."""

from __future__ import annotations

from dataclasses import dataclass

from notebook_classifier.models import NotebookInventory, RepositoryInventory


@dataclass(frozen=True)
class Suggestion:
    """One unconfirmed value proposal and the static evidence behind it."""

    property_name: str
    value: str | tuple[str, ...]
    confidence: str
    evidence: tuple[str, ...]


def suggest_notebook(
    notebook: NotebookInventory,
    repository: RepositoryInventory,
) -> tuple[Suggestion, ...]:
    """Return conservative suggestions without changing effective values."""

    if notebook.parse_error is not None:
        return (
            Suggestion(
                "validation_tier",
                "manual",
                "high",
                ("Notebook could not be parsed or validated statically.",),
            ),
        )

    suggestions: list[Suggestion] = []
    heading_text = " ".join(notebook.headings).casefold()
    if "exercise" in heading_text or "assignment" in heading_text:
        suggestions.append(
            Suggestion(
                "role",
                "exercise",
                "high",
                ("A Markdown heading contains 'exercise' or 'assignment'.",),
            )
        )
    elif notebook.markdown_cells and notebook.code_cells:
        suggestions.append(
            Suggestion(
                "role",
                "tutorial",
                "medium",
                (
                    f"Notebook mixes {notebook.markdown_cells} Markdown and "
                    f"{notebook.code_cells} code cells.",
                ),
            )
        )
    elif notebook.code_cells:
        suggestions.append(
            Suggestion(
                "role",
                "exploration",
                "low",
                ("Notebook has code cells but no Markdown cells.",),
            )
        )

    if notebook.stored_errors:
        suggestions.append(
            Suggestion(
                "output_policy",
                "declared_errors",
                "medium",
                (
                    f"Notebook contains {len(notebook.stored_errors)} stored "
                    "error output(s); confirm they are instructional.",
                ),
            )
        )
    elif notebook.output_count:
        suggestions.append(
            Suggestion(
                "output_policy",
                "preserve_source",
                "low",
                (f"Notebook contains {notebook.output_count} stored output(s).",),
            )
        )
    elif notebook.code_cells and notebook.unexecuted_code_cells == notebook.code_cells:
        suggestions.append(
            Suggestion(
                "output_policy",
                "empty_expected",
                "medium",
                ("All code cells are unexecuted and no outputs are stored.",),
            )
        )

    signal_cells = {signal.name: signal.cell_indices for signal in notebook.signals}
    constraints: list[str] = []
    for signal, constraint in (
        ("interactive", "manual_interaction"),
        ("network", "network"),
        ("gpu", "gpu"),
        ("hpc", "hpc"),
    ):
        if signal in signal_cells:
            constraints.append(constraint)
    if constraints:
        evidence = tuple(
            f"{signal} signal in cell(s) "
            + ", ".join(str(index + 1) for index in signal_cells[signal])
            for signal in ("interactive", "network", "gpu", "hpc")
            if signal in signal_cells
        )
        suggestions.extend(
            (
                Suggestion("constraints", tuple(constraints), "high", evidence),
                Suggestion(
                    "validation_tier",
                    "manual",
                    "medium",
                    ("Static signals indicate external or interactive requirements.",),
                ),
            )
        )
    elif notebook.shell_escapes:
        suggestions.append(
            Suggestion(
                "validation_tier",
                "manual",
                "medium",
                ("Notebook contains shell escapes, which require manual review.",),
            )
        )
    else:
        suggestions.append(
            Suggestion(
                "validation_tier",
                "required",
                "low",
                ("No known external or interactive requirement was detected.",),
            )
        )

    if "default" in repository.pixi_environments and not constraints:
        suggestions.append(
            Suggestion(
                "environment",
                "default",
                "low",
                ("Repository declares a Pixi environment named 'default'.",),
            )
        )
    return tuple(suggestions)


def suggestion_map(
    notebook: NotebookInventory,
    repository: RepositoryInventory,
) -> dict[str, Suggestion]:
    """Index suggestions by property for display and explicit application."""

    return {
        suggestion.property_name: suggestion
        for suggestion in suggest_notebook(notebook, repository)
    }
