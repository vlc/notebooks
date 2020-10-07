"""Python 2/3 cross compatibility layer for pathlib."""
import sys

if sys.version[0] == "2":
    from pathlib2 import Path
else:
    from pathlib import Path


def mkdir_p(dir):
    """Create a directory, and it's parents, without making a fuss about it."""
    Path(dir).mkdir(parents=True, exist_ok=True)
