"""diffstat - Compute unified diff statistics."""

from diffstat.core import parse_diff, parse_diff_file
from diffstat.formatter import format_stat
from diffstat.models import DiffResult, DiffstatError, FileStat, HunkStat

__version__ = "1.0.0"
__author__ = "Nripanka Das"

__all__ = [
    "parse_diff",
    "parse_diff_file",
    "format_stat",
    "DiffResult",
    "DiffstatError",
    "FileStat",
    "HunkStat",
]
