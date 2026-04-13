"""Tests for file-based parsing functionality."""

import tempfile
import pytest
from pathlib import Path
from diffstat.core import parse_diff_file
from diffstat.models import DiffstatError


class TestParseFile:
    """File-based parsing tests."""

    def test_parse_diff_file_basic(self) -> None:
        """Parse a diff from a file."""
        diff_content = """--- a/file.py
+++ b/file.py
@@ -1 +1,2 @@
 x = 1
+y = 2
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write(diff_content)
            f.flush()
            path = f.name

        try:
            result = parse_diff_file(path)
            assert result.total_files == 1
            assert result.files[0].path == "file.py"
            assert result.files[0].additions == 1
        finally:
            Path(path).unlink()

    def test_parse_diff_file_not_found(self) -> None:
        """File not found raises DiffstatError."""
        with pytest.raises(DiffstatError):
            parse_diff_file("/nonexistent/path/to/file.diff")

    def test_parse_diff_file_empty_file(self) -> None:
        """Parse empty diff file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write("")
            f.flush()
            path = f.name

        try:
            result = parse_diff_file(path)
            assert result.total_files == 0
        finally:
            Path(path).unlink()

    def test_parse_diff_file_multiple_files(self) -> None:
        """Parse file with multiple file diffs."""
        diff_content = """--- a/file1.py
+++ b/file1.py
@@ -1 +1,2 @@
#x
+y
--- a/file2.py
+++ b/file2.py
@@ -1,2 +0,0 @@
-a
-b
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write(diff_content)
            f.flush()
            path = f.name

        try:
            result = parse_diff_file(path)
            assert result.total_files == 2
        finally:
            Path(path).unlink()

    def test_parse_diff_file_with_binary(self) -> None:
        """Parse file containing binary diffs."""
        diff_content = """Binary files a/img.png and b/img.png differ
--- a/text.py
+++ b/text.py
@@ -1 +1 @@
-old
+new
"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write(diff_content)
            f.flush()
            path = f.name

        try:
            result = parse_diff_file(path)
            assert result.total_files == 2
            assert result.files[0].is_binary is True
            assert result.files[1].is_binary is False
        finally:
            Path(path).unlink()

    def test_parse_diff_file_preserves_content(self) -> None:
        """File and string parsing produce same results."""
        diff_content = """--- a/main.py
+++ b/main.py
@@ -1,3 +1,4 @@
 def main():
     pass
+    return True
 # end
"""
        # Parse from string
        from diffstat.core import parse_diff

        result_str = parse_diff(diff_content)

        # Parse from file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write(diff_content)
            f.flush()
            path = f.name

        try:
            result_file = parse_diff_file(path)
            assert result_str.total_files == result_file.total_files
            assert result_str.total_additions == result_file.total_additions
            assert result_str.total_deletions == result_file.total_deletions
        finally:
            Path(path).unlink()

    def test_parse_diff_file_with_special_chars(self) -> None:
        """Parse file with special characters in content."""
        diff_content = """--- a/file.py
+++ b/file.py
@@ -1 +1,2 @@
 x = "hello"
+y = "Ã©Ã Ã·"
"""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".diff", delete=False, encoding="utf-8"
        ) as f:
            f.write(diff_content)
            f.flush()
            path = f.name

        try:
            result = parse_diff_file(path)
            assert result.total_files == 1
        finally:
            Path(path).unlink()

    def test_parse_diff_file_with_large_content(self) -> None:
        """Parse file with large diff."""
        # Create a diff with many hunks
        lines = ["--- a/large.py", "+++ b/large.py"]
        for i in range(0, 100, 10):
            lines.append(f"@@ -{i},10 +{i},11 @@")
            for j in range(10):
                lines.append(f" line {i + j}")
            lines.append("+new line")

        diff_content = "\n".join(lines)

        with tempfile.NamedTemporaryFile(mode="w", suffix=".diff", delete=False) as f:
            f.write(diff_content)
            f.flush()
            path = f.name

        try:
            result = parse_diff_file(path)
            assert result.total_files == 1
            # 10 hunks with 1 addition each
            assert len(result.files[0].hunks) == 10
        finally:
            Path(path).unlink()

    def test_parse_diff_file_invalid_type(self) -> None:
        """Non-string path raises error."""
        with pytest.raises((DiffstatError, TypeError)):
            parse_diff_file(123)  # type: ignore
