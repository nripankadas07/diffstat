"""Tests for core diff parsing functionality."""

import pytest
from diffstat.core import parse_diff
from diffstat.models import DiffResult, DiffstatError


class TestParseBasic:
    """Basic parsing tests."""

    def test_parse_empty_string(self) -> None:
        """Empty diff string returns empty DiffResult."""
        result = parse_diff("")
        assert isinstance(result, DiffResult)
        assert result.files == []
        assert result.total_additions == 0
        assert result.total_deletions == 0
        assert result.total_files == 0

    def test_parse_simple_single_file(self) -> None:
        """Parse a simple diff with one file."""
        diff = """--- a/hello.py
+++ b/hello.py
@@ -1,3 +1,4 @@
 def hello():
-    print("old")
+    print("new")
+    return True
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].path == "hello.py"
        assert result.files[0].additions == 2
        assert result.files[0].deletions == 1

    def test_parse_multiple_files(self) -> None:
        """Parse diff with multiple files."""
        diff = """--- a/file1.py
+++ b/file1.py
@@ -1 +1,2 @@
 x = 1
+y = 2
--- a/file2.py
+++ b/file2.py
@@ -1 +0,0 @@
-old line
"""
        result = parse_diff(diff)
        assert result.total_files == 2
        assert result.files[0].path == "file1.py"
        assert result.files[1].path == "file2.py"

    def test_parse_non_string_input(self) -> None:
        """Non-string input raises DiffstatError."""
        with pytest.raises(DiffstatError):
            parse_diff(123)  # type: ignore

    def test_parse_multiple_hunks_single_file(self) -> None:
        """Parse file with multiple hunks."""
        diff = """--- a/code.py
+++ b/code.py
@@ -1,2 +1,3 @@
 line 1
+new 1
 line 2
@@ -10,2 +11,3 @@
 line 10
+new 2
 line 11
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert len(result.files[0].hunks) == 2
        assert result.files[0].additions == 2
        assert result.files[0].deletions == 0


class TestParseBinary:
    """Binary file handling."""

    def test_parse_binary_file(self) -> None:
        """Binary files are marked as binary."""
        diff = "Binary files a/image.png and b/image.png differ\n"
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].path == "image.png"
        assert result.files[0].is_binary is True
        assert result.files[0].additions == 0
        assert result.files[0].deletions == 0

    def test_parse_multiple_binary_files(self) -> None:
        """Multiple binary files in one diff."""
        diff = """Binary files a/img1.png and b/img1.png differ
Binary files a/img2.jpg and b/img2.jpg differ
"""
        result = parse_diff(diff)
        assert result.total_files == 2
        assert all(f.is_binary for f in result.files)


class TestParseNewDeleted:
    """New and deleted files."""

    def test_parse_new_file(self) -> None:
        """New files (from /dev/null) are marked."""
        diff = """--- /dev/null
+++ b/new_file.py
@@ -0,0 +1,2 @@
+line 1
+line 2
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].is_new is True
        assert result.files[0].additions == 2
        assert result.files[0].deletions == 0
        assert result.files[0].path == "new_file.py"

    def test_parse_deleted_file(self) -> None:
        """Deleted files (to /dev/null) are marked."""
        diff = """--- a/old_file.py
+++ /dev/null
@@ -1,2 +0,0 @@
-line 1
-line 2
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].is_deleted is True
        assert result.files[0].additions == 0
        assert result.files[0].deletions == 2
        assert result.files[0].path == "old_file.py"


class TestParseRenamed:
    """Renamed files."""

    def test_parse_renamed_file(self) -> None:
        """Renamed files with 'rename from' and 'rename to' headers."""
        diff = """--- a/old_name.py
+++ b/new_name.py
rename from old_name.py
rename to new_name.py
@@ -1 +1 @@
 def func():
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].is_renamed is True
        assert result.files[0].old_path == "old_name.py"
        assert result.files[0].path == "new_name.py"

    def test_parse_renamed_with_changes(self) -> None:
        """Renamed file with content changes."""
        diff = """--- a/old_name.py
+++ b/new_name.py
rename from old_name.py
rename to new_name.py
@@ -1,2 +1,3 @@
 def func():
-    old()
+    new()
+    extra()
"""
        result = parse_diff(diff)
        assert result.files[0].is_renamed is True
        assert result.files[0].additions == 2
        assert result.files[0].deletions == 1


class TestParseEdgeCases:
    """Edge cases and malformed input."""

    def test_parse_no_hunks_only_header(self) -> None:
        """File with header but no hunks (mode change only)."""
        diff = """--- a/script.sh
+++ b/script.sh
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].path == "script.sh"
        assert result.files[0].additions == 0
        assert result.files[0].deletions == 0
        assert len(result.files[0].hunks) == 0

    def test_parse_context_lines(self) -> None:
        """Context lines are counted separately."""
        diff = """--- a/file.py
+++ b/file.py
@@ -5,5 +5,6 @@
 context1
 context2
+new line
 context3
 context4
 context5
"""
        result = parse_diff(diff)
        assert result.files[0].hunks[0].context_lines == 5
        assert result.files[0].hunks[0].additions == 1
        assert result.files[0].hunks[0].deletions == 0

    def test_parse_whitespace_only_changes(self) -> None:
        """File with whitespace-only changes."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-x = 1
+x  = 1
"""
        result = parse_diff(diff)
        assert result.files[0].additions == 1
        assert result.files[0].deletions == 1

    def test_parse_file_path_with_spaces(self) -> None:
        """File paths with spaces are parsed correctly."""
        diff = """--- a/my file.py
+++ b/my file.py
@@ -1 +1,2 @@
 content
+more
"""
        result = parse_diff(diff)
        assert result.files[0].path == "my file.py"

    def test_parse_file_path_with_special_chars(self) -> None:
        """File paths with special characters."""
        diff = """--- a/dir/sub-dir/file_name.py
+++ b/dir/sub-dir/file_name.py
@@ -1 +1 @@
-old
+new
"""
        result = parse_diff(diff)
        assert result.files[0].path == "dir/sub-dir/file_name.py"

    def test_parse_large_hunk_counts(self) -> None:
        """Large addition and deletion counts."""
        diff = """--- a/large.py
+++ b/large.py
@@ -1,1000 +1,1500 @@
"""
        # Without actual hunk content, should still parse header
        result = parse_diff(diff)
        assert result.total_files == 1

    def test_parse_mixed_content_types(self) -> None:
        """Mix of new, deleted, renamed, and modified files."""
        diff = """--- /dev/null
+++ b/new.py
@@ -0,0 +1 @@
+new
--- a/deleted.py
+++ /dev/null
@@ -1 +0,0 @@
-old
--- a/old_name.py
+++ b/new_name.py
rename from old_name.py
rename to new_name.py
--- a/modified.py
+++ b/modified.py
@@ -1 +1,2 @@
 x
+y
"""
        result = parse_diff(diff)
        assert result.total_files == 4
        assert result.files[0].is_new is True
        assert result.files[1].is_deleted is True
        assert result.files[2].is_renamed is True
        assert not result.files[3].is_new
        assert not result.files[3].is_deleted
        assert not result.files[3].is_renamed


class TestParseHunkDetails:
    """Detailed hunk parsing."""

    def test_hunk_header_parsing(self) -> None:
        """Hunk headers are parsed correctly."""
        diff = """--- a/file.py
+++ b/file.py
@@ -10,5 +15,6 @@
+new
-old
"""
        result = parse_diff(diff)
        hunk = result.files[0].hunks[0]
        assert hunk.old_start == 10
        assert hunk.old_count == 5
        assert hunk.new_start == 15
        assert hunk.new_count == 6

    def test_hunk_line_counting(self) -> None:
        """Lines within hunks are counted correctly."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,4 @@
 context1
 context2
-old
+new1
+new2
 context3
"""
        result = parse_diff(diff)
        hunk = result.files[0].hunks[0]
        assert hunk.additions == 2
        assert hunk.deletions == 1
        assert hunk.context_lines == 3

    def test_parse_hunk_without_content(self) -> None:
        """Hunk header with no following lines."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,2 +1,1 @@
"""
        result = parse_diff(diff)
        # Should still parse file and hunk header
        assert result.total_files == 1


class TestParseRobustness:
    """Robustness against variations."""

    def test_parse_no_newline_at_end(self) -> None:
        """Diff without trailing newline."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-old
+new"""
        result = parse_diff(diff)
        assert result.files[0].additions == 1
        assert result.files[0].deletions == 1

    def test_parse_windows_line_endings(self) -> None:
        """Diffs with CRLF line endings."""
        diff = "--- a/file.py\r\n+++ b/file.py\r\n@@ -1 +1 @@\r\n-old\r\n+new\r\n"
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].additions == 1

    def test_parse_with_diff_options(self) -> None:
        """Diffs may include --color or other options in lines."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1 +1,2 @@
 old
+new
"""
        result = parse_diff(diff)
        assert result.files[0].additions == 1

    def test_parse_empty_file(self) -> None:
        """Diff for completely empty file."""
        diff = """--- a/empty.txt
+++ b/empty.txt
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].additions == 0
        assert result.files[0].deletions == 0

    def test_parse_only_context_lines(self) -> None:
        """Hunk with only context, no changes."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1,3 +1,3 @@
 line1
 line2
 line3
"""
        result = parse_diff(diff)
        assert result.files[0].additions == 0
        assert result.files[0].deletions == 0
        assert result.files[0].hunks[0].context_lines == 3
