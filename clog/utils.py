import logging
import os
import shutil
import subprocess
import textwrap
from enum import Enum
from pathlib import Path

import click

from .exceptions import GitPermissionDenied


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
    if message.strip():
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


def reset(directory: Path):
    """Remove non-essential files from a directory"""
    for path in directory.iterdir():
        if ".git" in path.as_posix():
            secho("Skipping over {}".format(Path(".git")))
        else:
            if path.is_dir():
                shutil.rmtree(path.as_posix())
            else:
                path.unlink()


def run(command, verbose=False):
    result = subprocess.run(command, shell=True, capture_output=True)
    stdout = result.stdout.decode()
    stderr = result.stderr.decode()
    if "remote: Permission to" in stderr and "denied to" in stderr:
        raise GitPermissionDenied(stderr)
    if (
        "fatal: unable to access" in stderr
        and "The requested URL returned error: 403" in stderr
    ):
        raise GitPermissionDenied(stderr)
    # if stderr.strip():
    #     raise GitException(stderr)
    if verbose:
        secho(stdout, indent="  ", dim=True)
    return stdout.strip()


class GitStatus(Enum):
    HAS_UNTRACKED_FILES = 0
    NOT_A_GIT_REPOSITORY = 1
    CLEAN_WORKING_TREE = 2
    UNKNOWN_STATUS = 3


def git_status():
    def _has_untracked(output):
        snippets = [
            "Untracked files:",
            "Changes to be committed:",
            "Changes not staged for commit:",
            'nothing added to commit but untracked files present (use "git add" to track)',
        ]
        for s in snippets:
            if s in output:
                return True
        return False

    result = run("git status")
    if (
        result
        == "fatal: not a git repository (or any of the parent directories): .git\n"
    ):
        return GitStatus.NOT_A_GIT_REPOSITORY
    elif _has_untracked(result):
        secho(result, indent="  ", dim=True)
        return GitStatus.HAS_UNTRACKED_FILES
    elif "nothing to commit, working tree clean" in result:
        return GitStatus.CLEAN_WORKING_TREE
    else:
        print("result == {}".format(result))
        return GitStatus.UNKNOWN_STATUS
