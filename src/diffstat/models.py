"""Data models for diffstat."""

from dataclasses import dataclass, field


class DiffstatError(Exception):
    """Raised when diff parsing or processing fails."""

    pass


@dataclass
class HunkStat:
    """Statistics for a single hunk in a diff."""

    old_start: int
    old_count: int
    new_start: int
    new_count: int
    additions: int
    deletions: int
    context_lines: int


@dataclass
class FileStat:
    """Statistics for a single file in a diff."""

    path: str
    old_path: str | None = None
    additions: int = 0
    deletions: int = 0
    is_binary: bool = False
    is_new: bool = False
    is_deleted: bool = False
    is_renamed: bool = False
    hunks: list[HunkStat] = field(default_factory=list)


@dataclass
class DiffResult:
    """Result of parsing a unified diff."""

    files: list[FileStat] = field(default_factory=list)

    @property
    def total_additions(self) -> int:
        """Total lines added across all files."""
        return sum(f.additions for f in self.files)

    @property
    def total_deletions(self) -> int:
        """Total lines deleted across all files."""
        return sum(f.deletions for f in self.files)

    @property
    def total_files(self) -> int:
        """Total number of files changed."""
        return len(self.files)
