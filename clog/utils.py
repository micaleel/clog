import logging
import textwrap

import click


def get_logger(name):
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    return logger


def secho(
    message,
    fg=None,
    bg=None,
    bold=None,
    dim=None,
    underline=None,
    blink=None,
    reverse=None,
    reset=True,
    indent=None,
):
    if isinstance(message, bytes):
        message = message.decode()
    if indent:
        message = textwrap.indent(message, indent)
    click.echo(
        click.style(
            message,
            fg=fg,
            bg=bg,
            bold=bold,
            dim=dim,
            underline=underline,
            blink=blink,
            reverse=reverse,
            reset=reset,
        )
    )
