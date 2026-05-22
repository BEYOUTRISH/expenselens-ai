from typing import Any


def generate_report(
    original_rows: int,
    cleaned_rows: list[dict],
    issues: list[dict],
) -> dict:
    rows_loaded = len(cleaned_rows)
    rows_excluded = original_rows - rows_loaded

    severity_counts: dict[str, int] = {"CRITICAL": 0, "WARNING": 0, "INFO": 0}
    for issue in issues:
        sev = issue.get("severity", "INFO")
        if sev in severity_counts:
            severity_counts[sev] += 1

    report = {
        "total_rows_in_source": original_rows,
        "rows_loaded": rows_loaded,
        "rows_excluded": rows_excluded,
        "issues": issues,
        "summary": severity_counts,
    }

    return report
