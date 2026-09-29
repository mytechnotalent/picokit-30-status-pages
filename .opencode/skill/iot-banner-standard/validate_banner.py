#!/usr/bin/env python3
"""Validate a repository banner against the IoT banner standard.

Checks that <repo>.png exists at the repository root, is a 2400x2400 PNG of a
reasonable size, that banner.json carries every required key with a known icon
and layout, that every drawn text line fits inside the safe inset, and that the
README references the banner with the exact raw GitHub URL. Run from the
repository root; exit zero means the banner conforms.
"""
import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import gen_banner

SIZE = (2400, 2400)
MARGIN = 80
MIN_BYTES = 100_000
REQUIRED = ("repo", "eyebrow", "title", "subtitle", "accent", "bg", "icon",
            "layout", "panel_status", "chips", "terminal", "categories",
            "cards", "footer")


def _repo_name():
    """
    Return the repository name from the working directory.

    Parameters
    ----------
    None

    Returns
    -------
    str
        The repository directory name.
    """
    return Path.cwd().name


def _image_line(repo):
    """
    Build the expected banner image line.

    Parameters
    ----------
    repo : str
        The repository name.

    Returns
    -------
    str
        The expected Markdown image line.
    """
    url = f"https://raw.githubusercontent.com/mytechnotalent/{repo}/main"
    return f"![{repo}]({url}/{repo}.png)"


def _png_errors(path):
    """
    Check the banner PNG dimensions and size.

    Parameters
    ----------
    path : pathlib.Path
        The banner PNG path.

    Returns
    -------
    list[str]
        PNG diagnostics.
    """
    if not path.is_file():
        return [f"{path}: missing banner PNG"]
    errors = []
    if Image.open(path).size != SIZE:
        errors.append(f"{path}: expected {SIZE}, got {Image.open(path).size}")
    if path.stat().st_size < MIN_BYTES:
        errors.append(f"{path}: PNG smaller than {MIN_BYTES} bytes")
    return errors


def _spec_errors(path, repo):
    """
    Check banner.json keys and enum values.

    Parameters
    ----------
    path : pathlib.Path
        The banner.json path.
    repo : str
        The repository name.

    Returns
    -------
    list[str]
        Spec diagnostics.
    """
    if not path.is_file():
        return ["banner.json: missing"]
    spec = json.loads(path.read_text(encoding="utf-8"))
    errors = [f"banner.json: missing key {key}"
              for key in REQUIRED if key not in spec]
    if spec.get("repo") != repo:
        errors.append("banner.json: repo does not match the directory")
    if spec.get("icon") not in gen_banner.ICONS:
        errors.append(f"banner.json: icon must be one of {gen_banner.ICONS}")
    if spec.get("layout") not in gen_banner.LAYOUTS:
        errors.append(f"banner.json: layout must be one of {gen_banner.LAYOUTS}")
    return errors


def _fit_errors(path):
    """
    Check that every drawn text extent sits inside the safe margin.

    Parameters
    ----------
    path : pathlib.Path
        The banner.json path.

    Returns
    -------
    list[str]
        Auto-fit diagnostics.
    """
    spec = json.loads(path.read_text(encoding="utf-8"))
    metrics = gen_banner.measure_spec(spec)
    errors = []
    for item in metrics["overflow"]:
        errors.append(
            f"banner.json: text {item['text']!r} spans "
            f"[{item['left']:.0f}, {item['right']:.0f}] outside "
            f"[{MARGIN}, {gen_banner.SIZE - MARGIN}]")
    if metrics["min_left"] < 0 or metrics["max_right"] > gen_banner.SIZE:
        errors.append("banner.json: text crosses the image bounds")
    return errors


def _readme_errors(repo):
    """
    Check the README references the banner on its first line.

    Parameters
    ----------
    repo : str
        The repository name.

    Returns
    -------
    list[str]
        README diagnostics.
    """
    path = Path("README.md")
    if not path.is_file():
        return ["README.md: missing"]
    first = path.read_text(encoding="utf-8").splitlines()[0]
    if first != _image_line(repo):
        return [f"README.md line 1: expected {_image_line(repo)!r}"]
    return []


def main():
    """
    Validate the repository banner.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Zero when the banner conforms, otherwise one.
    """
    repo = sys.argv[1] if len(sys.argv) > 1 else _repo_name()
    spec_path = Path("banner.json")
    errors = _png_errors(Path(f"{repo}.png"))
    errors += _spec_errors(spec_path, repo)
    if spec_path.is_file():
        errors += _fit_errors(spec_path)
    errors += _readme_errors(repo)
    print("\n".join(errors))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
