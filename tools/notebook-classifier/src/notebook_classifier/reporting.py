"""Render validated notebook evidence without strengthening its claims."""

from __future__ import annotations

from notebook_classifier.results import ResultAssessment


def render_validation_markdown(assessment: ResultAssessment) -> str:
    """Render a compact, deterministic Markdown evidence report."""

    report = assessment.to_dict()
    repository = report.get("repository") or {}
    counts = report["counts"]
    outcomes = counts["effective_outcomes"]
    lines = [
        "# Notebook validation evidence summary",
        "",
        "**Evidence validity:** "
        f"{'valid and complete' if report['complete'] else 'incomplete or invalid'}",
        "",
        "**Selected checks:** "
        f"{'all passed' if report['successful'] else 'non-passing outcomes present'}",
        "",
        f"> {report['evidence_boundary']}",
        "",
        "## Provenance",
        "",
        f"- Repository: `{repository.get('id', 'unknown')}`",
        f"- Commit: `{repository.get('commit', 'unknown')}`",
        f"- Platform: `{repository.get('platform', 'unknown')}`",
        f"- Plan digest: `{report.get('plan_digest') or 'unknown'}`",
        "",
        "## Outcomes",
        "",
        "| Outcome | Count |",
        "|---|---:|",
    ]
    for outcome in ("pass", "fail", "error", "not_run"):
        lines.append(f"| `{outcome}` | {outcomes.get(outcome, 0)} |")
    lines.extend(
        [
            "",
            "Total recorded duration: "
            f"{report['metrics']['total_duration_seconds']:.3f} s",
            "",
            "`exception_count` counts runner entries and individual checks reported "
            f"as `error`: {report['metrics']['exception_count']}.",
            "",
            "## Environments",
            "",
            "| Environment | Candidates | Reported | Pass | Fail | Error | "
            "Not run | Duration (s) |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )
    for environment in report["environments"]:
        env_outcomes = environment["outcomes"]
        lines.append(
            "| {environment} | {planned_candidates} | {reported} | {pass_count} | "
            "{fail_count} | {error_count} | {not_run_count} | {duration:.3f} |".format(
                environment=environment["environment"],
                planned_candidates=environment["planned_candidates"],
                reported=environment["reported"],
                pass_count=env_outcomes["pass"],
                fail_count=env_outcomes["fail"],
                error_count=env_outcomes["error"],
                not_run_count=env_outcomes["not_run"],
                duration=environment["duration_seconds"],
            )
        )

    lines.extend(
        [
            "",
            "## Entry accounting",
            "",
            "| Notebook | Action | Reported outcome | Effective outcome | "
            "Environment |",
            "|---|---|---|---|---|",
        ]
    )
    for entry in report["entries"]:
        identifier = entry["notebook_id"] or entry["path"]
        reported = entry["reported_outcome"] or "missing"
        lines.append(
            f"| `{identifier}` | `{entry['planned_action']}` | `{reported}` | "
            f"`{entry['effective_outcome']}` | `{entry['environment']}` |"
        )

    lines.extend(["", "## Diagnostics", ""])
    if not report["diagnostics"]:
        lines.append("No validation or provenance diagnostics.")
    else:
        for diagnostic in report["diagnostics"]:
            location = diagnostic["notebook_id"] or diagnostic["path"]
            suffix = f" (`{location}`)" if location else ""
            lines.append(
                f"- **{diagnostic['level']} / `{diagnostic['code']}`**{suffix}: "
                f"{diagnostic['message']}"
            )
    lines.append("")
    return "\n".join(lines)
