import os
from io import StringIO
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import yaml
from markdown import Markdown
from slugify import slugify

from clog.exceptions import CLogException

CODE_BACKTICKS = "```"


class PageMeta:
    DELIMETERS_SECTION = ["--", "==", "++"]
    DELIMETERS_VALUES = ["=", ":"]

    def __init__(self):
        self._complete = False
        self._delimeter = None
        self.data = {}

    def get_entry(self, key, fallback=None):
        if len(self.data) == 0:
            return fallback

        value = self.data.get(key, fallback)
        if isinstance(value, str):
            value = yaml.load(StringIO(value), Loader=yaml.SafeLoader)
        return value

    @staticmethod
    def is_delimeter(line):
        """Check if text is delimeter for the meta section of the page"""
        return any([line.startswith(d) for d in PageMeta.DELIMETERS_SECTION])

    @staticmethod
    def get_value_separator(line):
        for v in PageMeta.DELIMETERS_VALUES:
            if v in line:
                return v
        else:
            raise ValueError("Input does not contain any value delimeters")

    def parse(self, line):
        """Parses a line of text from a markdown file to extract page metadata"""
        _text = line.strip()
        if self._delimeter is None and PageMeta.is_delimeter(_text):
            self._delimeter = _text
        elif _text == self._delimeter and len(_text) > 0:
            self._complete = True
        else:
            if len(_text) > 0:
                separator = PageMeta.get_value_separator(_text)
                if separator == "=":
                    key, value = _text.strip().split(separator)
                elif separator == ":":
                    idx = _text.find(separator)
                    key = _text[:idx].strip()
                    value = _text[idx + len(separator) :].strip()
                else:
                    raise ValueError("Unrecognized separator")

                self.data[key.strip()] = value.strip()

    @property
    def complete(self):
        """Returns True if metadata is complete"""
        return self._complete


def format_codeblock(text: str) -> str:
    """Formats a markdown code block a HighlightJS friendly manner"""

    def _get_backticks_prefix(text):
        """Get the text before the backticks in a line"""
        backticks_pos = text.find(CODE_BACKTICKS)
        return "" if backticks_pos == -1 else text[:backticks_pos]

    lines = text.split("\n")
    codeblocks = []
    languages = {}

    # Find all codeblocks
    for idx, line in enumerate(lines):
        if line.strip().startswith(CODE_BACKTICKS):
            codeblocks.append(idx)
            lang = line.replace(CODE_BACKTICKS, "").strip()
            if len(lang) > 0:
                languages[idx] = lang

    if len(codeblocks) % 2 != 0:
        raise ValueError("Inconsistent code block")

    for i in range(0, len(codeblocks), 2):
        start, end = codeblocks[i], codeblocks[i + 1]
        bt_prefix = _get_backticks_prefix(lines[start])
        lang = languages.get(start, "")
        if lang:
            lines[start] = (
                bt_prefix + f'<pre class="highlight"><code class="language-{lang}">'
            )
        else:
            lines[start] = bt_prefix + "<pre><code>"

        lines[end] = lines[end].replace(CODE_BACKTICKS, f"</code></pre>")
        codeblocks.pop(0)
        codeblocks.pop(0)

    return "\n".join(lines)


class Page:
    def __init__(self):
        self.meta = PageMeta()
        self.html: Optional[str] = None
        self.source_path: Optional[str] = None
        self.base_url = "./"
        self._html_filename = None
        self._title = None
        self.html_directory = None
        self.is_toplevel = False

    @property
    def href(self):
        if len(self.html_directory.strip()) > 0:
            url = urljoin(self.base_url, self.html_directory) + "/" + self.html_filename
        else:
            url = urljoin(self.base_url, self.html_filename)

        return f"/{url}"

    @property
    def date(self):
        import arrow

        raw = self.meta.get_entry("date", None)
        return None if raw is None else arrow.get(raw)

    @property
    def date_humanized(self):
        return None if self.date is None else self.date.humanize()

    @property
    def title(self):
        if self._title is None:
            self._title = self.meta.get_entry("title", None)
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @property
    def title_slug(self):
        return None if self.title is None else slugify(self.title.encode())

    @property
    def html_filename(self):
        if self._html_filename is None:
            self._html_filename = self.title_slug
        return self._html_filename

    @html_filename.setter
    def html_filename(self, value):
        self._html_filename = value

    @property
    def tags(self):
        return self.meta.get_entry("tags", [])

    @property
    def source_file(self):
        return os.path.split(self.source_path)

    @staticmethod
    def parse(path) -> Optional["Page"]:
        if not isinstance(path, Path):
            path = Path(path)

        page = Page()
        page.source_path = path

        def _extract():
            with path.open(encoding="utf-8") as fp:
                # formatted = format_codeblock(fp.read())
                formatted = fp.read()
                for line in formatted.splitlines():
                    if not page.meta.complete:
                        page.meta.parse(line.strip())
                    else:
                        yield line

        extracted = "\n".join(_extract())
        page.html = Markdown(extensions=["pymdownx.extra"]).convert(extracted)
        if page.title is None:  # TODO Write test for this
            raise CLogException()

        return page
