from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from clog.exceptions import CLogException
from clog.models import Site
from ._helpers import assert_site_is_valid


def test_create_site_is_created_if_destination_is_empty():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        destination = Path(temp_dir) / site_name
        site = Site(cwd=destination)
        site.create()
        assert_site_is_valid(destination)


def test_create_site_fails_if_destination_exists():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        destination = Path(temp_dir) / site_name
        site = Site(cwd=destination)
        site.create()
        with pytest.raises(CLogException):
            site.create()
