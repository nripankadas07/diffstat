# diffstat

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Compute unified diff statistics: additions, deletions, and file changes** â a zero-dependency Python library for parsing and analyzing unified diff format.

## Installation

```bash
pip install diffstat
```

## Usage

### Basic Example

Parse a diff string and get statistics:

```python
from diffstat import parse_diff, format_stat

diff = """--- a/hello.py
+++ b/hello.py
@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
+    return True
"""

result = parse_diff(diff)
print(f"Files changed: {result.total_files}")
print(f"Additions: {result.total_additions}")
print(f"Deletions: {result.total_deletions}")

# Format as human-readable output (like `git diff --stat`)
print(format_stat(result))
```

### Parse from File

```python
from diffstat import parse_diff_file, format_stat

result = parse_diff_file("my_changes.patch")
print(format_stat(result))
```

### Access Detailed File Statistics

```python
from diffstat import parse_diff

result = parse_diff(diff_string)

for file_stat in result.files:
    print(f"File: {file_stat.path}")
    print(f"  Additions: {file_stat.additions}")
    print(f"  Deletions: {file_stat.deletions}")
    print(f"  New: {file_stat.is_new}")
    print(f"  Deleted: {file_stat.is_deleted}")
    print(f"  Renamed: {file_stat.is_renamed}")
    print(f"  Binary: {file_stat.is_binary}")
    print(f"  Hunks: {len(file_stat.hunks)}")
```

## API Reference

### Core Functions

#### `parse_diff(text: str) -> DiffResult`

Parse a unified diff string and compute statistics.

**Arguments:**
- `text` (str): Unified diff content

**Returns:**
- `DiffResult`: Statistics for the diff

**Raises:**
- `DiffstatError`: If input is not a string

**Example:**
```python
result = parse_diff("--- a/file\n+++ b/file\n@@ -1 +1 @@\n-old\n+new")
```

#### `parse_diff_file(path: str) -> DiffResult`

Parse a unified diff from a file path.

**Arguments:**
- `path` (str): Path to diff file

**Returns:**
- `DiffResult`: Statistics for the diff

**Raises:**
- `DiffstatError`: If file not found or cannot be read

**Example:**
```python
result = parse_diff_file("changes.patch")
```

#### `format_stat(result: DiffResult, width: int = 80) -> str`

Format diff statistics as a human-readable string (similar to `git diff --stat`).

**Arguments:**
- `result` (DiffResult): Diff statistics to format
- `width` (int, optional): Terminal width for output (default: 80)

**Returns:**
- str: Formatted statistics

**Example:**
```python
output = format_stat(result, width=100)
print(output)
```

### Data Classes

#### `DiffResult`

Statistics for a complete diff.

**Attributes:**
- `files` (list[FileStat]): List of file statistics
- `total_additions` (int, property): Total lines added across all files
- `total_deletions` (int, property): Total lines deleted across all files
- `total_files` (int, property): Total number of files changed

#### `FileStat`

Statistics for a single file in a diff.

**Attributes:**
- `path` (str): File path
- `old_path` (str | None): Original path (for renamed files)
- `additions` (int): Number of lines added
- `deletions` (int): Number of lines deleted
- `is_binary` (bool): Whether file is binary
- `is_new` (bool): Whether file is newly created
- `is_deleted` (bool): Whether file is deleted
- `is_renamed` (bool): Whether file is renamed
- `hunks` (list[HunkStat]): List of hunk statistics

#### `HunkStat`

Statistics for a single hunk (contiguous block of changes) in a diff.

**Attributes:**
- `old_start` (int): Starting line number in original file
- `old_count` (int): Number of lines in original file's hunk
- `new_start` (int): Starting line number in new file
- `new_count` (int): Number of lines in new file's hunk
- `additions` (int): Number of lines added in this hunk
- `deletions` (int): Number of lines deleted in this hunk
- `context_lines` (int): Number of context lines in this hunk

#### `DiffstatError`

Exception raised by diffstat operations.

**Inherits from:** `Exception`

**Usage:**
```python
from diffstat import parse_diff, DiffstatError

try:
    result = parse_diff(some_input)
except DiffstatError as e:
    print(f"Error: {e}")
```

## Features

- **Zero dependencies**: Pure Python, no external libraries required
- **Comprehensive parsing**: Handles unified diff format with all common variations
- **Edge case handling**: Correctly parses binary files, new files, deleted files, and renamed files
- **Type hints**: Full type annotations for IDE support
- **Human-readable output**: Format statistics similar to `git diff --stat`

## Supported Diff Features

- Single and multiple file diffs
- Additions, deletions, and unchanged lines
- Binary file detection
- New files (from `/dev/null`)
- Deleted files (to `/dev/null`)
- Renamed files (with `rename from/to` headers)
- Multiple hunks per file
- Mode changes and other metadata

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=src/diffstat --cov-report=term-missing
```

## License

MIT License â see [LICENSE](LICENSE) for details.

Copyright (c) 2026 Nripanka Das
