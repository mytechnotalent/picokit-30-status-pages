#!/usr/bin/env python3
"""Validate a repository README.md against the IoT README standard.

Enforces the exact top block (banner, <br>, the two FREE course links, <br>,
the H1 title block), the framed legal disclaimer, and the exact bottom block
(<br>, Next, <br>, License, MIT link). Run from the repository root; exit zero
means the README conforms.
"""
import sys
from pathlib import Path

RE_LINK = ("## FREE Reverse Engineering Self-Study Course [HERE]"
           "(https://github.com/mytechnotalent/reverse-engineering)")
EH_LINK = ("## FREE Embedded Hacking Course [HERE]"
           "(https://github.com/mytechnotalent/Embedded-Hacking)")
TEMPLATE = Path(__file__).resolve().parent / "README.template.md"


def _repo_name() -> str:
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


def _image_line(repo: str) -> str:
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


def _license_link(repo: str) -> str:
    """
    Build the expected MIT license link line.

    Parameters
    ----------
    repo : str
        The repository name.

    Returns
    -------
    str
        The expected license Markdown line.
    """
    url = f"https://github.com/mytechnotalent/{repo}/blob/main/LICENSE"
    return f"[MIT License]({url})"


def _disclaimer(lines: list[str]) -> list[str]:
    """
    Extract the framed disclaimer block from a line list.

    Parameters
    ----------
    lines : list[str]
        README or template lines.

    Returns
    -------
    list[str]
        The disclaimer lines including both *** fences, or an empty list.
    """
    starts = [i for i, line in enumerate(lines) if line.strip() == "***"]
    if len(starts) < 2:
        return []
    return [line.rstrip() for line in lines[starts[0]:starts[1] + 1]]


def _top_errors(lines: list[str], repo: str) -> list[str]:
    """
    Check the fixed top block of the README.

    Parameters
    ----------
    lines : list[str]
        README lines.
    repo : str
        The repository name.

    Returns
    -------
    list[str]
        Top-block diagnostics.
    """
    expected = [(_image_line(repo), 0), ("", 1), ("<br>", 2), ("", 3),
                (RE_LINK, 4), (EH_LINK, 5), ("", 6), ("<br>", 7), ("", 8)]
    errors = [f"line {number}: expected {want!r}"
              for want, number in expected if _at(lines, number) != want]
    return errors + _title_errors(lines)


def _title_errors(lines: list[str]) -> list[str]:
    """
    Check the H1 title block lines.

    Parameters
    ----------
    lines : list[str]
        README lines.

    Returns
    -------
    list[str]
        Title-block diagnostics.
    """
    errors = []
    if not _at(lines, 9).startswith("# "):
        errors.append("line 9: missing H1 title")
    if _at(lines, 10) != "":
        errors.append("line 10: expected a blank line")
    if not _at(lines, 11).startswith("### "):
        errors.append("line 11: missing H3 subtitle")
    if not (_at(lines, 12).startswith("#### ") and _at(lines, 12).endswith(" Series")):
        errors.append("line 12: missing the series line")
    if _at(lines, 13) != "" or _at(lines, 14) != "<br>":
        errors.append("line 14: expected <br> after the title block")
    if _at(lines, 15) != "":
        errors.append("line 15: expected a blank line")
    return errors


def _at(lines: list[str], number: int) -> str:
    """
    Return a line by index or an empty string when out of range.

    Parameters
    ----------
    lines : list[str]
        README lines.
    number : int
        Zero-based line index.

    Returns
    -------
    str
        The line text or an empty string.
    """
    return lines[number] if number < len(lines) else ""


def _bottom_errors(lines: list[str], repo: str) -> list[str]:
    """
    Check the fixed bottom block of the README.

    Parameters
    ----------
    lines : list[str]
        README lines.
    repo : str
        The repository name.

    Returns
    -------
    list[str]
        Bottom-block diagnostics.
    """
    tail = [line.rstrip() for line in lines if line.strip()]
    expected = ["<br>", "# Next", None, "<br>", "# License", _license_link(repo)]
    if len(tail) < len(expected):
        return ["missing the bottom block"]
    window = tail[-len(expected):]
    return [f"bottom: expected {want!r} got {got!r}"
            for want, got in zip(expected, window)
            if want is not None and want != got]


def _disclaimer_errors(lines: list[str]) -> list[str]:
    """
    Compare the README disclaimer to the template disclaimer.

    Parameters
    ----------
    lines : list[str]
        README lines.

    Returns
    -------
    list[str]
        Disclaimer diagnostics.
    """
    want = _disclaimer(TEMPLATE.read_text(encoding="utf-8").splitlines())
    got = _disclaimer(lines)
    if not got:
        return ["missing the framed legal disclaimer"]
    if got != want:
        return ["the legal disclaimer does not match the template"]
    return []


def main() -> int:
    """
    Validate the repository README.

    Parameters
    ----------
    None

    Returns
    -------
    int
        Zero when the README conforms, otherwise one.
    """
    repo = sys.argv[1] if len(sys.argv) > 1 else _repo_name()
    lines = Path("README.md").read_text(encoding="utf-8").splitlines()
    errors = _top_errors(lines, repo) + _disclaimer_errors(lines)
    errors += _bottom_errors(lines, repo)
    print("\n".join(errors))
    return int(bool(errors))


if __name__ == "__main__":
    raise SystemExit(main())
