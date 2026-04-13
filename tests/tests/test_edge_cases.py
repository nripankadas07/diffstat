"""Tests for edge cases and error conditions."""

import pytest
from diffstat.core import parse_diff
from diffstat.models import DiffstatError, DiffResult


class TestInputValidation:
    """Input validation tests."""

    def test_invalid_input_type_int(self) -> None:
        """Integer input raises DiffstatError."""
        with pytest.raises(DiffstatError):
            parse_diff(42)  # type: ignore

    def test_invalid_input_type_list(self) -> None:
        """List input raises DiffstatError."""
        with pytest.raises(DiffstatError):
            parse_diff([])  # type: ignore

    def test_invalid_input_type_dict(self) -> None:
        """Dict input raises DiffstatError."""
        with pytest.raises(DiffstatError):
            parse_diff({})  # type: ignore

    def test_invalid_input_type_none(self) -> None:
        """None input raises DiffstatError."""
        with pytest.raises(DiffstatError):
            parse_diff(None)  # type: ignore


class TestMalformedDiffs:
    """Malformed diff handling."""

    def test_missing_hunk_header_marker(self) -> None:
        """Lines without @@ after header are handled."""
        diff = """--- a/file.py
+++ b/file.py
this is not a valid hunk header
+some content
"""
        result = parse_diff(diff)
        # Should still parse file header
        assert result.total_files == 1

    def test_incomplete_file_header(self) -> None:
        """Missing +++ line after --- line."""
        diff = """--- a/file.py
some other content
"""
        result = parse_diff(diff)
        # Should handle gracefully
        assert isinstance(result, DiffResult)

    def test_random_text_mixed_in(self) -> None:
        """Random text mixed with valid diff."""
        diff = """Some random text here
--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-old
+new
More random text
"""
        result = parse_diff(diff)
        assert result.total_files == 1

    def test_hunk_without_lines(self) -> None:
        """Hunk header with immediately following new file."""
        diff = """--- a/file1.py
+++ b/file1.py
@@ -1 +1 @@
--- a/file2.py
+++ b/file2.py
@@ -1 +1 @@
-x
+y
"""
        result = parse_diff(diff)
        assert result.total_files == 2


class TestParsingRobustness:
    """Robustness tests."""

    def test_very_long_file_path(self) -> None:
        """Very long file path."""
        long_path = "a/" + "/".join(["dir"] * 50) + "/file.py"
        long_path_b = "b/" + "/".join(["dir"] * 50) + "/file.py"
        diff = f"""--- {long_path}
+++ {long_path_b}
@@ -1 +1 @@
-old
+new
"""
        result = parse_diff(diff)
        assert result.total_files == 1

    def test_many_hunks_single_file(self) -> None:
        """File with many hunks."""
        lines = ["--- a/file.py", "+++ b/file.py"]
        for i in range(100):
            lines.append(f"@@ -{i},2 +{i},2 @@")
            lines.append(" context")
            lines.append(f"-old{i}")
            lines.append(f"+new{i}")

        diff = "\n".join(lines)
        result = parse_diff(diff)
        assert result.total_files == 1
        assert len(result.files[0].hunks) == 100

    def test_many_files(self) -> None:
        """Diff with many files."""
        lines = []
        for i in range(50):
            lines.append(f"--- a/file{i}.py")
            lines.append(f"+++ b/file{i}.py")
            lines.append("@@ -1 +1 @@")
            lines.append(f"-old{i}")
            lines.append(f"+new{i}")

        diff = "\n".join(lines)
        result = parse_diff(diff)
        assert result.total_files == 50

    def test_mixed_unix_and_windows_line_endings(self) -> None:
        """Mix of Unix and Windows line endings."""
        diff = "--- a/file.py\r\n+++ b/file.py\n@@ -1 +1 @@\r\n-old\n+new\r\n"
        result = parse_diff(diff)
        assert result.total_files == 1

    def test_tabs_in_content(self) -> None:
        """Content with tabs."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-\tdef old():
+\tdef new():
"""
        result = parse_diff(diff)
        assert result.files[0].additions == 1
        assert result.files[0].deletions == 1


class TestSpecialScenarios:
    """Special parsing scenarios."""

    def test_empty_hunk_count(self) -> None:
        """Hunk with zero count."""
        diff = """--- a/file.py
+++ b/file.py
@@ -0,0 +1,1 @@
+new line
"""
        result = parse_diff(diff)
        assert result.files[0].additions == 1
        assert result.files[0].deletions == 0

    def test_file_mode_change_only(self) -> None:
        """File with mode change but no content change."""
        diff = """--- a/script.sh
+++ b/script.sh
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].additions == 0
        assert result.files[0].deletions == 0

    def test_similarity_index_line(self) -> None:
        """Diff with similarity index line (from rename detection)."""
        diff = """similarity index 95%
--- a/old.py
+++ b/new.py
rename from old.py
rename to new.py
@@ -1,2 +1,3 @@
 def func():
-    pass
+    return True
+    print("done")
"""
        result = parse_diff(diff)
        assert result.files[0].is_renamed is True

    def test_index_line(self) -> None:
        """Diff with index line (git internal)."""
        diff = """index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-old
+new
"""
        result = parse_diff(diff)
        assert result.total_files == 1

    def test_combined_diff_format(self) -> None:
        """Attempt to parse merge commit diff (combined format)."""
        # While not fully supported, should not crash
        diff = """  file.py
++++ b/file.py
"""
        result = parse_diff(diff)
        # Should handle gracefully
        assert isinstance(result, DiffResult)

    def test_git_apply_format(self) -> None:
        """Standard git apply format."""
        diff = """diff --git a/file.py b/file.py
index 1234567..abcdefg 100644
--- a/file.py
+++ b/file.py
@@ -1 +1 @@
-old
+new
"""
        result = parse_diff(diff)
        assert result.total_files == 1
        assert result.files[0].path == "file.py"


class TestHunkHeaderParsing:
    """Hunk header edge cases."""

    def test_hunk_header_with_function_name(self) -> None:
        """Hunk header with function context."""
        diff = """--- a/file.py
+++ b/file.py
@@ -10,3 +10,4 @@ def my_function():
 x = 1
+y = 2
 z = 3
"""
        result = parse_diff(diff)
        hunk = result.files[0].hunks[0]
        assert hunk.old_start == 10
        assert hunk.old_count == 3
        assert hunk.new_start == 10
        assert hunk.new_count == 4

    def test_hunk_header_single_line_context(self) -> None:
        """Hunk header with default context count."""
        diff = """--- a/file.py
+++ b/file.py
@@ -1 +1,2 @@
 x
+y
"""
        result = parse_diff(diff)
        hunk = result.files[0].hunks[0]
        assert hunk.old_count == 1
        assert hunk.new_count == 2

    def test_parse_binary_with_other_files(self) -> None:
        """Binary file mixed with text files."""
        diff = """--- a/text1.py
+++ b/text1.py
@@ -1 +1,2 @@
 x
+y
Binary files a/data.bin and b/data.bin differ
--- a/text2.py
+++ b/text2.py
@@ -1 +0,0 @@
-z
"""
        result = parse_diff(diff)
        assert result.total_files == 3
        assert result.files[1].is_binary is True
        assert result.files[0].is_binary is False
        assert result.files[2].is_binary is False


class TestAccumulationLogic:
    """Test stat accumulation across files."""

    def test_total_stats_accumulate(self) -> None:
        """Totals correctly sum across files."""
        diff = """--- a/f1.py
+++ b/f1.py
@@ -1 +1,3 @@
 x
+y
+z
--- a/f2.py
+++ b/f2.py
@@ -1,2 +0,0 @@
-a
-b
--- a/f3.py
+++ b/f3.py
@@ -5,1 +5,1 @@
-old
+new
"""
        result = parse_diff(diff)
        assert result.total_additions == 3  # 2 + 0 + 1
        assert result.total_deletions == 3  # 0 + 2 + 1
        assert result.total_files == 3

    def test_binary_not_counted_in_additions_deletions(self) -> None:
        """Binary files don't contribute to line counts."""
        result = parse_diff(
            "Binary files a/img.png and b/img.png differ\n"
        )
        assert result.total_additions == 0
        assert result.total_deletions == 0
        assert result.total_files == 1
