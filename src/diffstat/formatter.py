"""Formatting utilities for diff statistics."""

from diffstat.models import DiffResult


def format_stat(result: DiffResult, width: int = 80) -> str:
    """
    Format diff statistics as a human-readable string (like git diff --stat).

    Args:
        result: DiffResult to format.
        width: Terminal width for output (default 80).

    Returns:
        Formatted statistics as a multi-line string.
    """
    if not result.files:
        return ""

    lines = _format_file_lines(result, width)
    summary = _format_summary(result)
    lines.append(summary)

    return "\n".join(lines)


def _format_file_lines(result: DiffResult, width: int) -> list[str]:
    """Format individual file stat lines."""
    lines = []
    max_path_len = _calc_max_path_len(result, width)

    for file_stat in result.files:
        filename = _format_filename(file_stat)
        stat_str = _format_stat_str(file_stat, filename, width)
        line = filename.ljust(max_path_len) + " | " + stat_str
        lines.append(line)

    return lines


def _calc_max_path_len(result: DiffResult, width: int) -> int:
    """Calculate maximum file path length for alignment."""
    max_len = max(len(_format_filename(f)) for f in result.files)
    return min(max_len, width // 2)


def _format_stat_str(file_stat, filename: str, width: int) -> str:  # type: ignore
    """Format stat string for one file (binary marker or bar chart)."""
    if file_stat.is_binary:
        return "Bin"

    changes = file_stat.additions + file_stat.deletions
    if changes == 0:
        return ""

    total = changes
    bar_width = max(1, width - len(filename) - 20)
    add_chars = int((file_stat.additions / total) * bar_width)
    del_chars = int((file_stat.deletions / total) * bar_width)

    bar = "+" * add_chars + "-" * del_chars
    return bar + f" {file_stat.additions}+{file_stat.deletions}"


def _format_summary(result: DiffResult) -> str:
    """Format summary line with totals."""
    files_word = "file" if result.total_files == 1 else "files"
    return (
        f"{result.total_files} {files_word} changed, "
        f"{result.total_additions} insertions(+), "
        f"{result.total_deletions} deletions(-)"
    )


def _format_filename(file_stat) -> str:  # type: ignore
    """Format filename with status indicators."""
    name = file_stat.path

    if file_stat.is_binary:
        return f"{name} (binary)"
    elif file_stat.is_new:
        return f"{name} (new)"
    elif file_stat.is_deleted:
        return f"{name} (deleted)"
    elif file_stat.is_renamed:
        return f"{file_stat.old_path} => {name}"

    return name
