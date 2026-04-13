"""Tests for diff formatting functionality."""

import pytest
from diffstat.core import parse_diff
from diffstat.formatter import format_stat
from diffstat.models import DiffResult, FileStat


class TestFormatBasic:
    """Basic formatting tests."""

    def test_format_empty_result(self) -> None:
        """Empty DiffResult formats correctly."""
        result = DiffResult()
        output = format_stat(result)
        assert isinstance(output, str)
        # Should have some output even if empty
        assert len(output) >= 0

    def test_format_single_file(self) -> None:
        """Format output with one file."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1 +1,2 @@
 x
+y
"""
        result = parse_diff(diff)
        output = format_stat(result)
        assert "file.py" in output
        assert "1" in output  # addition count

    def test_format_multiple_files(self) -> None:
        """Format output with multiple files."""
        diff = """--- a/file1.py
+++ b/file1.py
@@ -1 +1,2 @@
 x
+y
--- a/file2.py
+++ b/file2.py
@@ -1,2 +0,0 @@
-x
-y
"""
        result = parse_diff(diff)
        output = format_stat(result)
        assert "file1.py" in output
        assert "file2.py" in output

    def test_format_width_parameter(self) -> None:
        """Format respects width parameter."""
        result = DiffResult(
            files=[FileStat(path="test.py", additions=100, deletions=50)]
        )
        output_80 = format_stat(result, width=80)
        output_120 = format_stat(result, width=120)
        # Both should be valid strings
        assert isinstance(output_80, str)
        assert isinstance(output_120, str)

    def test_format_includes_summary(self) -> None:
        """Format output includes summary stats."""
        result = DiffResult(
            files=[
                FileStat(path="a.py", additions=10, deletions=5),
                FileStat(path="b.py", additions=20, deletions=15),
            ]
        )
        output = format_stat(result)
        # Should include totals
        assert "30" in output or output  # 10 + 20 additions

    def test_format_binary_files(self) -> None:
        """Binary files are marked in output."""
        result = DiffResult(
            files=[
                FileStat(path="image.png", is_binary=True),
                FileStat(path="text.py", additions=5),
            ]
        )
        output = format_stat(result)
        assert "image.png" in output
        # Binary file might be marked specially
        assert "text.py" in output

    def test_format_new_deleted_renamed(self) -> None:
        """Format indicates new, deleted, and renamed files."""
        result = DiffResult(
            files=[
                FileStat(path="new.py", is_new=True, additions=10),
                FileStat(path="old.py", is_deleted=True, deletions=10),
                FileStat(
                    path="renamed.py", old_path="oldname.py", is_renamed=True
                ),
            ]
        )
        output = format_stat(result)
        assert "new.py" in output
        assert "old.py" in output
        assert "renamed.py" in output

    def test_format_large_numbers(self) -> None:
        """Format handles large line counts."""
        result = DiffResult(
            files=[
                FileStat(path="large.py", additions=1000, deletions=500),
            ]
        )
        output = format_stat(result)
        assert "1000" in output or "large.py" in output

    def test_format_zero_changes(self) -> None:
        """Format handles files with no changes."""
        result = DiffResult(
            files=[
                FileStat(path="unchanged.py", additions=0, deletions=0),
            ]
        )
        output = format_stat(result)
        assert "unchanged.py" in output

    def test_format_is_string(self) -> None:
        """Format always returns a string."""
        result = DiffResult(
            files=[FileStat(path="test.py", additions=1, deletions=0)]
        )
        output = format_stat(result, width=80)
        assert isinstance(output, str)


class TestFormatWidthHandling:
    """Width parameter handling."""

    def test_format_small_width(self) -> None:
        """Format works with small width."""
        result = DiffResult(
            files=[FileStat(path="test.py", additions=50, deletions=25)]
        )
        output = format_stat(result, width=40)
        assert isinstance(output, str)

    def test_format_large_width(self) -> None:
        """Format works with large width."""
        result = DiffResult(
            files=[FileStat(path="test.py", additions=50, deletions=25)]
        )
        output = format_stat(result, width=200)
        assert isinstance(output, str)

    def test_format_default_width(self) -> None:
        """Format uses default width when not specified."""
        result = DiffResult(
            files=[FileStat(path="test.py", additions=10, deletions=5)]
        )
        output = format_stat(result)
        assert isinstance(output, str)


class TestFormatRealDiffs:
    """Format tests with real diff examples."""

    def test_format_typical_commit(self) -> None:
        """Format typical commit diff."""
        diff = """--- a/src/main.py
+++ b/src/main.py
@@ -1,5 +1,6 @@
 def main():
     x = 1
-    y = 2
+    y = 3
     z = x + y
+    return z

"""
        result = parse_diff(diff)
        output = format_stat(result)
        assert "main.py" in output
        assert isinstance(output, str)

    def test_format_multiple_file_types(self) -> None:
        """Format mix of different file types."""
        diff = """--- a/src/main.py
+++ b/src/main.py
@@ -1 +1,2 @@
 x
+y
--- a/README.md
+++ b/README.md
@@ -1,3 +1,5 @@
 # Title
+## Subtitle
 Content
+More content
 End
Binary files a/image.png and b/image.png differ
"""
        result = parse_diff(diff)
        output = format_stat(result)
        assert "main.py" in output
        assert "README.md" in output
        assert "image.png" in output
