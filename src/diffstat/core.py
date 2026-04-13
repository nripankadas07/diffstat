"""Core diff parsing functionality."""

import re
from pathlib import Path
from diffstat.models import (
    DiffResult,
    DiffstatError,
    FileStat,
    HunkStat,
)


def parse_diff(text: str) -> DiffResult:
    """
    Parse a unified diff string and compute statistics.

    Args:
        text: Unified diff content as a string.

    Returns:
        DiffResult with file statistics.

    Raises:
        DiffstatError: If input is not a string.
    """
    if not isinstance(text, str):
        raise DiffstatError(
            f"Expected string input, got {type(text).__name__}"
        )

    result = DiffResult()
    if not text.strip():
        return result

    lines = text.splitlines()
    i = 0
    while i < len(lines):
        i = _process_diff_line(lines, i, result)

    return result


def parse_diff_file(path: str) -> DiffResult:
    """
    Parse a unified diff from a file.

    Args:
        path: Path to diff file.

    Returns:
        DiffResult with file statistics.

    Raises:
        DiffstatError: If file not found or cannot be read.
    """
    try:
        content = Path(path).read_text(encoding="utf-8")
        return parse_diff(content)
    except FileNotFoundError as e:
        raise DiffstatError(f"File not found: {path}") from e
    except UnicodeDecodeError as e:
        raise DiffstatError(f"Cannot read file as text: {path}") from e
    except Exception as e:
        raise DiffstatError(f"Error reading file: {path}: {e}") from e


def _process_diff_line(lines: list[str], index: int, result: DiffResult) -> int:
    """Process a single line in diff, return next index to process."""
    line = lines[index]

    # Check for binary file marker
    if line.startswith("Binary files"):
        file_stat = _parse_binary_file(line)
        if file_stat:
            result.files.append(file_stat)
        return index + 1

    # Check for file header (--- line)
    if line.startswith("--- "):
        return _process_file_header(lines, index, result)

    return index + 1


def _process_file_header(lines: list[str], index: int, result: DiffResult) -> int:
    """Process a file header starting with ---. Return next index."""
    old_path = _extract_path(lines[index][4:])
    index += 1

    # Look for +++ line
    if index >= len(lines) or not lines[index].startswith("+++ "):
        return index

    new_path = _extract_path(lines[index][4:])
    index += 1

    # Determine file status
    is_new = old_path == "/dev/null"
    is_deleted = new_path == "/dev/null"
    path = new_path if not is_deleted else old_path

    file_stat = FileStat(path=path, is_new=is_new, is_deleted=is_deleted)

    # Parse optional metadata lines
    index = _parse_file_metadata(lines, index, file_stat)

    # Parse hunks
    index = _parse_hunks(lines, index, file_stat)

    result.files.append(file_stat)
    return index


def _extract_path(path_str: str) -> str:
    """Extract file path from diff header, handling a/ and b/ prefixes."""
    path_str = path_str.strip()
    # Remove a/ or b/ prefix if present
    if path_str.startswith(("a/", "b/")):
        path_str = path_str[2:]
    return path_str


def _parse_binary_file(line: str) -> FileStat | None:
    """
    Parse a binary file diff line.

    Example: Binary files a/img.png and b/img.png differ
    """
    # Extract file path
    match = re.match(r"Binary files a/(.+) and b/", line)
    if match:
        path = match.group(1)
        return FileStat(path=path, is_binary=True)
    return None


def _parse_file_metadata(
    lines: list[str], start: int, file_stat: FileStat
) -> int:
    """Parse file metadata (rename, similarity, etc.) and return next index."""
    i = start
    while i < len(lines):
        line = lines[i]
        if _process_metadata_line(line, file_stat):
            i += 1
        else:
            return i
    return i


def _process_metadata_line(line: str, file_stat: FileStat) -> bool:
    """Process one metadata line. Return True if consumed, False if done."""
    if line.startswith("rename from "):
        file_stat.is_renamed = True
        file_stat.old_path = line[12:].strip()
        return True
    elif line.startswith("rename to "):
        file_stat.path = line[10:].strip()
        return True
    elif line.startswith("similarity index") or line.startswith("index "):
        # Skip metadata
        return True
    elif line.startswith(("--- ", "+++ ", "@@")):
        # Start of next file or hunks
        return False
    elif line.startswith((" ", "-", "+", "\\")):
        # Content line, still metadata section
        return True
    else:
        # Unknown line, end metadata
        return False


def _parse_hunks(lines: list[str], start: int, file_stat: FileStat) -> int:
    """Parse hunks and return next line index (next file or end)."""
    i = start
    while i < len(lines):
        line = lines[i]

        # Check for hunk header
        if line.startswith("@@"):
            hunk = _parse_hunk_header(line)
            if hunk:
                file_stat.hunks.append(hunk)
                i += 1

                # Parse hunk lines
                i = _parse_hunk_lines(lines, i, hunk, file_stat)
            else:
                i += 1
            continue

        # Check if we've hit the next file
        if line.startswith("--- "):
            return i
        if line.startswith("Binary files"):
            return i

        i += 1

    return i


def _parse_hunk_header(header: str) -> HunkStat | None:
    """Parse hunk header and extract line numbers."""
    # Format: @@ -old_start,old_count +new_start,new_count @@
    match = re.match(r"@@ -(d+)(?:,(d+))?\s+(d+)(?:,(d+))? @@", header)
    if not match:
        return None

    old_start = int(match.group(1))
    old_count = int(match.group(2)) if match.group(2) else 1
    new_start = int(match.group(3))
    new_count = int(match.group(4)) if match.group(4) else 1

    return HunkStat(
        old_start=old_start,
        old_count=old_count,
        new_start=new_start,
        new_count=new_count,
        additions=0,
        deletions=0,
        context_lines=0,
    )


def _parse_hunk_lines(
    lines: list[str],
    start: int,
    hunk: HunkStat,
    file_stat: FileStat,
) -> int:
    """Parse lines within a hunk and return next line index."""
    i = start
    while i < len(lines):
        line = lines[i]

        # Check boundaries
        if _is_diff_boundary(line):
            return i

        # Count line changes
        _count_hunk_line(line, hunk, file_stat)
        i += 1

    return i


def _is_diff_boundary(line: str) -> bool:
    """Check if line is a diff boundary (next hunk or file)."""
    return (
        line.startswith("@@")
        or line.startswith("--- ")
        or line.startswith("Binary files")
    )


def _count_hunk_line(line: str, hunk: HunkStat, file_stat: FileStat) -> None:
    """Count changes in a single hunk line."""
    if line.startswith("+") and not line.startswith("+++"):
        hunk.additions += 1
        file_stat.additions += 1
    elif line.startswith("-") and not line.startswith("---"):
        hunk.deletions += 1
        file_stat.deletions += 1
    elif line.startswith(" "):
        hunk.context_lines += 1
