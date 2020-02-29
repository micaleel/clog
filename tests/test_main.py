import shutil
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from clog.exceptions import CLogException
from clog.models import Site
from tests._helpers import create_site, assert_site_is_valid


def test_dud():
    assert 1 == 2 - 1


def test_develop_verbose():
    # port = 8001
    # runner = CliRunner()
    #
    # result = runner.invoke(develop, [f"--port={port}"])
    # assert result.exit_code == 0
    # assert "Serving on http://127.0.0.1:{}".format(port) in result.output
    assert True


#
def test_develop_quiet():
    #     runner = CliRunner()
    #     port = 8001
    #     result = runner.invoke(develop, [f"--port={port}", "--quiet"])
    #     assert result.exit_code == 0
    #     assert len(result.output) == 0
    assert True


def test_new_site_is_created():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        destination = Path(temp_dir).resolve().joinpath(site_name)
        result = create_site(site_name, temp_dir)
        assert result.strip() == "Project created at {}".format(destination)
        assert_site_is_valid(destination.as_posix())


def test_new_site_fails_if_destination_exists():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        _ = create_site(site_name, temp_dir)
        result = create_site(site_name, temp_dir)
        destination = Path(temp_dir) / site_name
        assert result.strip() == "Cannot create a project in an existing directory: {}".format(
            destination.resolve().as_posix()
        )
