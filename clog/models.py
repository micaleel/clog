import os
import shutil
import subprocess
from datetime import datetime
from os.path import exists as path_exists
from pathlib import Path
from typing import Union, Optional, List

import click
import yaml
from jinja2 import Environment, PackageLoader, TemplateNotFound, Template

from .exceptions import CLogException, MissingContent, InvalidSite
from .page import Page
from .utils import get_logger, secho

LOG = get_logger(__name__)


class Site:
    CURRENT_FILE = Path(__file__).parent.absolute()
    TEMPLATE_NEW_SITE = (
        CURRENT_FILE.joinpath("../_templates/site/_blank/").resolve().as_posix()
    )
    TEMPLATE_DEFAULT_THEME = (
        CURRENT_FILE.joinpath("../_templates/themes/basic/").resolve().as_posix()
    )

    def __init__(self, cwd: Union[Path, str]):
        self.config = {}
        self.cwd = Path(cwd).resolve().absolute() if isinstance(cwd, str) else cwd
        self.content_dir = self.cwd.joinpath("content").resolve()
        self.publish_dir = self.cwd.joinpath("public").resolve()
        self.config_path = self.cwd.joinpath("config.yaml").resolve()
        self._theme_dir = None  # type: Optional[Path]
        self.pages = []  # type: List[Page]
        self.toplevel_pages: Optional[List[Page]] = []
        self.tags = set()
        self.template_index: Optional[Template] = None
        self.template_list: Optional[Template] = None
        self.template_index: Optional[Template] = None
        self.template_single: Optional[Template] = None

    @property
    def theme_dir(self):
        return self._theme_dir

    @theme_dir.setter
    def theme_dir(self, value):
        self._theme_dir = value
        try:
            self.template_index = self._get_template(
                package_path=self.theme_dir.as_posix(), template="index.html"
            )
        except TemplateNotFound:
            self.template_index = self._get_template(
                package_path=self.theme_dir.joinpath("layouts").as_posix(),
                template="index.html",
            )
        self.template_list = self._get_template(
            package_path=self.theme_dir.joinpath("layouts", "_default").as_posix(),
            template="list.html",
        )
        self.template_single = self._get_template(
            package_path=self.theme_dir.joinpath("layouts", "_default").as_posix(),
            template="single.html",
        )

    @property
    def base_url(self):
        return self.config.get("baseURL", "./")

    @property
    def subtext(self):
        return self.config.get("subtext", None)

    @property
    def title(self):
        return self.config.get("title", "")

    @staticmethod
    def _clean_markup(markup):
        return "\n".join([s.strip() for s in markup.splitlines() if len(s.strip()) > 0])

    def mathjax_imports(self):
        markup = """
          <script src="https://polyfill.io/v3/polyfill.min.js?features=es6"></script>
          <script id="MathJax-script" async src="https://cdn.jsdelivr.net/npm/mathjax@3/es5/tex-mml-chtml.js"></script>
          """
        markup = """
          <!-- mathjax for formulas -->
          <script src="https://cdnjs.cloudflare.com/ajax/libs/mathjax/2.7.3/MathJax.js?config=TeX-MML-AM_CHTML" async></script>
          """
        return Site._clean_markup(markup)

    def highlightjs_imports(self):
        markup = """
          <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.18.1/styles/default.min.css">
          <script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/9.18.1/highlight.min.js"></script>
          """
        return Site._clean_markup(markup)

    def highlightjs_init(self):
        return "<script>hljs.initHighlightingOnLoad();</script>"

    @property
    def imports(self):
        imports = "\n".join([self.highlightjs_imports(), self.mathjax_imports()])
        return imports

    @property
    def scripts(self):
        scripts = "\n".join([self.highlightjs_init()])
        return scripts

    def is_valid(self):
        has_content_dir = self.content_dir.exists() and self.content_dir.is_dir()
        has_config = self.config_path.exists() and self.config_path.is_file()
        return all([has_content_dir, has_config])

    def create(self):
        destination = self.cwd
        if path_exists(destination):
            raise CLogException(
                "Cannot create a project is an existing directory: {}".format(
                    destination
                )
            )
        # Create site structure
        assert os.path.exists(Site.TEMPLATE_NEW_SITE)
        shutil.copytree(Site.TEMPLATE_NEW_SITE, destination)

        # Copy default theme
        assert os.path.exists(Site.TEMPLATE_DEFAULT_THEME)
        theme_name = os.path.split(Site.TEMPLATE_DEFAULT_THEME)[-1]
        destination_theme = os.path.join(destination, "themes", theme_name)
        shutil.copytree(Site.TEMPLATE_DEFAULT_THEME, destination_theme)

        # Set theme name in config file
        destination_config = os.path.join(destination, "config.yaml")
        assert os.path.exists(destination_config)
        with open(destination_config, "r") as reader:
            config = yaml.load(reader, Loader=yaml.SafeLoader)
            config["theme"] = "basic"
        with open(destination_config, "w") as writer:
            yaml.dump(config, writer)

    def _get_template(self, package_path: str, template: str):
        env_layouts = Environment(
            loader=PackageLoader(package_name="clog", package_path=package_path,),
            autoescape=False,
        )
        return env_layouts.get_template(template)

    def _generate(self):
        LOG.info("Creating index page")
        html = self.template_index.render(title=self.title, pages=self.pages, site=self)
        self.publish_dir.joinpath("index.html").write_text(html)

        LOG.info("Creating single pages")
        for page in self.pages:
            html = self.template_single.render(page=page, site=self, title=page.title)
            if page.html_directory:
                destination = self.publish_dir.joinpath(
                    page.html_directory, page.html_filename
                )
            else:
                destination = self.publish_dir.joinpath(page.html_filename)

            if not destination.exists():
                os.makedirs(destination.as_posix(), exist_ok=True)
            destination.joinpath("index.html").write_text(html)

        # Copy theme's /static directory to /public directory
        static_dir_source = self.theme_dir.joinpath("static")
        static_dir_target = self.publish_dir.joinpath("static")
        if static_dir_target.exists():
            shutil.rmtree(static_dir_target.as_posix())
        shutil.copytree(
            static_dir_source.as_posix(), static_dir_target.as_posix(),
        )
        self._generate_tags()

    def _generate_tags(self):
        """Create pages based on tags"""
        tags_dir = self.publish_dir.joinpath("tags")

        os.makedirs(tags_dir.as_posix(), exist_ok=True)

        def _get_tag_home_iter():
            """Create page that lists all tags"""
            for tag in sorted(self.tags):
                page = Page()
                page.html_filename = f"./tags/{tag}/"
                page.title = tag
                yield page

        # Create page to list all tags. Clicking on a tag should take the user
        # to another page that lists the pages that correspond to the click tag
        tag_pages = [p for p in list(_get_tag_home_iter())]
        html = self.template_list.render(title="Tags", pages=tag_pages, site=self)
        tags_dir.joinpath("index.html").write_text(html)
        """Create page that lists articles related to a specific tag"""
        for tag in self.tags:
            tag_articles_dir = tags_dir.joinpath(tag)
            os.makedirs(tag_articles_dir, exist_ok=True)

            tag_articles = [p for p in self.pages if tag in p.tags]
            html = self.template_list.render(title=tag, pages=tag_articles, site=self)
            tag_articles_dir.joinpath("index.html").write_text(html)

    def validate(self):
        secho("Validating current directory...")
        if not self.is_valid():
            raise InvalidSite()

        if not self.content_dir.exists():
            raise MissingContent(
                f"Cannot find the ./content directory. "
                "Ensure that command is run from your site's root directory"
            )

        if len(list(self.content_dir.rglob("*.md"))) == 0:
            raise MissingContent("Cannot continue because content directory is empty")

    def build(self):
        self.validate()
        # Load configuration
        self.config = yaml.load(self.config_path.read_text(), yaml.SafeLoader)
        self.theme_dir = self.cwd.joinpath("themes/{}".format(self.config["theme"]))

        # Create public/ directory
        if not self.publish_dir.exists():
            os.makedirs(self.publish_dir.as_posix(), exist_ok=True)

        for c in os.walk(self.content_dir.as_posix(), topdown=True):
            dirpath, dirnames, filenames = c
            is_toplevel_page = len(dirnames) == 1 and dirnames[0] == "posts"
            target_rel_dir = dirpath.replace(self.content_dir.as_posix(), "")
            for fname in filenames:
                fpath = Path(dirpath).joinpath(fname).as_posix()
                click.echo(click.style("\t ↠ {}...".format(fpath), dim=True))
                page = Page.parse(fpath)
                page.is_toplevel = is_toplevel_page
                page.html_directory = target_rel_dir[1:]  # Remove the / prefix
                self.pages.append(page)
                self.tags.update(page.tags)
                if is_toplevel_page:
                    self.toplevel_pages.append(page)

        self._generate()

    def _has_remotes(self):
        return len(Git.run("git remote -v").stdout.decode().strip()) > 0

    def _autocommit(self):
        secho("Auto-committing changes ...", fg="blue")
        timestamp = datetime.now().strftime("%H:%M:%S")
        status = Git(self.cwd).run(
            'git add . && git commit -m "Auto commit as {}" && git push'.format(
                timestamp
            )
        )
        secho(status.stdout, dim=True, indent="\t")

    def _update_gitignore(self):
        """Add public/ directory is in .gitignore file"""
        dirty = False
        gitignore_file = self.cwd.joinpath(".gitignore").resolve()
        dirname = "public/"
        if not gitignore_file.exists():
            gitignore_file.write_text(dirname)
            dirty = True
        else:
            ignored_files = gitignore_file.read_text()
            if dirname not in ignored_files:
                ignored_files += f"\n{dirname}"
                gitignore_file.write_text(ignored_files)
                dirty = True
        if dirty:
            secho(f"Adding public/ directory to .gitignore file")
            commands = "git add --all && git commit -m 'Update .gitignore'"
            response = Git.run(commands).stdout
            secho(response, indent="\t", dim=True)

    def _init_gh_pages_branch(self, autocommit: bool = False):
        status = Git.status()
        if status == Git.CLEAN_WORKING_TREE:
            if not self._has_remotes():
                secho(
                    "Git repository has no remotes. "
                    "See https://help.github.com/en/github/using-git/adding-a-remote for help",
                    bold=True,
                    fg="red",
                )
                raise CLogException()
            else:
                # Create gh-pages branch, if necessary
                if "gh-pages" not in Git.run("git branch").stdout.decode():
                    commands = " && ".join(
                        [
                            "git push -u origin master",
                            "git checkout -b gh-pages",
                            "git push -u origin gh-pages",
                            "git checkout master",
                            "git status",
                        ]
                    )
                    output = Git.run(commands).stdout
                    secho(output, indent="\t", dim=True)
        elif status == Git.NOT_A_GIT_REPOSITORY:
            secho(
                "Working directory is not a Git repository", bold=True, fg="red",
            )
            raise CLogException()
        elif status == Git.HAS_UNTRACKED_FILES:
            secho(
                "Working directory has changes that have not been committed.",
                bold=True,
                fg="yellow",
            )
            if autocommit:
                self._autocommit()
        elif status == Git.UNKNOWN_STATUS:
            secho("Git repository in a status not handled by CLog")
            raise CLogException()

    def _create_worktree(self):
        # Create worktree in public/ directory, if necessary
        output = Git.run("git worktree list | grep gh-pages").stdout.decode()
        secho(output, dim=True, indent="\t")

        exists = (
            self.publish_dir.absolute().as_posix() in output and "gh-pages" in output
        )
        if not exists:
            secho("Creating worktree for gh-pages in public/", bold=True)
            output = Git.run("git worktree add public gh-pages").stdout.decode()
            secho(output, dim=True, indent="\t")

    def deploy(self, autocommit=False):
        """
        Deploy /public directory to gh-pages branch on GitHub
        """

        # Raise an exception if user is in the wrong directory
        self.validate()
        self._update_gitignore()
        self._init_gh_pages_branch(autocommit=autocommit)
        self._create_worktree()
        self.build()  # Create HTML pages in public/

        secho("Pushing changes in /public directory", bold=True)
        commands = "; ".join(
            [
                "pushd public",
                "git add --all",
                "git commit -m \"Build output as of $(git log '--format=format:%H' master -1)\"",
                "git push origin gh-pages",
                "popd",
                # "git worktree prune",
                "git status",
            ]
        )
        output = Git.run(commands).stdout.decode()
        secho(output, indent="\t", dim=True)
        secho("Done. Site deployed!", bold=True)


class Git:
    HAS_UNTRACKED_FILES = 0
    NOT_A_GIT_REPOSITORY = 1
    CLEAN_WORKING_TREE = 2
    UNKNOWN_STATUS = 3

    def __init__(self, path: Union[str, Path]):
        self.path = path if isinstance(path, Path) else Path(path).resolve()

    @staticmethod
    def run(command):
        return subprocess.run(command, shell=True, capture_output=True)

    @staticmethod
    def _has_untracked(output):
        snippets = [
            b"Untracked files:",
            b"Changes to be committed:",
            b"Changes not staged for commit:",
            b'nothing added to commit but untracked files present (use "git add" to track)',
        ]
        for s in snippets:
            if s in output:
                return True
        return False

    @staticmethod
    def status():
        result = Git.run("git status")

        if (
            result.stdout
            == b"fatal: not a git repository (or any of the parent directories): .git\n"
        ):
            return Git.NOT_A_GIT_REPOSITORY
        elif Git._has_untracked(result.stdout):
            output = result.stdout.decode()
            secho("Oops, something went wrong!", fg="red")
            secho(output, indent="\t", dim=True)
            return Git.HAS_UNTRACKED_FILES
        elif b"nothing to commit, working tree clean" in result.stdout:
            return Git.CLEAN_WORKING_TREE
        else:
            print("result == {}".format(result))
            return Git.UNKNOWN_STATUS
