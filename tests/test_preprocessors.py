import shutil
from pathlib import Path
from tempfile import NamedTemporaryFile, TemporaryDirectory

import pytest

from clog.exceptions import MissingContent, InvalidSite
from clog.models import Site
from clog.page import format_codeblock, Page
from tests._helpers import _page_meta_parse_lines, create_site

CODE_BLOCK_JAVASCRIPT = """
```javascript
var s = "JavaScript syntax highlighting";
alert(s);
```
"""
CODE_BLOCK_RUBY = """
```ruby
require 'redcarpet'
markdown = Redcarpet.new("Hello World!")
puts markdown.to_html
```
"""
CODE_BLOCK_PYTHON = """
```python
s = "Python syntax highlighting"
print s
```
"""
CODE_BLOCK_PLAIN_A = """
```
function test() {
  console.log("notice the blank line before this function?");
}
```
"""


def test_page_meta():
    meta_parser = _page_meta_parse_lines(
        """
        +++
        title = "About"
        date = 2019-02-06T16:52:34+01:00
        author= "Khalil"
        +++
        """
    )
    assert len(meta_parser.data) == 3
    assert meta_parser.data["title"] == '"About"'
    assert meta_parser.data["author"] == '"Khalil"'
    assert meta_parser.data["date"] == "2019-02-06T16:52:34+01:00"

    meta_parser = _page_meta_parse_lines(
        """
        =====
        title = "Contact"
        =====
        """
    )
    assert len(meta_parser.data) == 1
    assert meta_parser.data["title"] == '"Contact"'

    meta_parser = _page_meta_parse_lines(
        """
        ---
        title : "Map"
        ---
        """
    )
    assert len(meta_parser.data) == 1
    assert meta_parser.data["title"] == '"Map"'


# TODO Tabs, newlines and spaces in code should not be changed


def test_backticks_are_replaced_with_lang():
    markdown = f"""# Demo

    ```python
    s = "Python syntax highlighting"
    print(s)
    if __name__ == '__main__':
        process(
            x=a,
            b=c
        )
    ```

    ## End
    """
    expected = f"""# Demo

    <pre class="highlight"><code class="language-python">
    s = "Python syntax highlighting"
    print(s)
    if __name__ == '__main__':
        process(
            x=a,
            b=c
        )
    </code></pre>

    ## End
    """
    assert format_codeblock(markdown) == expected


def test_backticks_are_replaced():
    markdown = f"""
    # Demo

    ```
    No language indicated, so no syntax highlighting.
    But let's throw in a <b>tag</b>.
    ```

    ## End
    """
    expected = f"""
    # Demo

    <pre><code>
    No language indicated, so no syntax highlighting.
    But let's throw in a <b>tag</b>.
    </code></pre>

    ## End
    """

    assert format_codeblock(markdown) == expected


def test_throws_for_incomplete_codeblocks():
    markdown = f"""
    # Demo

    ```
    No language indicated, so no syntax highlighting.
    But let's throw in a <b>tag</b>.


    ## End
    """

    with pytest.raises(ValueError):
        assert format_codeblock(markdown)


def assert_html_equal(s1, s2):
    def _strip(s):
        return "".join([x for x in s.splitlines() if len(x.strip()) > 0]).strip()

    assert _strip(s1) == _strip(s2)


def test_page_parsing():
    markdown = """
+++
title = "About"
+++

# Demo

```python
s = "Python syntax highlighting"
print(s)
```

## End
    """

    expected = """
<h1>Demo</h1>

<pre class="highlight"><code class="language-python">
s = "Python syntax highlighting"
print(s)
</code></pre>

<h2>End</h2>
    """
    with NamedTemporaryFile() as fp:
        fp.write(markdown.encode("utf-8"))
        fp.flush()
        page = Page.parse(fp.name)

    assert_html_equal(page.html, expected)


def test_page_parsing():
    markdown = """
+++
title = "About"
+++

# Demo

```python
s = "Python syntax highlighting"
print(s)
```

## End
    """

    expected = """
<h1>Demo</h1>

<pre class="highlight"><code class="language-python">
s = "Python syntax highlighting"
print(s)
</code></pre>

<h2>End</h2>
    """
    with NamedTemporaryFile() as fp:
        fp.write(markdown.encode("utf-8"))
        fp.flush()
        page = Page.parse(fp.name)

    assert_html_equal(page.html, expected)


def test_site_build_fails_when_invoked_from_invalid_director():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        _ = create_site(site_name, temp_dir)
        with pytest.raises(InvalidSite):
            site = Site(cwd=Path.cwd().as_posix())
            site.build()


def test_site_build_fails_for_missing_content_dir():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        _ = create_site(site_name, temp_dir)

        with pytest.raises(MissingContent):
            site_dir = Path(temp_dir).resolve().joinpath(site_name)
            site = Site(cwd=site_dir)
            site.build()


def test_site_build_recreates_missing_public_dir():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        _ = create_site(site_name, temp_dir)

        site_dir = Path(temp_dir).resolve().joinpath(site_name)
        site = Site(cwd=site_dir)
        if site.publish_dir.exists():
            shutil.rmtree(site.publish_dir.as_posix())
        # Add some content to the site
        md_markup = """
        +++
        title = "About"
        tags = [python, programming]
        +++
        # Demo
        ```python
        s = "Python syntax highlighting"
        print(s)
        ```
        """
        site.content_dir.joinpath("about.md").write_text(md_markup)
        site.build()
        assert site.publish_dir.exists()


def test_site_build_parses_pages():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        _ = create_site(site_name, temp_dir)

        site_dir = Path(temp_dir).resolve().joinpath(site_name)
        site = Site(cwd=site_dir)
        if site.publish_dir.exists():
            shutil.rmtree(site.publish_dir.as_posix())
        # Add some content to the site
        md_markup = """
        +++
        title = "About"
        tags = [python, programming]
        +++
        # Demo
        ```python
        s = "Python syntax highlighting"
        print(s)
        ```
        """
        site.content_dir.joinpath("about.md").write_text(md_markup)
        site.build()
        assert len(site.pages) == len(list(site.content_dir.rglob("*.md")))
        assert (
            site.pages[0].source_path.as_posix()
            == site.content_dir.joinpath("about.md").as_posix()
        )
        assert set(site.pages[0].tags) == {"python", "programming"}


def test_site_build_saves_pages():
    site_name = "new-site"
    with TemporaryDirectory() as temp_dir:
        _ = create_site(site_name, temp_dir)

        site_dir = Path(temp_dir).resolve().joinpath(site_name)
        site = Site(cwd=site_dir)
        if site.publish_dir.exists():
            shutil.rmtree(site.publish_dir.as_posix())
        # Add some content to the site
        md_markup = """
        +++
        title = "About"
        tags = [python, programming]
        +++
        # Demo
        ```python
        s = "Python syntax highlighting"
        print(s)
        ```
        """
        site.content_dir.joinpath("about.md").write_text(md_markup)
        site.build()

        tags_dir = site.publish_dir.joinpath("tags")
        assert tags_dir.exists()

        for tag in site.pages[0].tags:
            specific_tag_dir = tags_dir.joinpath(tag)
            index_file = specific_tag_dir.joinpath("index.html")
            assert specific_tag_dir.exists() and specific_tag_dir.is_dir()
            assert index_file.exists() and index_file.is_file()
