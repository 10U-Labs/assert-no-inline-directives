"""Write test input files."""

from pathlib import Path


def write_files(root: Path, files: dict[str, str]) -> list[str]:
    """Write each named file under root and return their paths in order."""
    paths = []
    for name, content in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content)
        paths.append(str(path))
    return paths
