import os
import sys
import importlib.metadata

# Try to get the version from metadata, fallback to reading from pyproject.toml
try:
    __version__ = importlib.metadata.version("sneko")
except importlib.metadata.PackageNotFoundError:
    if sys.version_info >= (3, 11):
        import tomllib
    else:
        import tomli as tomllib
    from pathlib import Path

    try:
        pyproject_path = Path(__file__).resolve().parents[2] / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomllib.load(f)
        __version__ = pyproject_data["project"]["version"]
    except (FileNotFoundError, KeyError):
        __version__ = "unknown"

class Config:
    VERSION = __version__
    SOLIDITY_VERSION = "0.8.26"
    CSS_PATH = "main.tcss"
    BINDINGS = [
        ("v", "noop", VERSION),
        ("f", "toggle_files", "Toggle Files"),
        ("ctrl+p", "copy_to_clipboard", "Copy Code"),
        ("ctrl+v", "paste_from_clipboard"),
        ("q", "quit", "Quit"),
    ]
    DEFAULT_CONTRACTS_PATH = os.path.join(os.path.dirname(__file__), "contracts")

    # ANSI escape codes for bold text
    BOLD = "\033[1m"
    RESET = "\033[0m"
