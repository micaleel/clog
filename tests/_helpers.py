import subprocess
from pathlib import Path
from typing import Union

from clog.page import PageMeta


def _page_meta_parse_lines(text):
    """Returns a `:class:clog.page.PageMeta` after parsing a markdown `text`"""
    meta_parser = PageMeta()
    for line in text.splitlines():
        meta_parser.parse(line)
    return meta_parser


def create_site(site_name, directory):
    return subprocess.check_output(
        "clog new {}".format(site_name),
        cwd=directory,
        shell=True,
        stderr=subprocess.STDOUT,
    ).decode()


def _build_site(site_name, directory):
    return subprocess.check_output(
        "clog build {}".format(site_name),
        cwd=directory,
        shell=True,
        stderr=subprocess.STDOUT,
    ).decode()


def assert_file_exists(path: Union[Path, str]):
    site_dir = Path(path).resolve() if isinstance(path, str) else path
    assert site_dir.exists() and site_dir.is_file()


def assert_directory_exists(path: Union[Path, str]):
    site_dir = Path(path).resolve() if isinstance(path, str) else path
    assert site_dir.exists() and site_dir.is_dir()


def assert_site_is_valid(path: Union[str, Path]):
    site_dir = Path(path).resolve() if isinstance(path, str) else path
    assert site_dir.exists()
    expected_dirs = ["archetypes", "content", "content/posts", "themes"]
    expected_files = [".nojekyll"]
    for path in expected_dirs:
        assert_directory_exists(site_dir.joinpath(path))
    for path in expected_files:
        assert_file_exists(site_dir.joinpath(path))
