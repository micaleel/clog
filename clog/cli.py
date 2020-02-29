import logging
import os
import subprocess
from pathlib import Path

import click
import tornado
from tornado import web

from .exceptions import CLogException
from .models import Site

logging.basicConfig(
    format="%(asctime)s [p%(process)s:%(pathname)s:%(lineno)d] %(levelname)s: %(message)s"
)
LOG = logging.getLogger(__name__)
DEFAULT_HOST = "http://localport:8000"

TORNADO_GENLOG = logging.getLogger("tornado.general")
handler = logging.StreamHandler()
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
TORNADO_GENLOG.addHandler(handler)


@click.group()
def main():
    pass


@main.command()
@click.argument("directory", type=click.Path(exists=False))
def new(directory):
    """Create a new website"""
    destination = Path(directory).resolve().absolute().as_posix()
    try:
        builder = Site(directory)
        builder.create()
        click.echo(click.style("Project created at {}".format(destination)))
    except CLogException:
        click.echo(
            "Cannot create a project in an existing directory: {}".format(
                click.style(destination, fg="red", bold=True)
            )
        )
        raise SystemExit()


def rebuild():
    click.echo("Building pages")
    Site(cwd=Path.cwd()).build()


@main.command()
@click.option("--port", default=8000, help="Port to serve website")
def develop(port):
    public_dir = Path.cwd().joinpath("public")
    if not public_dir.exists():
        click.echo("Cannot find public/ directory")
        raise SystemExit()

    command = f"livereload {public_dir.as_posix()} -p {port}"
    subprocess.call(command, shell=True)


@main.command()
def build():
    click.secho("Transforming markdown to HTML")
    builder = Site(Path.cwd())

    try:
        builder.build()
        click.echo(click.style("Done!", bold=True))
    except CLogException as ex:
        click.echo(click.style(ex, fg="yellow"))
        raise SystemExit()


@main.command()
@click.option(
    "--autocommit", default=False, help="Automatically commit changes", is_flag=True
)
def deploy(autocommit: bool):
    click.secho("Deploying to gh-pages", bold=True)
    builder = Site(Path.cwd())
    try:
        builder.deploy(autocommit=autocommit)
        click.echo(click.style("Done!", bold=True))
    except CLogException as ex:
        click.echo(click.style(str(ex), fg="red", bold=True))
        raise SystemExit()


if __name__ == "__main__":
    main()
